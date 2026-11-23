---
title: Mis clips privados
emoji: 🎬
colorFrom: purple
colorTo: pink
sdk: docker
app_port: 7860
pinned: false
---

# pag-web-clips
Aplicación web privada (FastAPI + Tailwind) que, desde un enlace de YouTube, Twitch o Kick, descarga el video y su transcripción con yt-dlp, pide a Gemini (gratis) los 5 momentos más virales y los corta en vertical 9:16 con FFmpeg.

## Instalación
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # y edita los valores
```
Requiere **FFmpeg** instalado (`apt install ffmpeg` / `brew install ffmpeg`).

## Ejecutar
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Abre http://127.0.0.1:8000 e introduce tu `APP_PASSWORD`. Si lo expones a internet, ponlo detrás de HTTPS y activa `COOKIE_SECURE=true`.

## Notas
- Si el video no trae subtítulos, se transcribe el audio en local con faster-whisper (gratis; la primera vez descarga el modelo y en CPU puede tardar).
- Los directos en emisión se rechazan; usa el VOD cuando termine.
- Procesa un video a la vez. Los clips se guardan en `DATA_DIR` (ignorado por git).

## Desplegar gratis en Hugging Face Spaces
1. Crea un Space en https://huggingface.co/new-space con SDK **Docker** (hardware CPU basic, gratis) y ponlo en **Private**.
2. Sube este repo al Space (`git remote add space https://huggingface.co/spaces/<usuario>/<space>` y `git push space main`) o sincronízalo desde GitHub.
3. En *Settings → Variables and secrets* crea estos **Secrets**: `GEMINI_API_KEY`, `APP_PASSWORD` y `SECRET_KEY` (cadena aleatoria de 32+ caracteres).
4. Cuando termine el build, abre la URL directa `https://<usuario>-<space>.hf.space` (mejor que el iframe de huggingface.co, por las cookies).

Limitaciones: el disco es efímero (los clips se borran al reiniciar; descárgalos al terminar) y YouTube suele bloquear las IP de centros de datos, así que algunos enlaces pueden fallar sin un `cookies.txt`.
