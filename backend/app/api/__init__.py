"""API routers.

`register_routers` mounts every feature router onto the app. Routers are kept thin —
they validate input, call a service, and shape the response. Business logic lives in
`app.services`.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.api import health, settings, workspaces


def register_routers(app: FastAPI) -> None:
    app.include_router(health.router)
    app.include_router(workspaces.router, prefix="/api/workspaces")
    app.include_router(settings.router, prefix="/api/settings")
