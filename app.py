"""Vercel entrypoint (FIX-09): Vercel's FastAPI preset looks for `app` in a root app.py. Local uvicorn
(run_local.ps1) keeps using backend.main:app directly."""
from backend.main import app  # noqa: F401
