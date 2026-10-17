# Backend on GitHub Codespaces (P8-02, D-58)

The backend runs in a Codespace on `haiderhkhan/OpenPSX`, port 8000 set to **public**. The frontend runs on Vercel.
Config: `.devcontainer/devcontainer.json` (Python 3.11, gh CLI, `pip install -r requirements.txt` on create).
Start: `bash scripts/run_codespace.sh`.
API URL: `https://<codespace-name>-8000.app.github.dev`.

## 1. Codespaces secrets (one-off)
`backend/config.py` reads every setting with `os.getenv`. `load_dotenv` never overrides a real env var, and `.env` isn't in git, so in a Codespace the secrets are the only source.

| Secret | Value | Needed? |
|---|---|---|
| `GEMINI_API_KEYS` | your Gemini keys, comma-separated | yes (without it every LLM part is a template; seeded verdicts still load as CACHED) |
| `GROQ_API_KEY` | your real Groq key (not `your-groq-key`) | optional: no key → the mic hides itself |
| `CORS_ORIGINS` | `https://<your-vercel-domain>,http://localhost:3000` | yes, once the Vercel URL exists (P8-03) |

The other variables keep their defaults, so you don't need to set them.

**How to set them:**
1. Go to github.com → profile picture → **Settings** → **Codespaces** → **Codespaces secrets** → **New secret**.
2. Enter the name and value, and set **Repository access** to `haiderhkhan/OpenPSX`.
3. Click **Add secret**.

From the CLI, run `gh secret set GEMINI_API_KEYS --user --repos haiderhkhan/OpenPSX` and paste the value at the prompt. If gh refuses, run `gh auth refresh -s codespace` first.

- Secrets become env vars when the Codespace **starts**. After you add or change one, stop and restart the Codespace; a rebuild isn't needed.
- `CORS_ORIGINS` must match exactly: `https://`, no trailing slash, the production domain. Vercel preview URLs (`…-git-….vercel.app`) won't match.

## 2. Demo-day wake-up checklist (start about 30 min before)
1. **Idle timeout, set beforehand:** github.com → Settings → Codespaces → **Default idle timeout** → `240` (the maximum). It only applies to Codespaces created *after* the change, so if your Codespace is older, delete it and create a new one. Terminal output resets the timer, and `run_codespace.sh` prints a log line per request. During long quiet stretches, keep the Codespace tab open.
2. **Start the Codespace:** github.com/codespaces → the OpenPSX Codespace → **Open in browser**. If none exists, open the repo → **Code** → **Codespaces** → **Create codespace on main** (the first build takes a few minutes for pip).
3. **Pull the latest code:** run `git pull` in the Codespace terminal.
4. **Run:** `bash scripts/run_codespace.sh`. Wait for `Public API: https://….app.github.dev`.
5. **Check the port is public:** open the **Ports** tab and confirm port 8000 shows **Public**. If the script printed "Could not make port 8000 public", right-click 8000 → **Port Visibility** → **Public**.
6. **Warm it** from a second terminal (or from your laptop): `python scripts/warm.py https://<name>-8000.app.github.dev`. Expect `17 requests, 0 not 200`.
7. **Check the frontend:** open the Vercel URL in a **private window** and confirm a stock page shows its verdict and the chat answers (see §3).
8. **Keep the tab open** and don't press Ctrl+C. If the Codespace stopped anyway, repeat steps 2, 4, 5 and 6; the URL stays the same for the same Codespace.

**If the Codespace is unusable**, fall back to `scripts/run_local.ps1` on the laptop (P8-04).

## 3. Verifying cross-origin fetch (Vercel → Codespace)
Set `NEXT_PUBLIC_API_BASE=https://<name>-8000.app.github.dev` (no trailing slash) and `NEXT_PUBLIC_USE_MOCKS=false` on Vercel, then redeploy. `NEXT_PUBLIC_*` values are baked in at build time.

1. **Port is public and the app answers.** On the laptop, in PowerShell:
   `curl.exe -s https://<name>-8000.app.github.dev/api/health`
   - JSON → good.
   - HTML (a GitHub sign-in or warning page) → the port is still private, or GitHub's page is in front of it.
2. **CORS preflight** (the chat POST sends `Content-Type: application/json`, which triggers one):
   `curl.exe -si -X OPTIONS https://<name>-8000.app.github.dev/api/chat -H "Origin: https://<vercel-domain>" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: content-type"`
   - Expect `200` and `access-control-allow-origin: https://<vercel-domain>`.
   - `400 Disallowed CORS origin` → `CORS_ORIGINS` is wrong or wasn't loaded. Fix the secret, restart the Codespace, and run the script again.
3. **Browser warning page.**
   - Open `https://<name>-8000.app.github.dev/api/health` in a normal browser tab.
   - GitHub may show a warning page about opening a development port in someone's Codespace before it forwards you. Click through it; you should then see the health JSON.
   - That page is meant for people visiting the URL directly. Step 4 checks that it doesn't block the site's own `fetch` calls.
4. **The real check, in a fresh private window** (one that hasn't clicked through the warning, like a judge's browser):
   1. Open the Vercel URL, then **DevTools** (F12).
   2. In **Network**, filter `api/`, open `/stock/OGDC` and ask the chat a question.
   3. Every `/api/…` request should be `200`, with `access-control-allow-origin` in its response headers.
   4. The **Console** should show no CORS errors.
   - A CORS error together with an HTML response from `github.dev` means GitHub's page is intercepting fetches. Log it in `BUGS.md` and use the local backup (P8-04) for the demo.
