# UI Flow

## State Machine

```
BOOT
  │
  └── GET /status ──┬─ logged_in=false ──> NOT_LOGGED_IN
                   ├─ refreshing=true ─> REFRESHING
                   └─ cache_available=false ─> REFRESHING
                                           └─ cache_available=true ─> READY

NOT_LOGGED_IN
  └── POST /login ──> LOGGING_IN ──> REFRESHING

REFRESHING
  └── POST /refresh (only when logged_in=true)
  └── poll GET /status until refreshing=false

READY
  └── GET /channels /stats /groups (empty lists are valid)
```

## Sequence Diagrams (text)

### Login + Refresh

```
UI                 Backend
│   GET /status      │
│───────────────────>│
│<───────────────────│  { logged_in: false }
│
│   POST /login       │
│───────────────────>│
│<───────────────────│  { status: ok }
│
│   POST /refresh     │
│───────────────────>│
│<───────────────────│  { status: started }
│
│   GET /status       │
│───────────────────>│
│<───────────────────│  { refreshing: true }
│   ...poll...        │
│   GET /status       │
│───────────────────>│
│<───────────────────│  { refreshing: false, cache_available: true }
```

### Empty Cache (valid)

```
UI                 Backend
│   GET /status      │
│───────────────────>│
│<───────────────────│  { cache_available: false }
│
│   GET /channels     │
│───────────────────>│
│<───────────────────│  { channels: [], total: 0 }
│
│   GET /stats        │
│───────────────────>│
│<───────────────────│  { total: 0, tv: 0, ... }
```

### Refresh Guardrails

```
UI                 Backend
│   POST /refresh     │
│───────────────────>│
│<───────────────────│  409 not logged in
│
│   POST /refresh     │
│───────────────────>│
│<───────────────────│  409 already refreshing
```
