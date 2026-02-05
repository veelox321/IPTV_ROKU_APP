# Architecture Overview

This repository is organized into three independent surfaces:

- **backend/**: FastAPI service that fetches, parses, and caches IPTV playlists.
- **frontend-web/**: Vite + React + Tailwind UI for end-users (TV-first navigation).
- **frontend-streamlit/**: Streamlit admin/debug console.

## Data Flow

1. Admin configures IPTV credentials (via `.env` or `/login`).
2. Backend refreshes the playlist and writes cache metadata to `backend/data/channels.json`.
3. Web UI fetches `GET /channels`, `GET /stats`, and `GET /status` to render tiles.

## Key Decisions

- **Pydantic v2 + pydantic-settings** for configuration with Python 3.12.
- **File-backed JSON cache** with precomputed stats/group counts for O(1) endpoints.
- **Streamlit kept admin-only** to avoid UI coupling with the user-facing experience.
- **React frontend is the main UI**, with hooks and service layer isolating API access.

## Future Targets

Roku / Fire TV targets can consume the same backend APIs (status, channels, groups). The React UI already uses focus-first navigation to match remote control interactions.
