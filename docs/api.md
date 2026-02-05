# API Reference

Base URL: `http://localhost:8000`

## GET /status
Returns backend status and cache metadata.
Payload fields:
- `logged_in`
- `refreshing`
- `cache_available`
- `last_refresh`
- `channel_count`

## POST /refresh
Triggers a background refresh of the IPTV playlist.
Returns HTTP 409 when credentials have not been supplied via `POST /login` or when a
refresh is already running.

## GET /channels
Paginated list of cached channels.
If the cache is missing, returns an empty list with `cached=false`.

Query params:
- `page` (int, required)
- `page_size` (int, max 100)
- `search` (optional)
- `category` (optional: tv, movies, series, other)
- `group` (optional)

## GET /stats
Returns channel counts for `tv`, `movies`, `series`, `other`, and `total`.
If the cache is missing, all counts are `0`.

## GET /groups
Returns available categories and top group titles with counts.

## GET /health
Basic health check.

## POST /login
Stores IPTV credentials in memory for the current process.

Payload:

```json
{
  "host": "https://provider.example",
  "username": "user",
  "password": "pass"
}
```
