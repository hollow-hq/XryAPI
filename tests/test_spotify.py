import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.services.spotify_service import SpotifyService


class TestSpotifyService:
    def test_init_without_creds(self, monkeypatch):
        monkeypatch.delenv("SPOTIFY_CLIENT_ID", raising=False)
        monkeypatch.delenv("SPOTIFY_CLIENT_SECRET", raising=False)
        with pytest.raises(ValueError):
            SpotifyService()

    def test_extract_id_from_url_track(self):
        service = SpotifyService.__new__(SpotifyService)
        track_id = service._extract_id("https://open.spotify.com/track/123abc", "track")
        assert track_id == "123abc"

    def test_extract_id_from_url_playlist(self):
        service = SpotifyService.__new__(SpotifyService)
        playlist_id = service._extract_id("https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M", "playlist")
        assert playlist_id == "37i9dQZF1DXcBWIGoYBM5M"

    def test_extract_id_from_url_album(self):
        service = SpotifyService.__new__(SpotifyService)
        album_id = service._extract_id("https://open.spotify.com/album/41MnTivkwTO3UUJ8DrqEJJ", "album")
        assert album_id == "41MnTivkwTO3UUJ8DrqEJJ"

    def test_extract_id_plain_id(self):
        service = SpotifyService.__new__(SpotifyService)
        track_id = service._extract_id("4cOdK2wGLETKBW3PvgPWqT", "track")
        assert track_id == "4cOdK2wGLETKBW3PvgPWqT"

    def test_format_track(self):
        service = SpotifyService.__new__(SpotifyService)
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
        assert result['duration_ms'] == 180000

    def test_normalize_search_results(self):
        service = SpotifyService.__new__(SpotifyService)
        data = {
            'tracks': {
                'items': [
                    {
                        'id': 't1',
                        'name': 'Song',
                        'duration_ms': 200000,
                        'explicit': True,
                        'popularity': 80,
                        'artists': [{'id': 'a1', 'name': 'Artist'}],
                        'album': {'id': 'al1', 'name': 'Album', 'images': []},
                        'external_urls': {'spotify': 'http://t'}
                    }
                ]
            }
        }
        result = service._normalize_search_results(data, "Song")
        assert len(result['tracks']) == 1
        assert result['tracks'][0]['name'] == 'Song'
