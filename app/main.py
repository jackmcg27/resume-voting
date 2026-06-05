import socketio as _socketio

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import STATIC_DIR, UPLOAD_DIR
from .routers import admin, sessions, resumes, voting
from .socket import sio
from . import events  # noqa: F401 — registers socket.io event handlers


@asynccontextmanager
async def lifespan(app):
    if UPLOAD_DIR.exists():
        for f in UPLOAD_DIR.iterdir():
            try:
                f.unlink()
            except Exception:
                pass
    yield


_fastapi_app = FastAPI(title="Resume Voting", lifespan=lifespan)

_fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_fastapi_app.include_router(admin.router)
_fastapi_app.include_router(sessions.router)
_fastapi_app.include_router(resumes.router)
_fastapi_app.include_router(voting.router)

assets_dir = STATIC_DIR / "assets"
if assets_dir.is_dir():
    _fastapi_app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@_fastapi_app.get("/{full_path:path}")
async def spa(full_path: str):
    index = STATIC_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse(
        {"message": "Frontend not built. Run: cd frontend && npm install && npm run build"},
        status_code=503,
    )


# Wrap FastAPI with socket.io — socket.io handles /socket.io/* and passes
# everything else through to the FastAPI app.
app = _socketio.ASGIApp(sio, other_asgi_app=_fastapi_app)
