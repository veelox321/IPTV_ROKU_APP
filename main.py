# load credentials from credentials.json
import json

def load_credentials():
    with open('credentials.json', 'r') as f:
        credentials = json.load(f)
    return credentials

credentials = load_credentials()

username = credentials.get('iptv', {}).get('username')
password = credentials.get('iptv', {}).get('password')
print(username, password)

hosts = credentials.get('iptv', {}).get('hosts', [])
print("Available hosts:", hosts)

m3u_urls = []

for host in hosts:
    m3u_url = f"{host}/playlist/{username}/{password}/m3u"
    m3u_urls.append(m3u_url)

print("Generated M3U URLs:", m3u_urls)

