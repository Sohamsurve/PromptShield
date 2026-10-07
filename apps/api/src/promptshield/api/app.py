"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from promptshield import __version__
from promptshield.api.routes import router
from promptshield.detect.judge import log_judge_startup

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log_judge_startup()
    yield


app = FastAPI(
    title="PromptShield API",
    version=__version__,
    description="Educational prompt-injection firewall for AI agents.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3010",
        "http://127.0.0.1:3010",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/v1")


def custom_openapi() -> dict[str, Any]:
    """Include WebSocket paths from README §6 (not emitted by FastAPI by default)."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    paths = schema.setdefault("paths", {})
    ws_doc = {
        "get": {
            "tags": ["websocket"],
            "summary": "WebSocket (upgrade)",
            "description": "RFC6455 WebSocket endpoint. Clients connect with `ws://` / `wss://`.",
            "responses": {"101": {"description": "Switching Protocols"}},
        }
    }
    paths.setdefault("/v1/ws/stream", ws_doc)
    paths.setdefault("/v1/ws/runs/{run_id}", {
        "get": {
            **ws_doc["get"],
            "summary": "WebSocket run stream",
            "parameters": [
                {
                    "name": "run_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"},
                }
            ],
        }
    })
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "promptshield", "docs": "/docs", "openapi": "/openapi.json"}
