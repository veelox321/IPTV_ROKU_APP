# IPTV Backend (FastAPI)

Production-ready FastAPI backend for fetching IPTV channel data via the Xtream Codes
M3U API. The backend caches channel lists locally in JSON to avoid refetching on
every request and supports scalable pagination for large catalogs.

## Architecture overview

- **FastAPI** for REST API endpoints.
- **Pydantic models** for request/response validation.
- **Service layer** for authentication, caching, and IPTV fetch logic.
- **JSON cache** stored at `backend/app/data/channels.json` with configurable TTL.

## Refresh flow

1. `/login` stores credentials in memory.
2. `/refresh` schedules a background refresh and returns immediately.
3. The background job fetches the M3U playlist, parses channels, and writes cache data.
4. `/status` exposes refresh progress and last refresh timestamp.

The refresh operation is protected by a thread-safe flag to prevent duplicate jobs.

## Cache lifecycle

Cache entries follow a strict schema:

```json
{
  "timestamp": "2024-01-01T00:00:00+00:00",
  "host": "https://provider.example",
  "channel_count": 12345,
  "channels": []
}
```

The backend validates cache structure on load, refuses malformed payloads, and uses
the configured TTL to decide when the cache is stale.

## IPTV categorization

Channels are normalized into the following categories based on group/name keywords:

- `tv`: live TV, news, sports, and general live programming
- `movies`: films, cinema, and VOD labels
- `series`: TV series and show catalogs
- `other`: anything that doesn't match the above rules

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

4. Run the backend locally:

```
uvicorn app.main:app --reload
uvicorn app.main:app --reload --log-level debug

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
Returns cached channels with **mandatory** pagination. Use `page` and `page_size`
query params, along with optional `search` and `category` filters.

### POST `/refresh`
Schedules a non-blocking cache refresh by fetching fresh data from the IPTV provider.

### GET `/status`
Returns refresh status, last refresh timestamp, and cached channel count.

### GET `/stats`
Returns cached channel counts by normalized category.

### GET `/groups`
Returns distinct channel groups discovered in the cached playlist.

### GET `/health`
Basic service health check.

## Notes

- Credentials are never stored on disk or committed to git.
- Cache data is stored locally in JSON and can be refreshed manually.
- SSL verification is configurable for providers using self-signed certificates.
- The API never returns all channels at once; pagination is required.
