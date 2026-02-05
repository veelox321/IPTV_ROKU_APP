# IPTV Debug Runbook

## 1) Start backend
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Expected logs:
- `Application startup instance_id=...` with PID/cwd/sys.path
- `Registered route:` lines showing `/status`, `/refresh`, `/debug/cache`, `/debug/selftest`

## 2) Check status (no cache yet)
```bash
curl -s http://localhost:8000/status | jq
```
Expected:
- `cache_available=false`
- `channel_count=0`

## 3) Inspect cache diagnostics
```bash
curl -s http://localhost:8000/debug/cache | jq
```
Expected:
- `cache_exists=false` (first run)
- `cache_path` is an absolute path under `~/.cache/iptv_roku_app`
- `refreshing=false`

## 4) Login
```bash
curl -s -X POST http://localhost:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"host":"YOUR_HOST","username":"YOUR_USER","password":"YOUR_PASS"}' | jq
```
Expected:
- `status: ok`

## 5) Trigger refresh
```bash
curl -s -X POST http://localhost:8000/refresh | jq
```
Expected:
- `status: started`

## 6) Poll status
```bash
watch -n 2 'curl -s http://localhost:8000/status | jq'
```
Expected while refreshing:
- `refreshing=true`

Expected on success:
- `refreshing=false`
- `refresh_status=success`
- `last_successful_refresh` populated

## 7) Re-check cache
```bash
curl -s http://localhost:8000/debug/cache | jq
```
Expected on success:
- `cache_exists=true`
- `cache_size_bytes>0`
- `load_cache_summary.channel_count>0`

If cache is still missing:
- Compare `cache_path`, `cwd`, and `pid` from `/debug/cache` vs startup logs.
- If the path differs across processes, uvicorn reload is likely spawning multiple workers.

## 8) Use selftest to verify upstream reachability
```bash
curl -s -X POST http://localhost:8000/debug/selftest | jq
```
Expected:
- `dns_ok=true` if DNS resolves
- `tcp_ok=true` and `http_status=200` if the host is reachable
- `content_length` may be empty for chunked responses

### If X then Y
- **`refresh_status=failed` + `last_error` populated** → upstream fetch/parse failed; cache should remain intact.
- **`cache_path` differs across processes** → fix uvicorn reload config or run a single worker.
- **`refreshing=true` for long periods** → check `refresh_started_at` in `/debug/cache` and refresh logs to see if the job hung.
