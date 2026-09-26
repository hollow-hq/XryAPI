import os
import re
import io
import tempfile
import shutil
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from ..utils.litterbox_uploader import LitterboxUploader
from ..utils.cache_manager import CacheManager


class SpotifyService:
    """Spotify service using SpotiFLAC for audio acquisition."""

    def __init__(self):
        self.litterbox = LitterboxUploader()
        self.cache = CacheManager()
        self.temp_dir = tempfile.mkdtemp(prefix="HAPI2_spotify_")
        self.default_services = ["tidal", "qobuz", "deezer", "amazon"]
        self.default_quality = "LOSSLESS"
        self._spotiflac = None

    def _get_spotiflac(self):
        if self._spotiflac is None:
            try:
                from SpotiFLAC import SpotiFLAC
                self._spotiflac = SpotiFLAC
            except Exception as e:
                raise RuntimeError(f"SpotiFLAC is not available: {e}")
        return self._spotiflac

    def search(self, query: str, limit: int = 20) -> Dict[str, Any]:
        import requests
        search_url = "https://api.spotify.com/v1/search"
        try:
            params = {"q": query, "type": "track,artist,album,playlist", "limit": limit}
            response = requests.get(search_url, params=params)
            if response.status_code == 200:
                return self._normalize_search_results(response.json(), query)
        except Exception:
            pass
        return {"query": query, "tracks": [], "artists": [], "albums": [], "playlists": []}

    def get_track(self, track_identifier: str) -> Dict[str, Any]:
        track_id = self._extract_id(track_identifier, "track")
        url = f"https://open.spotify.com/track/{track_id}"
        try:
            return self._get_track_metadata_via_webapi(track_id)
        except Exception:
            return {
                "id": track_id,
                "name": "Unknown",
                "artists": [],
                "album": {},
                "duration_ms": 0,
                "explicit": False,
                "preview_url": None,
                "external_urls": {"spotify": url}
            }

    def get_album(self, album_identifier: str) -> Dict[str, Any]:
        album_id = self._extract_id(album_identifier, "album")
        return self._get_album_metadata_via_webapi(album_id)

    def _get_track_metadata_via_webapi(self, track_id: str) -> Dict[str, Any]:
        import requests
        url = f"https://api.spotify.com/v1/tracks/{track_id}"
        response = requests.get(url)
        response.raise_for_status()
        return self._format_track(response.json())

    def _get_album_metadata_via_webapi(self, album_id: str) -> Dict[str, Any]:
        import requests
        url = f"https://api.spotify.com/v1/albums/{album_id}"
        response = requests.get(url)
        response.raise_for_status()
        return self._format_album(response.json())

    def download_audio(self, url: str, upload_to_litterbox: bool = False) -> Union[bytes, Dict[str, Any]]:
        track_id = self._extract_id(url, "track")
        spotify_url = f"https://open.spotify.com/track/{track_id}"
        output_dir = os.path.join(self.temp_dir, track_id)
        os.makedirs(output_dir, exist_ok=True)
        try:
            spoti = self._get_spotiflac()(
                url=spotify_url,
                output_dir=output_dir,
                services=self.default_services,
                quality=self.default_quality,
                timeout_s=300,
                track_max_retries=3,
                log_level=30
            )
            downloaded_files = list(Path(output_dir).rglob("*.flac"))
            downloaded_files.extend(Path(output_dir).rglob("*.m4a"))
            downloaded_files.extend(Path(output_dir).rglob("*.mp3"))
            if not downloaded_files:
                raise RuntimeError("SpotiFLAC did not produce any audio files")
            audio_path = downloaded_files[0]
            with open(audio_path, 'rb') as f:
                audio_data = f.read()
            shutil.rmtree(output_dir, ignore_errors=True)
            if upload_to_litterbox:
                return self.litterbox.upload(audio_data, f"track_{track_id}.flac")
            return audio_data
        except Exception as e:
            shutil.rmtree(output_dir, ignore_errors=True)
            raise RuntimeError(f"SpotiFLAC download failed: {str(e)}")

    def download_playlist(self, url: str, upload_to_litterbox: bool = False) -> Dict[str, Any]:
        playlist_id = self._extract_id(url, "playlist")
        spotify_url = f"https://open.spotify.com/playlist/{playlist_id}"
        output_dir = os.path.join(self.temp_dir, f"playlist_{playlist_id}")
        os.makedirs(output_dir, exist_ok=True)
        try:
            spoti = self._get_spotiflac()(
                url=spotify_url,
                output_dir=output_dir,
                services=self.default_services,
                quality=self.default_quality,
                timeout_s=300,
                track_max_retries=3,
                use_album_subfolders=True,
                use_track_numbers=True,
                log_level=30
            )
            downloaded_files = list(Path(output_dir).rglob("*.flac"))
            downloaded_files.extend(Path(output_dir).rglob("*.m4a"))
            results = []
            for f in downloaded_files[:50]:
                with open(f, 'rb') as audio_f:
                    data = audio_f.read()
                if upload_to_litterbox:
                    results.append(self.litterbox.upload(data, f.name))
                else:
                    results.append({"filename": f.name, "size": len(data)})
            shutil.rmtree(output_dir, ignore_errors=True)
            return {
                "playlist_id": playlist_id,
                "total_tracks": len(downloaded_files),
                "downloaded": len(results),
                "results": results
            }
        except Exception as e:
            shutil.rmtree(output_dir, ignore_errors=True)
            raise RuntimeError(f"Playlist download failed: {str(e)}")

    def download_album(self, url: str, upload_to_litterbox: bool = False) -> Dict[str, Any]:
        album_id = self._extract_id(url, "album")
        spotify_url = f"https://open.spotify.com/album/{album_id}"
        output_dir = os.path.join(self.temp_dir, f"album_{album_id}")
        os.makedirs(output_dir, exist_ok=True)
        try:
            spoti = self._get_spotiflac()(
                url=spotify_url,
                output_dir=output_dir,
                services=self.default_services,
                quality=self.default_quality,
                timeout_s=300,
                track_max_retries=3,
                use_track_numbers=True,
                log_level=30
            )
            downloaded_files = list(Path(output_dir).rglob("*.flac"))
            downloaded_files.extend(Path(output_dir).rglob("*.m4a"))
            results = []
            for f in downloaded_files:
                with open(f, 'rb') as audio_f:
                    data = audio_f.read()
                if upload_to_litterbox:
                    results.append(self.litterbox.upload(data, f.name))
                else:
                    results.append({"filename": f.name, "size": len(data)})
            shutil.rmtree(output_dir, ignore_errors=True)
            return {
                "album_id": album_id,
                "total_tracks": len(downloaded_files),
                "results": results
            }
        except Exception as e:
            shutil.rmtree(output_dir, ignore_errors=True)
            raise RuntimeError(f"Album download failed: {str(e)}")

    def _extract_id(self, identifier: str, type_str: str) -> str:
        if not identifier.startswith("http") and not identifier.startswith("spotify:"):
            return identifier
        patterns = {
            "track": r'track[/:]([a-zA-Z0-9]+)',
            "album": r'album[/:]([a-zA-Z0-9]+)',
            "playlist": r'playlist[/:]([a-zA-Z0-9]+)',
            "artist": r'artist[/:]([a-zA-Z0-9]+)'
        }
        pattern = patterns.get(type_str, r'([a-zA-Z0-9]{22})')
        match = re.search(pattern, identifier)
        if not match:
            match = re.search(r'([a-zA-Z0-9]{22})', identifier)
        if match:
            return match.group(1)
        raise ValueError(f"Could not extract {type_str} ID from: {identifier}")

    def _format_track(self, data: Dict) -> Dict[str, Any]:
        return {
            "id": data.get('id'),
            "name": data.get('name'),
            "duration_ms": data.get('duration_ms'),
            "explicit": data.get('explicit', False),
            "popularity": data.get('popularity', 0),
            "preview_url": data.get('preview_url'),
            "artists": [
                {"id": a['id'], "name": a['name']}
                for a in data.get('artists', [])
            ],
            "album": {
                "id": data.get('album', {}).get('id'),
                "name": data.get('album', {}).get('name'),
                "images": [img['url'] for img in data.get('album', {}).get('images', [])]
            },
            "external_urls": data.get('external_urls', {})
        }

    def _format_album(self, data: Dict) -> Dict[str, Any]:
        return {
            "id": data.get('id'),
            "name": data.get('name'),
            "release_date": data.get('release_date'),
            "total_tracks": data.get('total_tracks'),
            "artists": [
                {"id": a['id'], "name": a['name']}
                for a in data.get('artists', [])
            ],
            "images": [img['url'] for img in data.get('images', [])],
            "external_urls": data.get('external_urls', {})
        }

    def _normalize_search_results(self, data: Dict, query: str) -> Dict:
        result = {"query": query, "tracks": [], "artists": [], "albums": [], "playlists": []}
        for item in data.get('tracks', {}).get('items', []):
            result["tracks"].append(self._format_track(item))
        return result

    def __del__(self):
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
