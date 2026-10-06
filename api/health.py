from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

import verses
from realtime.manager import manager
from services.config import VERSION, broadcast_codes, is_production, openai_configured
from services.mosques import list_mosques

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok", "version": VERSION, "live_rooms": len(manager.live_rooms())}


@router.get("/ready")
async def ready():
    """Readiness: data loaded and, in production, the required secrets present."""
    checks = {
        "quran_corpus": len(verses._CORPUS) == 6236,
        "translations": all(len(verses._load_translation(l)) > 6236 for l in ("en", "ur", "hi")),
        "mosques": bool(list_mosques()),
        "openai_configured": openai_configured(),
        "broadcast_codes_configured": all(m["id"] in broadcast_codes() for m in list_mosques()),
    }
    required = ["quran_corpus", "translations", "mosques"]
    if is_production():
        required += ["openai_configured", "broadcast_codes_configured"]
    ok = all(checks[k] for k in required)
    return JSONResponse(
        {"status": "ready" if ok else "not_ready", "environment": "production" if is_production() else "development", "checks": checks},
        status_code=200 if ok else 503,
    )
