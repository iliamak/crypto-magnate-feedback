# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Style

Respond concisely and to the point. No preamble, no filler phrases, no restating what the user said. Lead with the answer or action.

## What This Is

Telegram Mini App for collecting bug reports and feature ideas from beta testers of the Crypto Magnate mobile game. Reports are submitted to Asana via OAuth.

```
Frontend (Telegram Mini App) → Backend (Flask) → Asana API
```

## Commands

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
python main.py                  # Runs on port 8000 by default
```

Production: `gunicorn main:app`

### Frontend

The frontend is a single static HTML file. Serve it with HTTPS (Telegram Mini Apps require it). For local dev, use ngrok or similar. In production, it deploys to Vercel automatically (`vercel.json` sets `outputDirectory: frontend`).

## Architecture

### Frontend (`frontend/index.html`)

Single self-contained HTML file. No build step. Uses:
- Tailwind CSS (CDN)
- `telegram-web-app.js` (CDN) — reads `window.Telegram.WebApp` for user data (tg_id, username, language, platform, device)
- Montserrat font (Google Fonts CDN)

The app auto-detects device info from Telegram's WebApp API and populates hidden fields. Users fill in one of two forms (problem/idea) and submit via `multipart/form-data` to the backend. `API_URL` constant at the top of the `<script>` block points to the backend.

Safe area padding uses `--tg-safe-area-inset-top` + `--tg-content-safe-area-inset-top` CSS variables injected by Telegram.

### Backend (`backend/main.py`)

Flask app, single file. Key behavior:
- Uses Asana OAuth (not PAT): reads `ASANA_CLIENT_ID`, `ASANA_CLIENT_SECRET`, `ASANA_REFRESH_TOKEN` and exchanges for short-lived access tokens, caching them until expiry.
- `POST /api/report` — accepts `multipart/form-data`, validates, creates an Asana task with HTML-formatted notes, then uploads file attachments (images/videos, max 50MB each, problem reports only).
- `GET /health` — returns `{"status": "ok"}`

### Environment Variables (backend)

| Variable | Description |
|----------|-------------|
| `ASANA_CLIENT_ID` | Asana OAuth app client ID |
| `ASANA_CLIENT_SECRET` | Asana OAuth app client secret |
| `ASANA_REFRESH_TOKEN` | Long-lived refresh token from Asana OAuth flow |
| `ASANA_PROJECT_GID` | Target Asana project GID |
| `ASANA_WORKSPACE_GID` | Asana workspace GID |
| `ALLOWED_ORIGINS` | CORS origins, comma-separated or `*` |
| `PORT` | Server port (default: 8000) |

## Deployment

- **Frontend**: Vercel (static, `outputDirectory: frontend`)
- **Backend**: Render — https://crypto-magnate-feedback.onrender.com

After deploying the backend, update `API_URL` in `frontend/index.html` to point to it.
