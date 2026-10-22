# Backend on Vercel (Python): feasibility report

FIX-06, 2026-10-22. No deploy yet: this decides **Vercel vs Codespaces** for P8-02 (Haider confirms first).

**Verdict: it fits.** Every hard limit has headroom. The real risks are behavioural (lifespan, per-instance state) and are checked in the first 45 minutes.

## Measured

| Check | Result | Vercel limit (docs read 2026-10-22) |
|---|---|---|
| Serve-time imports (all 13 endpoints hit, `LLM_ENABLED=false`) | fastapi, pydantic, google-genai, httpx, **pandas + numpy**. **Not** loaded: lightgbm, scikit-learn, scipy, feedparser, openpyxl | — |
| Why pandas/numpy load | Only `backend/api/insights.py` → `from backend.ml.features import FEATURES` (a label dict). Quant predictions are read from the DB; no model runs at request time | — |
| Linux py3.12 install size: full `requirements.txt` (minus pytest) | **317 MB** (scipy 110, pandas 41, sklearn 32, numpy 57, uvloop 16) | **500 MB** uncompressed for Python (5 GB "large functions" beta) |
| Serve set + pandas/numpy (today's imports) | **138 MB** | 500 MB |
| Serve set only (after moving `FEATURES`) | **41 MB** | 500 MB |
| Committed data the function needs | 10.5 MB (`openpsx.db` 9.9, model 0.5, seed 0.08) | — |
| Python version | Vercel: 3.12 (default), 3.13, 3.14; **no 3.11**. Full suite on 3.12.8 with the same pins: **368 passed** | — |
| Filesystem | DB opened `mode=ro`, `journal_mode=delete` → reads from a read-only bundle. The only serve-time write is `cache.db` (`macro.write` is script-only) | Writable `/tmp` only |
| Import time (`import backend.main`, Windows) | 1.6 s (≈ 0.5 s of it pandas) | cold start |
| Request body | voice clips are ~50–150 KB; the API's own cap is 10 MB | **4.5 MB** (413 above) |
| Longest request | refresh worst case ≈ 2 LLM calls × (15 s timeout + 2 s retry + 15 s) | Hobby: **300 s** default and max; 2 GB / 1 vCPU |

## Changes needed for the Vercel path (all small; none made yet)

1. **Entrypoint.** Add `[tool.vercel] entrypoint = "backend.main:app"` to a root `pyproject.toml`, or a one-line root `app.py` (`from backend.main import app`). `backend/main.py` stays frozen.
2. **Dependencies.** Vercel installs everything listed (no Python tree-shaking). Either:
   - accept the full `requirements.txt` (317 MB fits), or
   - split: `requirements.txt` = serve deps only (no uvicorn needed on Vercel); `requirements-dev.txt` = `-r requirements.txt` + pandas, numpy, scikit-learn, lightgbm, feedparser, openpyxl, uvicorn, pytest. Then update README / devcontainer install lines.

   Recommended: split, together with step 3 (41 MB, faster cold start).
3. **Drop pandas/numpy from the serve path.** Move `FEATURES` into a pandas-free module (e.g. `backend/ml/feature_labels.py`, re-exported by `features.py`). About 5 lines; tests unchanged.
4. **`vercel.json` (backend project, repo root).** `excludeFiles` for `frontend/**`, `_legacy_reference/**`, `docs/**`, `backend/tests/**`, `contracts/**`, `graphify-out/**`, `scripts/**`. Region `bom1` (Mumbai) instead of the default `iad1`, closer to judges in Pakistan.
5. **Environment (backend project).** `GEMINI_API_KEYS`, `GEMINI_MODEL`, `LLM_ENABLED=true`, `GROQ_API_KEY`, `CORS_ORIGINS=https://<frontend>.vercel.app` (no trailing slash), **`CACHE_DB_PATH=/tmp/cache.db`**, feature flags as in `.env.example`.
6. **Frontend project.** `NEXT_PUBLIC_API_BASE=https://<backend>.vercel.app`, `NEXT_PUBLIC_TUNNEL_SKIP_HEADER=false`, then redeploy (baked at build time).

## Risks to verify in the 45-minute timebox

1. **Lifespan → seed.** `main.py` loads the verdict seed in the ASGI `lifespan`. Vercel announced FastAPI lifespan support, but a community thread reports it not running under `vercel dev` / previews. Test: `/api/verdict/OGDC` must return `summary_status: CACHED` with 0 LLM calls. If not, add a lazy seed load on the first verdict cache miss (`startup.py`, ~5 lines).
2. **Per-instance state.** `cache.db`, the refresh rate limit and the daily LLM counter live per instance and reset on cold starts. That is acceptable for a demo; the seed reloads on every cold start.
3. **Cold start on stage.** Run `scripts/warm.py` against the backend URL before the pitch; check its timing.
4. **Python version.** The repo's `.python-version` still says `3.11` (kept from Render, D-58). Vercel doesn't offer 3.11 and falls back to its 3.12 default; change the pin to `3.12` explicitly. 3.12 is verified locally.

## Deploy steps (FIX-09; second deployment, Render untouched)

Repo side is done:
- root `app.py` (re-exports `backend.main:app`);
- root `vercel.json` (region `bom1`, `excludeFiles`);
- serve-only `requirements.txt` (FIX-08).

The bundle is about 41 MB of dependencies plus 10.5 MB of repo files. `.python-version` stays `3.11` for Render; Vercel treats an unsupported version as "use the default" (3.12).

1. vercel.com → Add New → Project → import `haiderhkhan/OpenPSX`. Name it e.g. `openpsx-api`. Leave Root Directory at the repo root; the Framework Preset should say **FastAPI**. Leave Build/Install at their defaults.
2. Environment variables (Production):

   | Variable | Value |
   |---|---|
   | `GEMINI_API_KEYS` | your keys |
   | `GROQ_API_KEY` | when you have it |
   | `CACHE_DB_PATH` | `/tmp/cache.db` |
   | `LLM_ENABLED` | `true` |
   | `GEMINI_MODEL` | `gemini-3.1-flash-lite` |
   | `GROQ_WHISPER_MODEL` | `whisper-large-v3-turbo` |
   | `LLM_DAILY_CALL_LIMIT` | `200` |
   | `APP_TZ` | `Asia/Karachi` |
   | `FEATURE_ETFS`, `FEATURE_MACRO_LLM`, `FEATURE_FISCAL_TOGGLE`, `FEATURE_VOICE` | `true` |
   | `CORS_ORIGINS` | the frontend URL once P8-03 exists (no trailing slash) |
3. Deploy, then check (the 45-minute timebox starts at step 1):
   - `curl -s https://<api>.vercel.app/api/health` → `"status":"ok"`
   - `curl -s https://<api>.vercel.app/api/verdict/HUBC` → `"summary_status":"CACHED"`. That proves the lifespan seed load ran (risk 1). A LIVE/TEMPLATE result means the seed did not load.
   - Final seed (FIX-12, commit `e21f63a`, 2026-10-23): expect HUBC POSITIVE 0.23 and OGDC POSITIVE 0.36, both CACHED. Deploy from `main` at or after that commit.
   - `python scripts/warm.py https://<api>.vercel.app` for the cold-start timing.
4. If it isn't serving both by the end of the timebox: stop, log it in `docs/MEMORY.md`, and use Render/Codespaces.

## Codespaces fallback (if Vercel fails the timebox)

Already prepared in `docs/CODESPACES.md` (D-58, G-27): public port 8000 via `scripts/run_codespace.sh`. The idle timeout defaults to 30 min (set 240 in GitHub settings before creating the Codespace); port traffic alone doesn't count as activity, but terminal output does, and uvicorn's access log provides it. Run `warm.py` 10 minutes before the pitch.
