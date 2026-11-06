import json
from urllib.request import urlopen

with urlopen('http://127.0.0.1:8080/health', timeout=4) as response:
    result = json.load(response)
if result.get('status') != 'ok':
    raise SystemExit('Backend health check failed')
