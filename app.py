"""Vercel entrypoint (FIX-09): Vercel's FastAPI preset looks for `app` in a root app.py. Render and uvicorn keep using
backend.main:app directly."""
from backend.main import app  # noqa: F401
