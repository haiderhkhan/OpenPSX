"""FastAPI app. Written once in P0-04 and frozen: add behaviour in routers or `startup.py`, not here."""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend import config, startup
from backend.api import ApiException, chat, insights, market
from backend.schemas.common import ApiError, ErrorBody, ErrorCode


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    startup.on_startup()
    yield


app = FastAPI(title="OPEN PSX API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
for module in (market, insights, chat):
    app.include_router(module.router, prefix="/api")


def _error(status_code: int, code: ErrorCode, message: str) -> JSONResponse:
    body = ApiError(error=ErrorBody(code=code, message=message))
    return JSONResponse(status_code=status_code, content=body.model_dump())


@app.exception_handler(ApiException)
async def api_exception_handler(request: Request, exc: ApiException) -> JSONResponse:
    return _error(exc.status_code, exc.code, exc.message)


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    first = exc.errors()[0] if exc.errors() else {}
    where = ".".join(str(part) for part in first.get("loc", ()))
    return _error(400, "BAD_REQUEST", f"{where}: {first.get('msg', 'invalid request')}")
