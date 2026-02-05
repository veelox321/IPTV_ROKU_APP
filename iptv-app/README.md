# IPTV Backend (FastAPI)

Production-ready FastAPI backend for fetching IPTV channel data via Xtream Codes API.
The backend caches channel lists locally in JSON to avoid refetching on every request.

## Architecture overview

- **FastAPI** for REST API endpoints.
- **Pydantic models** for request/response validation.
- **Service layer** for authentication, caching, and IPTV fetch logic.
- **JSON cache** stored at `backend/app/data/channels.json` with a consistent schema.

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

## Refresh flow

1. Client calls `POST /refresh`.
2. The backend sets a thread-safe refreshing flag and returns immediately.
3. A background job downloads the playlist and parses it into normalized channels.
4. The cache is written to disk atomically and the refreshing flag is cleared.

## Cache lifecycle

The cache file uses a fixed schema to simplify API responses and protect against
corrupted data:

```json
{
  "timestamp": "2024-01-01T12:00:00+00:00",
  "host": "provider.example",
  "channel_count": 1234,
  "channels": [
    {
      "name": "Channel Name",
      "group": "News",
      "category": "tv",
      "url": "http://..."
    }
  ]
}
```

Invalid or malformed cache files are ignored safely, and the API will prompt for
refresh if no valid cache is present.

## IPTV categorization

Channel categories are normalized based on the `group-title` field in the M3U.
Matching is case-insensitive:

- `tv`: groups containing `tv` or `live`
- `movies`: groups containing `movie`, `vod`, or `film`
- `series`: groups containing `series` or `show`
- `other`: anything not matched above

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
Returns a paginated list of cached channels. Pagination is mandatory.

Query parameters:

- `page`: 1-indexed page number
- `page_size`: max 100 items per page
- `search`: optional case-insensitive search
- `category`: optional category filter (`tv`, `movies`, `series`, `other`)

### POST `/refresh`
Forces a cache refresh by fetching fresh data from the IPTV provider.

### GET `/status`
Returns login status, cache metadata, and refresh state.

### GET `/stats`
Returns total counts for TV, movies, series, and other categories.

### GET `/groups`
Returns available categories found in cached channels.

### GET `/health`
Basic service health check.

## Notes

- Credentials are never stored on disk or committed to git.
- Cache data is stored locally in JSON and can be refreshed manually.
- SSL verification is configurable for providers using self-signed certificates.
