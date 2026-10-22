# Backend on Vercel (Python): feasibility report

FIX-06, 2026-10-22. Decided (D-71, 2026-10-23): Vercel is the sole public deploy, as two projects; the click-by-click list is in "Deploy steps" below.

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
4. **Python version.** The repo's `.python-version` still says `3.11` (a leftover of the never-deployed Render plan, D-71). Vercel doesn't offer 3.11 and falls back to its 3.12 default; 3.12 is verified locally.

## Deploy steps: two Vercel projects (D-71: Vercel is the sole public deploy; Render was never deployed)

The repo side is done:
- root `app.py` (re-exports `backend.main:app`);
- root `vercel.json` (region `bom1`, `excludeFiles`);
- serve-only `requirements.txt` (FIX-08);
- the final seed (FIX-13, commit `0104ed6`: 30/30 LIVE).

The backend bundle is about 41 MB of dependencies plus 10.5 MB of repo files. `.python-version` says `3.11`, which Vercel doesn't offer, so it uses its default, 3.12; the suite passes on 3.12.

**Order:** backend first → frontend (needs the backend URL) → set `CORS_ORIGINS` on the backend → redeploy the backend.

### A. Backend project
1. vercel.com → **Add New… → Project** → **Import** `haiderhkhan/OpenPSX` (branch `main`).
2. Project Name: `openpsx-api`. **Root Directory: leave as `./`** (the repo root). Framework Preset: **FastAPI** (auto-detected). Build and Output Settings: leave the defaults.
3. Open **Environment Variables** and add:

   | Variable | Value |
   |---|---|
   | `GEMINI_API_KEYS` | your Gemini keys, comma-separated |
   | `CACHE_DB_PATH` | `/tmp/cache.db` |
   | `LLM_ENABLED` | `true` |
   | `GEMINI_MODEL` | `gemini-3.1-flash-lite` |
   | `LLM_DAILY_CALL_LIMIT` | `200` |
   | `APP_TZ` | `Asia/Karachi` |
   | `FEATURE_ETFS`, `FEATURE_MACRO_LLM`, `FEATURE_FISCAL_TOGGLE` | `true` |
   | `FEATURE_VOICE` | `false` (no Groq key, B-035) |
   | `GROQ_API_KEY` | leave unset (voice off) |
   | `CORS_ORIGINS` | leave unset for now; set in step C1 |
4. **Deploy**. When it finishes, copy the domain (e.g. `https://openpsx-api.vercel.app`) and check:
   - `https://<api>/api/health` → `"status":"ok"` and `"voice":false`
   - `https://<api>/api/verdict/HUBC` → POSITIVE, `"confidence":0.23`, `"summary_status":"CACHED"`. CACHED proves the lifespan seed load ran (risk 1).
   - `https://<api>/api/verdict/OGDC` → POSITIVE 0.36 CACHED.

### B. Frontend project
1. **Add New… → Project** → Import the **same** repo again.
2. Project Name: `openpsx`. **Root Directory: click Edit → choose `frontend`**. Framework Preset: **Next.js** (auto-detected).
3. Environment Variables:

   | Variable | Value |
   |---|---|
   | `NEXT_PUBLIC_API_BASE` | the backend URL from A4, with no trailing slash |
   | `NEXT_PUBLIC_USE_MOCKS` | `false` |
   | `NEXT_PUBLIC_TUNNEL_SKIP_HEADER` | `false` |
4. **Deploy**. `NEXT_PUBLIC_*` values are baked in at build time; if you change one, redeploy.

### C. Connect them
1. Backend project → **Settings → Environment Variables** → add `CORS_ORIGINS` = the frontend URL (e.g. `https://openpsx.vercel.app`, no trailing slash). The origin must match exactly; add any custom domain comma-separated.
2. Backend project → **Deployments** → latest → **⋯ → Redeploy**. Env changes apply only to new deployments.
3. Open the frontend URL. The overview loads, a stock page shows the verdict, and the browser console shows no CORS error. Then run `python scripts/warm.py https://<api>` to time the cold start.

**Timebox:** 45 minutes from A1. If `/api/health` plus a CACHED verdict aren't served by then, stop, log it in `docs/MEMORY.md`, and present from the local backup (`scripts/run_local.ps1`).

**Voice upload vs the 4.5 MB request limit.** Voice is off for the demo, but the upload fits. `MicButton` records with MediaRecorder (Opus/WebM, or AAC on Safari) and stops at 30 s (`MAX_RECORDING_MS`). At typical 32–128 kbps that is about 0.1–0.5 MB, and even 256 kbps is about 1 MB, all well under Vercel's 4.5 MB. No change needed. The API's own 10 MB cap is never reached on Vercel, which returns 413 above 4.5 MB first.

## Codespaces (superseded, D-71)

`docs/CODESPACES.md` and `scripts/run_codespace.sh` stay in the repo, unused. The backup for the pitch is the local launcher.
