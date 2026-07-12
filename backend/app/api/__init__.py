"""API routers.

`register_routers` mounts every feature router onto the app. Routers are kept thin —
they validate input, call a service, and shape the response. Business logic lives in
`app.services`.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api import (
    chat,
    documents,
    health,
    interview,
    memory,
    settings,
    study,
    workspaces,
)


def register_routers(app: FastAPI) -> None:
    app.include_router(health.router)
    app.include_router(workspaces.router, prefix="/api/workspaces")
    app.include_router(settings.router, prefix="/api/settings")
    app.include_router(documents.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    app.include_router(memory.router, prefix="/api")
    app.include_router(study.router, prefix="/api")
    app.include_router(interview.router, prefix="/api")
