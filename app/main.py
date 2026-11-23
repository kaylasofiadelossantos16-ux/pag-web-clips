import hmac
import re
import threading
import time
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from . import config, pipeline

config.validate()
config.DATA_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(
    SessionMiddleware, secret_key=config.SECRET_KEY, session_cookie="clips_session",
    max_age=60 * 60 * 24 * 7, same_site=config.COOKIE_SAMESITE, https_only=config.COOKIE_SECURE,
)
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()
FAILS: dict[str, list[float]] = {}  # ip -> timestamps de intentos fallidos
JOB_ID = re.compile(r"^[0-9a-f]{32}$")


def require_auth(request: Request):
    if not request.session.get("auth"):
        raise HTTPException(status_code=401)


@app.exception_handler(401)
async def _unauth(request: Request, exc):
    if request.url.path.startswith(("/api/", "/clips/")):
        return JSONResponse({"error": "No autorizado"}, status_code=401)
    return RedirectResponse("/login", status_code=303)


# ---------- login ----------
def _locked(ip: str) -> bool:
    now = time.time()
    FAILS[ip] = [t for t in FAILS.get(ip, []) if now - t < 300]
    return len(FAILS[ip]) >= 5


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@app.post("/login")
def login(request: Request, password: str = Form(...)):
    ip = request.client.host if request.client else "?"
    if _locked(ip):
        return templates.TemplateResponse(
            request, "login.html", {"error": "Demasiados intentos. Espera 5 minutos."}, status_code=429)
    if hmac.compare_digest(password.encode(), config.APP_PASSWORD.encode()):
        FAILS.pop(ip, None)
        request.session.clear()
        request.session["auth"] = True
        return RedirectResponse("/", status_code=303)
    FAILS.setdefault(ip, []).append(time.time())
    return templates.TemplateResponse(
        request, "login.html", {"error": "Contraseña incorrecta."}, status_code=401)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


# ---------- app ----------
@app.get("/", dependencies=[Depends(require_auth)])
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


class JobIn(BaseModel):
    url: str


def _work(job_id: str, url: str):
    def progress(step, msg):
        JOBS[job_id].update(step=step, message=msg)

    try:
        result = pipeline.run(url, config.DATA_DIR / job_id, progress)
        JOBS[job_id].update(status="done", step="done", message="¡Listo!", **result)
    except pipeline.PipelineError as e:
        JOBS[job_id].update(status="error", error=str(e))
    except Exception:
        JOBS[job_id].update(status="error", error="Error inesperado procesando el video.")
    finally:
        JOBS_LOCK.release()


@app.post("/api/jobs", dependencies=[Depends(require_auth)])
def create_job(body: JobIn, background: BackgroundTasks):
    try:
        url = pipeline.validate_url(body.url)
    except pipeline.PipelineError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    if not JOBS_LOCK.acquire(blocking=False):
        return JSONResponse({"error": "Ya hay un video procesándose. Espera a que termine."}, status_code=409)
    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"status": "running", "step": "download", "message": "En cola…", "clips": []}
    background.add_task(_work, job_id, url)
    return {"job_id": job_id}


@app.get("/api/jobs/{job_id}", dependencies=[Depends(require_auth)])
def job_status(job_id: str):
    if not JOB_ID.match(job_id) or job_id not in JOBS:
        raise HTTPException(404)
    return JOBS[job_id]


@app.get("/clips/{job_id}/{n}", dependencies=[Depends(require_auth)])
def clip(job_id: str, n: int, download: bool = False):
    if not JOB_ID.match(job_id) or not 1 <= n <= config.NUM_CLIPS:
        raise HTTPException(404)
    path = config.DATA_DIR / job_id / f"clip_{n}.mp4"
    if not path.is_file():
        raise HTTPException(404)
    return FileResponse(
        path, media_type="video/mp4",
        filename=f"clip_{n}.mp4" if download else None,
        content_disposition_type="attachment" if download else "inline")
