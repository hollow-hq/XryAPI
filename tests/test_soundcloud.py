import pytest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.services.youtube_service import YouTubeService
from api.services.soundcloud_service import SoundCloudService
from api.services.spotify_service import SpotifyService
from api.utils.cache_manager import CacheManager
from api.utils.litterbox_uploader import LitterboxUploader
from api.utils.response_formatter import api_response, error_response

class TestCacheManager:
    def setup_method(self):
        self.cache = CacheManager(maxsize=10, ttl=60)

    def test_get_cache_key(self):
        key = self.cache.get_cache_key("func", "arg1", key="val")
        assert isinstance(key, str)
        assert len(key) == 32

    def test_cached_decorator(self):
        call_count = [0]
        @self.cache.cached(ttl=60)
        def func(x):
            call_count[0] += 1
            return x * 2
        assert func(5) == 10
        assert func(5) == 10
        assert call_count[0] == 1
        assert func(6) == 12
        assert call_count[0] == 2

class TestLitterboxUploader:
    def setup_method(self):
        self.uploader = LitterboxUploader()

    def test_init(self):
        assert self.uploader.upload_url == "https://litterbox.catbox.moe/upload"

class TestResponseFormatter:
    def test_api_response(self):
        from flask import Flask
        app = Flask(__name__)
        with app.app_context():
            data = {"key": "value"}
            response, status = api_response(data, 200)
            assert status == 200
            assert response.json["success"] is True

    def test_error_response(self):
        from flask import Flask
        app = Flask(__name__)
        with app.app_context():
            response, status = error_response("test error", 400)
            assert status == 400
            assert response.json["success"] is False
