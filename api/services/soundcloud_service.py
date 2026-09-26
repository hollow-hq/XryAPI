import io
from typing import Dict, Any, Optional, List, Union
from sclib import SoundcloudAPI, Track, Playlist
from sclib.asyncio import SoundcloudAPI as AsyncSoundcloudAPI
import httpx
import requests
from ..utils.litterbox_uploader import LitterboxUploader

class SoundCloudService:
    def __init__(self):
        self.api = SoundcloudAPI()
        self.async_api = AsyncSoundcloudAPI()
        self.litterbox = LitterboxUploader()
        self.session = httpx.Client(timeout=60.0)

    def search(self, query: str) -> Dict[str, Any]:
        search_url = "https://api-v2.soundcloud.com/search"
        params = {"q": query, "limit": 20, "client_id": self.api.client_id}
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        return self._format_search_response(data)

    def get_track(self, url: str) -> Dict[str, Any]:
        track = self.api.resolve(url)
        if not isinstance(track, Track):
            raise ValueError("URL does not resolve to a track")
        return self._format_track(track)

    def get_user(self, url: str) -> Dict[str, Any]:
        user_id = url.split("/")[-1].split("?")[0]
        api_url = f"https://api-v2.soundcloud.com/users/{user_id}"
        params = {"client_id": self.api.client_id}
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        return self._format_user(data)

    def get_playlist(self, url: str) -> Dict[str, Any]:
        playlist = self.api.resolve(url)
        if not isinstance(playlist, Playlist):
            raise ValueError("URL does not resolve to a playlist")
        return self._format_playlist(playlist)

    def get_user_tracks(self, url: str, limit: int = 50) -> Dict[str, Any]:
        user_id = url.split("/")[-1].split("?")[0]
        api_url = f"https://api-v2.soundcloud.com/users/{user_id}/tracks"
        params = {"client_id": self.api.client_id, "limit": limit}
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        data = response.json()
        tracks = []
        for item in data.get("collection", [])[:limit]:
            tracks.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "artist": item.get("user", {}).get("username"),
                "duration": item.get("duration"),
                "artwork_url": item.get("artwork_url")
            })
        user_info = self.get_user(url)
        return {"user": self._format_user_basic_from_dict(user_info), "track_count": len(tracks), "tracks": tracks}

    def get_related(self, url: str, count: int = 10) -> Dict[str, Any]:
        track = self.api.resolve(url)
        if not isinstance(track, Track):
            raise ValueError("URL does not resolve to a track")
        related_tracks = []
        search_results = self.search(track.title)
        items = search_results.get("collection", [])
        for item in items[:count]:
            if item.get("kind") == "track":
                related_tracks.append({
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "artist": item.get("user", {}).get("username"),
                    "duration": item.get("duration"),
                    "artwork_url": item.get("artwork_url"),
                    "permalink": item.get("permalink")
                })
        return {"track_id": track.id, "related_tracks": related_tracks[:count]}

    def download_audio(self, url: str, upload_to_litterbox: bool = False) -> Union[bytes, Dict[str, Any]]:
        track = self.api.resolve(url)
        if not isinstance(track, Track):
            raise ValueError("URL does not resolve to a track")
        if not track.downloadable:
            raise ValueError("Track is not downloadable")
        mp3_data = track.download()
        if upload_to_litterbox:
            return self.litterbox.upload(mp3_data, f"{track.artist} - {track.title}.mp3")
        return mp3_data

    def _format_track(self, track: Track) -> Dict[str, Any]:
        return {
            "id": track.id,
            "title": track.title,
            "artist": track.artist,
            "duration": track.duration,
            "duration_ms": track.duration * 1000,
            "genre": track.genre,
            "tags": track.tags,
            "description": track.description,
            "artwork_url": track.artwork_url,
            "stream_url": track.stream_url,
            "downloadable": track.downloadable,
            "play_count": track.playback_count,
            "like_count": track.likes_count,
            "repost_count": track.reposts_count,
            "comment_count": track.comment_count,
            "permalink": track.permalink_url,
            "user": self._format_user_basic(track.user)
        }

    def _format_track_basic(self, track) -> Dict[str, Any]:
        return {"id": track.id, "title": track.title, "artist": track.artist, "duration": track.duration, "artwork_url": track.artwork_url}

    def _format_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": user.get("id"),
            "username": user.get("username"),
            "full_name": user.get("full_name"),
            "bio": user.get("description"),
            "avatar_url": user.get("avatar_url"),
            "follower_count": user.get("followers_count"),
            "following_count": user.get("followings_count"),
            "track_count": user.get("tracks_count"),
            "playlist_count": user.get("playlists_count"),
            "likes_count": user.get("likes_count"),
            "verified": user.get("verified"),
            "plan": user.get("plan"),
            "website": user.get("website")
        }

    def _format_user_basic(self, user) -> Dict[str, Any]:
        return {"id": user.id, "username": user.username, "full_name": user.full_name, "avatar_url": user.avatar_url}

    def _format_user_basic_from_dict(self, user: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": user.get("id"), "username": user.get("username"), "full_name": user.get("full_name"), "avatar_url": user.get("avatar_url")}

    def _format_playlist(self, playlist: Playlist) -> Dict[str, Any]:
        tracks = []
        for track in playlist.tracks[:20]:
            tracks.append(self._format_track_basic(track))
        return {
            "id": playlist.id,
            "title": playlist.title,
            "description": playlist.description,
            "track_count": len(playlist.tracks),
            "duration": sum(t.duration for t in playlist.tracks),
            "artwork_url": playlist.artwork_url,
            "created": playlist.created_at,
            "user": self._format_user_basic(playlist.user),
            "tracks": tracks
        }

    def _format_search_response(self, data: Dict) -> Dict[str, Any]:
        collection = data.get("collection", [])
        formatted = []
        for item in collection:
            if item.get("kind") == "track":
                formatted.append({
                    "type": "track",
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "artist": item.get("user", {}).get("username"),
                    "duration": item.get("duration"),
                    "artwork_url": item.get("artwork_url"),
                    "stream_url": item.get("stream_url"),
                    "permalink": item.get("permalink_url")
                })
            elif item.get("kind") == "playlist":
                formatted.append({
                    "type": "playlist",
                    "id": item.get("id"),
                    "title": item.get("title"),
                    "track_count": item.get("track_count"),
                    "artwork_url": item.get("artwork_url"),
                    "permalink": item.get("permalink_url")
                })
            elif item.get("kind") == "user":
                formatted.append({
                    "type": "user",
                    "id": item.get("id"),
                    "username": item.get("username"),
                    "full_name": item.get("full_name"),
                    "avatar_url": item.get("avatar_url"),
                    "track_count": item.get("track_count")
                })
        return {"query": data.get("query", ""), "total_results": data.get("total_results", 0), "collection": formatted}
