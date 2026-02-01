# IPTV_ROKU_APP

IPTV Channel List Manager with intelligent caching system.

## Features

- **Credential Management**: Load IPTV credentials from `credentials.json`
- **Smart Caching**: Channel lists are cached locally and automatically refreshed after 24 hours
- **Dual API Support**: Works with both M3U playlists and Xtream API
- **Channel Filtering**: Filter channels by keywords for faster searching
- **Performance**: Loads channel list once and reuses cached data for faster subsequent access

## Setup

1. Copy `credentials_example.json` to `credentials.json`:
   ```bash
   cp credentials_example.json credentials.json
   ```

2. Edit `credentials.json` with your IPTV provider details:
   ```json
   {
       "iptv": {
           "username": "your_username",
           "password": "your_password",
           "type": "m3u",
           "hosts": [
               "http://your-iptv-server.com"
           ]
       },
       "filters": {
           "keywords": [
               "Sport",
               "News"
           ]
       }
   }
   ```

   - `type`: Set to `"m3u"` for M3U playlists or `"xtream"` for Xtream API
   - `hosts`: List of IPTV server URLs
   - `keywords`: Optional list of keywords to filter channels (case-insensitive)

## Usage

Run the main script:
```bash
python3 main.py
```

### First Run
On the first run (or when cache is older than 24 hours), the script will:
1. Load credentials from `credentials.json`
2. Fetch channel list from IPTV server(s)
3. Apply filters if specified
4. Save channels to `channels_cache.json` with timestamp
5. Display summary of available channels

### Subsequent Runs
When cache is fresh (less than 24 hours old):
1. Load credentials from `credentials.json`
2. Load channel list from `channels_cache.json` (fast!)
3. Display summary of available channels

## Cache Management

- Cache file: `channels_cache.json`
- Cache duration: 24 hours
- Cache structure:
  ```json
  {
    "timestamp": "2026-02-01T15:30:00.000000",
    "channels": [...]
  }
  ```

To force a refresh, simply delete the cache file:
```bash
rm channels_cache.json
```

## API Types

### M3U Playlist
For M3U-based IPTV services, set `"type": "m3u"` in credentials.json.
The script will construct URLs like:
```
http://server/playlist/username/password/m3u
```

### Xtream API
For Xtream API-based services, set `"type": "xtream"` in credentials.json.
The script will fetch from multiple endpoints:
- Live streams
- VOD streams
- Series

## Testing

Run the test suite to verify caching functionality:
```bash
python3 test_caching.py
```

## Files

- `main.py` - Main application with caching logic
- `credentials.json` - Your IPTV credentials (not tracked in git)
- `credentials_example.json` - Example credentials file
- `channels_cache.json` - Cached channel list (not tracked in git)
- `test_caching.py` - Test suite for caching functionality