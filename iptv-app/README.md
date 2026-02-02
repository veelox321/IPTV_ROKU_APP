# IPTV Backend (FastAPI)

Production-ready FastAPI backend for fetching IPTV channel data via Xtream Codes API.
The backend caches channel lists locally in JSON to avoid refetching on every request.

## Architecture overview

- **FastAPI** for REST API endpoints.
- **Pydantic models** for request/response validation.
- **Service layer** for authentication, caching, and IPTV fetch logic.
- **JSON cache** stored at `backend/app/data/channels.json` with configurable TTL.

## Project structure

```
iptv-app/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── services/
│   │   │   ├── iptv.py
│   │   │   ├── cache.py
│   │   │   └── auth.py
│   │   ├── routes/
│   │   │   └── channels.py
│   │   └── data/
│   │       └── channels.json
│   ├── requirements.txt
│   └── .env.example
├── .gitignore
├── README.md
```

## Environment variables

Create a `.env` file in `backend/` and set the following values:

```
IPTV_HOST=https://example-iptv-provider.com
IPTV_USERNAME=your_username
IPTV_PASSWORD=your_password
CACHE_TTL_SECONDS=21600
VERIFY_SSL=true
```

## Local development setup (Windows / Anaconda)

1. Create and activate a virtual environment:

```
conda create -n iptv-backend python=3.11
conda activate iptv-backend
```

2. Install dependencies:

```
pip install -r backend/requirements.txt
```

3. Copy the example environment file and update it:

```
copy backend\.env.example backend\.env
```

4. Run the backend locally (from the repo root):

```
uvicorn backend.app.main:app --reload
uvicorn backend.app.main:app --reload --log-level debug

```

5. (Optional) Run the Streamlit UI (from the repo root):

```
streamlit run backend/streamlit_app.py
```

## API endpoints

### POST `/login`
Stores IPTV credentials in memory for the current process.

```json
{
  "host": "https://provider.example",
  "username": "user",
  "password": "pass"
}
```

### GET `/channels`
Returns cached channels if valid, otherwise fetches from the IPTV provider.
Use `?search=` to filter channels by name (case-insensitive).

### POST `/refresh`
Forces a cache refresh by fetching fresh data from the IPTV provider.

## Notes

- Credentials are never stored on disk or committed to git.
- Cache data is stored locally in JSON and can be refreshed manually.
- SSL verification is configurable for providers using self-signed certificates.
