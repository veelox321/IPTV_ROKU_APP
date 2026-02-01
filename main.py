# IPTV Channel List Caching System
import json
import os
from datetime import datetime, timedelta
import urllib.request
import urllib.error

# Constants
CACHE_FILE = 'channels_cache.json'
CACHE_EXPIRY_HOURS = 24

def load_credentials():
    """Load credentials from credentials.json file."""
    try:
        with open('credentials.json', 'r') as f:
            credentials = json.load(f)
        return credentials
    except FileNotFoundError:
        print("Error: credentials.json not found. Please create one based on credentials_example.json")
        return None
    except json.JSONDecodeError:
        print("Error: Invalid JSON in credentials.json")
        return None

def build_m3u_url(host, username, password):
    """Build M3U playlist URL."""
    return f"{host}/playlist/{username}/{password}/m3u"

def build_xtream_urls(host, username, password):
    """Build Xtream API URLs."""
    base_url = f"{host}/player_api.php?username={username}&password={password}"
    return {
        'live': f"{base_url}&action=get_live_streams",
        'vod': f"{base_url}&action=get_vod_streams",
        'series': f"{base_url}&action=get_series"
    }

def fetch_m3u_content(url):
    """Fetch content from M3U URL."""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read().decode('utf-8')
            return content
    except urllib.error.URLError as e:
        print(f"Error fetching M3U from {url}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching M3U: {e}")
        return None

def fetch_xtream_content(url):
    """Fetch content from Xtream API URL."""
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read().decode('utf-8')
            return json.loads(content)
    except urllib.error.URLError as e:
        print(f"Error fetching from Xtream API {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing Xtream API response: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching from Xtream API: {e}")
        return None

def parse_m3u_content(content):
    """Parse M3U content into channel list."""
    channels = []
    lines = content.split('\n')
    current_channel = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('#EXTINF:'):
            # Parse channel info
            parts = line.split(',', 1)
            if len(parts) == 2:
                current_channel['name'] = parts[1].strip()
                # Extract additional info from EXTINF line if needed
                current_channel['info'] = parts[0].replace('#EXTINF:', '').strip()
        elif line and not line.startswith('#') and current_channel:
            # This is the channel URL
            current_channel['url'] = line
            channels.append(current_channel)
            current_channel = {}
    
    return channels

def is_cache_valid():
    """Check if cache file exists and is less than 24 hours old."""
    if not os.path.exists(CACHE_FILE):
        return False
    
    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
        
        # Check if cache has timestamp
        if 'timestamp' not in cache_data:
            return False
        
        # Parse timestamp and check if it's within expiry time
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        now = datetime.now()
        age = now - cache_time
        
        if age < timedelta(hours=CACHE_EXPIRY_HOURS):
            print(f"Cache is valid (age: {age.total_seconds() / 3600:.2f} hours)")
            return True
        else:
            print(f"Cache expired (age: {age.total_seconds() / 3600:.2f} hours)")
            return False
    except Exception as e:
        print(f"Error checking cache validity: {e}")
        return False

def load_from_cache():
    """Load channel list from cache file."""
    try:
        with open(CACHE_FILE, 'r') as f:
            cache_data = json.load(f)
        return cache_data.get('channels', [])
    except Exception as e:
        print(f"Error loading from cache: {e}")
        return []

def save_to_cache(channels):
    """Save channel list to cache file with timestamp."""
    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'channels': channels
    }
    
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=2)
        print(f"Successfully cached {len(channels)} channels")
        return True
    except Exception as e:
        print(f"Error saving to cache: {e}")
        return False

def fetch_and_cache_channels(credentials):
    """Fetch channels from API and cache them."""
    username = credentials.get('iptv', {}).get('username')
    password = credentials.get('iptv', {}).get('password')
    hosts = credentials.get('iptv', {}).get('hosts', [])
    api_type = credentials.get('iptv', {}).get('type', 'm3u')  # Default to m3u
    
    if not username or not password or not hosts:
        print("Error: Missing credentials (username, password, or hosts)")
        return []
    
    all_channels = []
    
    for host in hosts:
        print(f"\nProcessing host: {host}")
        
        if api_type.lower() == 'xtream':
            # Fetch from Xtream API
            urls = build_xtream_urls(host, username, password)
            
            # Fetch live streams
            print("Fetching live streams...")
            live_streams = fetch_xtream_content(urls['live'])
            if live_streams:
                for stream in live_streams:
                    all_channels.append({
                        'name': stream.get('name', 'Unknown'),
                        'stream_id': stream.get('stream_id'),
                        'type': 'live',
                        'category_id': stream.get('category_id'),
                        'host': host
                    })
            
            # Fetch VOD streams
            print("Fetching VOD streams...")
            vod_streams = fetch_xtream_content(urls['vod'])
            if vod_streams:
                for stream in vod_streams:
                    all_channels.append({
                        'name': stream.get('name', 'Unknown'),
                        'stream_id': stream.get('stream_id'),
                        'type': 'vod',
                        'category_id': stream.get('category_id'),
                        'host': host
                    })
        else:
            # Fetch from M3U
            m3u_url = build_m3u_url(host, username, password)
            print(f"Fetching M3U from: {m3u_url}")
            
            content = fetch_m3u_content(m3u_url)
            if content:
                channels = parse_m3u_content(content)
                for channel in channels:
                    channel['host'] = host
                all_channels.extend(channels)
    
    # Apply filters if specified
    filters = credentials.get('filters', {})
    keywords = filters.get('keywords', [])
    
    if keywords:
        print(f"\nApplying filters: {keywords}")
        filtered_channels = []
        for channel in all_channels:
            channel_name = channel.get('name', '').lower()
            if any(keyword.lower() in channel_name for keyword in keywords):
                filtered_channels.append(channel)
        
        print(f"Filtered: {len(all_channels)} -> {len(filtered_channels)} channels")
        all_channels = filtered_channels
    
    # Save to cache
    save_to_cache(all_channels)
    
    return all_channels

def main():
    """Main function to load credentials and manage channel list caching."""
    print("=" * 60)
    print("IPTV Channel List Manager")
    print("=" * 60)
    
    # Load credentials
    print("\nLoading credentials...")
    credentials = load_credentials()
    if not credentials:
        return
    
    print("Credentials loaded successfully")
    
    # Check if we can use cached data
    if is_cache_valid():
        print("\nUsing cached channel list...")
        channels = load_from_cache()
        print(f"Loaded {len(channels)} channels from cache")
    else:
        print("\nFetching fresh channel list...")
        channels = fetch_and_cache_channels(credentials)
        print(f"Fetched and cached {len(channels)} channels")
    
    # Display summary
    print("\n" + "=" * 60)
    print(f"Total channels available: {len(channels)}")
    
    if channels:
        print("\nFirst 5 channels:")
        for i, channel in enumerate(channels[:5], 1):
            print(f"  {i}. {channel.get('name', 'Unknown')}")
    
    print("=" * 60)
    
    return channels

if __name__ == "__main__":
    main()

