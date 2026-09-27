import json
from api.services.youtube_service import YouTubeService, PLAYER_CLIENTS

s = YouTubeService()
for c in PLAYER_CLIENTS:
    try:
        d = s._make_request('player', {'videoId': 'zPOMR2tenHE'}, c)
        sd = d.get('streamingData', {}) or {}
        all_f = sd.get('formats', []) + sd.get('adaptiveFormats', [])
        direct = sum(1 for f in all_f if f.get('url'))
        print(c.name, c.version, 'total', len(all_f), 'url direta', direct)
    except Exception as e:
        print(c.name, c.version, 'EXC', str(e)[:60])
