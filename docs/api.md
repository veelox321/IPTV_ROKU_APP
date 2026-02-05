# API Reference

Base URL: `http://localhost:8000`

## GET /status
Returns backend status and cache metadata.

## POST /refresh
Triggers a background refresh of the IPTV playlist.

## GET /channels
Paginated list of cached channels.

Query params:
- `page` (int, required)
- `page_size` (int, max 100)
- `search` (optional)
- `category` (optional: tv, movies, series, other)
- `group` (optional)

## GET /stats
Returns channel counts for `tv`, `movies`, `series`, `other`, and `total`.

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
