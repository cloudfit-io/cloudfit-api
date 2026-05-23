"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import snapshot
from .config import settings
from .routers import diff, instances, providers, recommend


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm the snapshot cache once at startup so the first request is fast.
    snapshot.load_snapshot()
    yield


app = FastAPI(
    title=settings.title,
    version=settings.version,
    description=settings.description,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommend.router)
app.include_router(instances.router)
app.include_router(providers.router)
app.include_router(diff.router)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "name": settings.title,
        "version": settings.version,
        "instances": len(snapshot.all_instances()),
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}
