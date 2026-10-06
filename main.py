from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

import logger  # noqa: F401  (configures logging)
from api.broadcast import router as broadcast_router
from api.health import router as health_router
from api.live_audio import router as live_audio_router
from api.transcription import router as transcription_router
from api.translation import router as translation_router
from realtime.ws import router as ws_router
from services.config import VERSION, allowed_origins, is_production

FRONTEND = Path(__file__).resolve().parent / "frontend"

app = FastAPI(
    title="Minbar",
    version=VERSION,
    description="Real-time Friday sermon translation for non-Arabic speakers.",
    docs_url=None if is_production() else "/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Broadcaster-Token"],
)

_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "img-src 'self' data:; "
    "connect-src 'self' ws: wss:; "
    "media-src 'self' blob:; "
    "frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "microphone=(self), camera=(), geolocation=()")
    response.headers.setdefault("Content-Security-Policy", _CSP)
    if request.url.scheme == "https":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
    return response


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    import logging

    logging.getLogger("minbar").exception("unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": {"code": "server_error", "message": "حدث خطأ غير متوقع في الخادم."}})


def _page(name: str):
    async def handler():
        return FileResponse(FRONTEND / name, headers={"Cache-Control": "no-cache"})
    return handler


def _redirect(target: str):
    async def handler(request: Request):
        query = f"?{request.url.query}" if request.url.query else ""
        return RedirectResponse(target + query, status_code=301)
    return handler


for _path, _file in {"/": "index", "/listen": "listen", "/broadcast": "broadcast", "/privacy": "privacy"}.items():
    app.add_api_route(_path, _page(f"{_file}.html"), include_in_schema=False)
    app.add_api_route(f"/{_file}.html", _redirect(_path), include_in_schema=False)

app.include_router(health_router)
app.include_router(broadcast_router)
app.include_router(live_audio_router)
app.include_router(transcription_router)
app.include_router(translation_router)
app.include_router(ws_router)

app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")
app.mount("/css", StaticFiles(directory=FRONTEND / "css"), name="css")
