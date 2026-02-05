# IPTV Web Frontend

This is the main user-facing UI (Vite + React + Tailwind + Radix/MUI). It is designed for TV-style navigation and consumes the FastAPI backend.

## Requirements

- Node.js 18+
- Backend running on `http://localhost:8000`

## Setup

```bash
npm install
npm run dev
```

## Environment Variables

Create a `.env` file in `frontend-web/` (optional):

```
VITE_API_BASE_URL=http://localhost:8000
```

## Notes

- The UI fetches channel data and stats through `src/services/api.ts`.
- Navigation is optimized for remote control input (arrow keys + enter).
