from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import auth, jobs, publishing, social
from app.core.exceptions import (
    AppException,
    InvalidStateTransitionError,
    NotFoundError,
    PermissionError,
    PublishingError,
    VideoProcessingError,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown logic."""
    logger.info("FastQuickTikGram API starting up...")
    yield
    logger.info("FastQuickTikGram API shutting down...")


app = FastAPI(
    title="FastQuickTikGram API",
    description="Backend API for the FastQuickTikGram video content creator SaaS platform.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        # TODO: Add production domain(s) here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Exception handlers
# ------------------------------------------------------------------


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message, "resource": exc.resource},
    )


@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": exc.message},
    )


@app.exception_handler(InvalidStateTransitionError)
async def state_transition_handler(
    request: Request, exc: InvalidStateTransitionError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.message,
            "current_state": exc.current_state,
            "target_state": exc.target_state,
        },
    )


@app.exception_handler(VideoProcessingError)
async def video_processing_handler(
    request: Request, exc: VideoProcessingError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": exc.message},
    )


@app.exception_handler(PublishingError)
async def publishing_error_handler(request: Request, exc: PublishingError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": exc.message, "platform": exc.platform},
    )


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": exc.message},
    )


# ------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------
app.include_router(auth.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(social.router, prefix="/api/v1")
app.include_router(publishing.router, prefix="/api/v1")


# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------

@app.get("/health", tags=["health"], summary="Health check")
async def health_check() -> dict:
    return {"status": "ok", "service": "fastquicktikgram-api"}


@app.get("/", tags=["root"], include_in_schema=False)
async def root() -> dict:
    return {"message": "FastQuickTikGram API", "docs": "/docs"}
