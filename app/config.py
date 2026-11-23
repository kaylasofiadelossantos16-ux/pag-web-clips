import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


APP_PASSWORD = os.getenv("APP_PASSWORD", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
DATA_DIR = Path(os.getenv("DATA_DIR", "data")).resolve()
MAX_VIDEO_MINUTES = _int("MAX_VIDEO_MINUTES", 180)
CLIP_MIN_SECONDS = _int("CLIP_MIN_SECONDS", 20)
CLIP_MAX_SECONDS = _int("CLIP_MAX_SECONDS", 60)
LIVE_RECORD_SECONDS = _int("LIVE_RECORD_SECONDS", 900)
LIVE_MAX_MB = _int("LIVE_MAX_MB", 150)
SUBTITLE_LANGS = [s.strip() for s in os.getenv("SUBTITLE_LANGS", "es,en").split(",") if s.strip()]
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax").lower()
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
YTDLP_COOKIES_FILE = os.getenv("YTDLP_COOKIES_FILE") or None
NUM_CLIPS = 5


def validate() -> None:
    missing = [n for n, v in [("APP_PASSWORD", APP_PASSWORD), ("SECRET_KEY", SECRET_KEY),
                              ("GEMINI_API_KEY", GEMINI_API_KEY)] if not v]
    if missing:
        sys.exit(f"Faltan variables en .env: {', '.join(missing)} (copia .env.example a .env)")
    if len(SECRET_KEY) < 32:
        sys.exit("SECRET_KEY debe tener al menos 32 caracteres.")
