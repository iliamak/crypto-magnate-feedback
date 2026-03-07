# Crypto Magnate Feedback System

Telegram Mini App for collecting bug reports and feature ideas from beta testers of the Crypto Magnate mobile game.

## Architecture

```
Frontend (Telegram Mini App) → Backend (Flask) → Asana API
```

- **Frontend**: HTML + Tailwind CSS + Vanilla JS
- **Backend**: Python Flask
- **Storage**: Asana (tasks with attachments)

## Quick Start

### Backend

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file from template:
   ```bash
   cp .env.example .env
   ```

5. Fill in Asana credentials in `.env`:
   - `ASANA_ACCESS_TOKEN`: Your Asana Personal Access Token
   - `ASANA_PROJECT_GID`: Target project GID
   - `ASANA_WORKSPACE_GID`: Workspace GID

6. Run the server:
   ```bash
   python main.py
   ```

### Frontend

1. Update `API_URL` in `frontend/index.html` to point to your backend

2. Serve frontend with HTTPS (required for Telegram Mini Apps):
   - For local development: use ngrok or similar
   - For production: deploy to Vercel, Netlify, or any static hosting with HTTPS

### Telegram Bot Setup

1. Create a bot via @BotFather
2. Configure Web App URL:
   - Use `/setmenubutton` to set the URL of your deployed frontend
   - Or use inline buttons with `web_app: { url: "https://your-domain.com" }`

## API Endpoints

### POST /api/report

Submit a feedback report (problem or idea).

**Content-Type**: `multipart/form-data`

**Fields**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| category | string | Yes | `problem` or `idea` |
| tg_id | string | Yes | Telegram user ID |
| username | string | No | Telegram username |
| os | string | No | User's OS |
| device | string | No | User's device |
| tg_version | string | No | Telegram version |
| lang | string | Yes | `ru` or `en` |
| playback_steps | string | Yes (problem) | Steps to reproduce |
| actual_result | string | Yes (problem) | What happened |
| expected_result | string | Yes (problem) | What should happen |
| idea_title | string | Yes (idea) | Idea title |
| idea_description | string | Yes (idea) | Idea details |
| improvement | string | Yes (idea) | Expected improvement |
| files | File[] | No | Screenshots/videos (max 50MB each) |

### GET /api/fields

Returns custom field GIDs for the Asana project. Use this once after deployment to look up GIDs for env vars.

**Response**: `{ "fields": [{ "gid": "...", "name": "...", "type": "text" }, ...] }`

### GET /health

Health check endpoint.

**Response**: `{ "status": "ok" }`

## File Structure

```
crypto-magnate-feedback/
├── frontend/
│   ├── index.html      # Main app file
│   ├── logo.png        # App logo
│   └── favicon.ico
├── backend/
│   ├── main.py         # Flask application
│   ├── requirements.txt
│   └── .env.example
├── README.md
└── .gitignore
```

## Deployment

### Frontend
- Static hosting with HTTPS
- Options: Vercel, Netlify, GitHub Pages

### Backend
- Python hosting with Flask support
- Options: Railway, Render, PythonAnywhere

### Custom Fields Setup (bug reports)

After deploying the backend:

1. Call `GET /api/fields` → get list of custom fields with GIDs
2. Add the corresponding GIDs as env vars:

| Env var | Asana field |
|---------|-------------|
| `ASANA_FIELD_PLAYBACK_STEPS` | Шаги воспроизведения |
| `ASANA_FIELD_EXPECTED_RESULT` | Ожидаемый результат |
| `ASANA_FIELD_ACTUAL_RESULT` | Фактический результат |
| `ASANA_FIELD_TG_ID_USERNAME` | Ваш TG ID / UserName TG |
| `ASANA_FIELD_OS` | Операционная система |
| `ASANA_FIELD_TGID` | TGID |

3. Restart the service.

If a GID is not set, that field is silently skipped — tasks are created without errors.
