"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from promptshield import __version__
from promptshield.api.routes import router

app = FastAPI(
    title="PromptShield API",
    version=__version__,
    description="Educational prompt-injection firewall for AI agents.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/v1")


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "promptshield", "docs": "/docs", "openapi": "/openapi.json"}
