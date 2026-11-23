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
