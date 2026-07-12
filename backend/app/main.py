"""FastAPI application factory.

Keeps app construction in one place: middleware, router registration, and lifecycle.
Business logic never lives here.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import register_routers
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup / shutdown hooks (background workers, warmups) attach here later.
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="InterviewOS API",
        version=__version__,
        summary="AI-powered interview preparation workspace.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_routers(app)
    return app


app = create_app()
