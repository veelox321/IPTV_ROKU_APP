# IPTV ROKU App

A FastAPI IPTV backend with platform-agnostic frontends (web + Streamlit) that honor a strict login → refresh → ready flow.

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Web UI

```bash
cd frontend-web
npm install
npm run dev
```

### Streamlit Admin Console

```bash
cd frontend-streamlit
streamlit run app.py
```

> **Note:** The backend requirements already include Streamlit.

## Login & Refresh Flow

1. **Login**
   - `POST /login` is the only way to set credentials.
   - Credentials live **in memory only** (no disk persistence).
2. **Refresh**
   - `POST /refresh` starts a background cache refresh **only if logged in**.
   - Returns `409` if not logged in or if a refresh is already running.
3. **Status**
   - `GET /status` is the single source of truth for UI state.

## Why Channels Might Be Empty

- The channel cache is **not** stored in the git repo.
- If the cache is missing, `/channels` returns an empty list and `/stats` returns zero counts.
- This is expected until a refresh completes.

## Cache Location

Channel caches are stored outside the repo by default:

- `~/.cache/iptv_roku_app/channels.json`

Override with `CACHE_DIR` if needed, but keep it out of git-tracked paths.

## API Summary

- `POST /login`
- `POST /refresh`
- `GET /status`
- `GET /channels`
- `GET /stats`
- `GET /groups`
- `GET /health`

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [FLOW.md](FLOW.md)
