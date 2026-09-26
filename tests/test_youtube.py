import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.services.youtube_service import YouTubeService
from api.services.soundcloud_service import SoundCloudService
from api.services.spotify_service import SpotifyService

class TestYouTubeService:
    def setup_method(self):
        self.service = YouTubeService()

    def test_search(self):
        result = self.service.search("test", max_results=5)
        assert "items" in result
        assert "query" in result
        assert "result_count" in result

    def test_browse(self):
        result = self.service.browse("FEtrending")
        assert "contents" in result

    def test_trending(self):
        result = self.service.trending()
        assert "contents" in result

    def test_homepage(self):
        result = self.service.homepage()
        assert "contents" in result

    def test_player(self):
        result = self.service.player("dQw4w9WgXcQ")
        assert "video_id" in result
        assert "formats" in result

    def test_parse_search_item_video(self):
        item = {"videoRenderer": {"videoId": "123", "title": {"runs": [{"text": "Test"}]}, "ownerText": {"runs": [{"text": "Channel", "navigationEndpoint": {"browseEndpoint": {"browseId": "UC123"}}}]}, "viewCount": {"simpleText": "1K views"}, "publishedTimeText": {"simpleText": "1 day ago"}, "thumbnail": {"thumbnails": [{"url": "http://img"}]}, "lengthText": {"simpleText": "3:00"}}}
        result = self.service._parse_search_item(item)
        assert result["type"] == "video"
        assert result["id"] == "123"

class TestSoundCloudService:
    def setup_method(self):
        self.service = SoundCloudService()

    def test_search(self):
        result = self.service.search("test")
        assert "collection" in result

    def test_format_track(self):
        from sclib import Track
        track = type('obj', (object,), {
            'id': 1,
            'title': 'Test',
            'artist': 'Artist',
            'duration': 180,
            'genre': 'Electronic',
            'tags': ['tag'],
            'description': 'desc',
            'artwork_url': 'http://img',
            'stream_url': 'http://stream',
            'downloadable': True,
            'playback_count': 1000,
            'likes_count': 100,
            'reposts_count': 10,
            'comment_count': 5,
            'permalink_url': 'http://permalink',
            'user': type('obj', (object,), {'id': 1, 'username': 'user', 'full_name': 'User', 'avatar_url': 'http://avatar'})()
        })()
        result = self.service._format_track(track)
        assert result['id'] == 1
        assert result['title'] == 'Test'

class TestSpotifyService:
    def test_init_without_creds(self):
        with pytest.raises(ValueError):
            SpotifyService()

    def test_format_track(self):
        service = SpotifyService.__new__(SpotifyService)
        service.sp = None
        track = {
            'id': '1',
            'name': 'Test',
            'duration_ms': 180000,
            'explicit': False,
            'popularity': 50,
            'artists': [{'id': 'a1', 'name': 'Artist', 'external_urls': {'spotify': 'http://s'}}],
            'album': {'id': 'al1', 'name': 'Album', 'images': [], 'external_urls': {'spotify': 'http://a'}},
            'preview_url': None,
            'track_number': 1,
            'disc_number': 1,
            'external_urls': {'spotify': 'http://t'}
        }
        result = service._format_track(track)
        assert result['id'] == '1'
        assert result['name'] == 'Test'
