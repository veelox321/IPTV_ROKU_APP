# IPTV Web Frontend

A platform-agnostic React UI that follows the backend status contract and supports login → refresh → ready.

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

## Folder Structure

```
src/
  api/iptv.ts
  state/session.ts
  components/
    Dashboard.tsx
    LoadingScreen.tsx
    LoginScreen.tsx
  pages/
    AppShell.tsx
```

## Behavior Notes

- `/status` drives UI state.
- `/refresh` is only called if `logged_in=true`.
- Empty channel lists are valid until the cache is populated.
