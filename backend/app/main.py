"""FastAPI application entry point.

Serves the JSON API under ``/api`` and the mobile-style web UI from ``web/`` at the root.
Run from the ``backend/`` directory:

    uvicorn app.main:app --reload
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.routes import router

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"

app = FastAPI(title="IDBI Wealth Copilot", version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Static UI mounted last so /api/* routes take precedence.
app.mount("/", StaticFiles(directory=str(_WEB_DIR), html=True), name="web")
