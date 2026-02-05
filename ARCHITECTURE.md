# Architecture

## Overview

The project is split into three layers:

- **Backend (FastAPI)** — IPTV login, refresh, caching, and API endpoints.
- **Web UI (Vite + React)** — Platform-agnostic UI that follows the backend status contract.
- **Streamlit Admin UI** — Lightweight admin/debug console for login and cache visibility.

## Backend

- **Credentials** are stored **in memory** only via `POST /login`.
- **Cache** lives outside the repo under `~/.cache/iptv_roku_app` (or `CACHE_DIR`).
- **Refresh** uses background tasks to fetch and parse M3U playlists.
- **Status** (`GET /status`) is the single source of truth for UI state.

### Key Modules

- `backend/app/routes/channels.py` — API endpoints.
- `backend/app/services/auth.py` — In-memory credentials.
- `backend/app/services/cache.py` — Disk cache outside git.
- `backend/app/services/iptv.py` — Fetching/parsing M3U playlists.

## Web UI

The web UI lives in `frontend-web/src` and is organized for clear separation:

- `api/iptv.ts` — Centralized API client.
- `state/session.ts` — Session state machine (BOOT → LOGIN → REFRESH → READY).
- `components/` — Login, Loading, Dashboard.
- `pages/` — Application shell.

## Streamlit

The Streamlit UI mirrors the backend state:

- Reads `/status` before allowing refresh.
- Displays cache stats and group summaries.
