# IPTV Roku App (Refactored)

Production-ready IPTV stack with a FastAPI backend, a TV-first React UI, and a Streamlit admin console.

## Repository Structure

```
IPTV_ROKU_APP/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── routes/
│   │   │   └── channels.py
│   │   ├── services/
│   │   │   ├── auth.py
│   │   │   ├── cache.py
│   │   │   └── iptv.py
│   │   └── utils/
│   │       └── logging.py
│   ├── data/
│   │   └── channels.json
│   └── requirements.txt
├── frontend-web/
│   ├── public/
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── frontend-streamlit/
│   ├── app.py
│   ├── components.py
│   └── README.md
├── docs/
│   ├── architecture.md
│   ├── api.md
│   └── figma-to-code.md
├── .gitignore
└── README.md
```

## Backend (FastAPI)

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### Run

```bash
uvicorn backend.app.main:app --reload
```

### Environment Variables

Create `backend/.env`:

```
IPTV_HOST=https://provider.example
IPTV_USERNAME=user
IPTV_PASSWORD=pass
CACHE_TTL_SECONDS=21600
VERIFY_SSL=true
DEBUG=false
```

## Web Frontend (Main UI)

```bash
cd frontend-web
npm install
npm run dev
```

Optional `.env`:

```
VITE_API_BASE_URL=http://localhost:8000
```

## Streamlit Admin UI

```bash
cd frontend-streamlit
streamlit run app.py
```

## Docs

See `docs/architecture.md` for system design, `docs/api.md` for endpoint details, and `docs/figma-to-code.md` for frontend integration guidance.
