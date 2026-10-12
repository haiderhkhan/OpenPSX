"""Shared API helpers: the error type every router raises, and the fixture loader for stubs."""
from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from backend import config
from backend.schemas.common import ErrorCode

M = TypeVar("M", bound=BaseModel)


class ApiException(Exception):
    """Raise from any endpoint; `backend.main` turns it into an `ApiError` body (SCHEMA.md §4.1)."""

    def __init__(self, status_code: int, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def load_fixture(name: str, model: type[M]) -> M:
    """Load `contracts/fixtures/<name>` and validate it through its contract model."""
    return model.model_validate_json((config.FIXTURES_DIR / name).read_text(encoding="utf-8"))
