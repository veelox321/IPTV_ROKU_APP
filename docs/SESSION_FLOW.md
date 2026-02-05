# Session Flow

## Overlay behavior
- The IPTV UI screens render as-is.
- A `LoginOverlay` is mounted on top of the existing pages when the session state is `NOT_LOGGED_IN`.
- Once credentials are accepted, the overlay disappears and the existing UI remains unchanged.

## Why channels can be empty
- The backend serves channels from a cache.
- Before credentials are provided (or after a refresh that yields no data), `/channels` returns an empty array.
- The UI can safely render with empty lists until a refresh repopulates the cache.

## Refresh trigger
- After login, the session flow triggers `/refresh` to populate the channel cache.
- The session then polls `/status` until the backend reports `refreshing=false`.
- Existing screens continue to fetch stats/channels as usual once the cache is ready.
