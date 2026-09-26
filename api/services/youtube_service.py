import httpx
import cachetools
from typing import Dict, Any, List, Optional
from cachetools import TTLCache

class YouTubeService:
    def __init__(self):
        self.base_url = "https://www.youtube.com/youtubei/v1"
        self.api_key = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
        self.client_version = "2.20241118.01.00"
        self.cache = TTLCache(maxsize=100, ttl=300)
        self.session = httpx.Client(timeout=30.0)

    def _make_request(self, endpoint: str, data: Dict) -> Dict:
        headers = {
            "Content-Type": "application/json",
            "X-YouTube-Client-Name": "1",
            "X-YouTube-Client-Version": self.client_version,
            "Origin": "https://www.youtube.com",
            "User-Agent": "Mozilla/5.0 (compatible; HAPI2/1.0)"
        }
        payload = {
            "context": {
                "client": {
                    "hl": "en",
                    "gl": "US",
                    "clientName": "WEB",
                    "clientVersion": self.client_version
                }
            },
            **data
        }
        response = self.session.post(f"{self.base_url}/{endpoint}", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def search(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        cache_key = f"search_{query}_{max_results}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        data = {"query": query, "maxResults": max_results}
        result = self._make_request("search", data)
        formatted = self._format_search_response(result, max_results)
        self.cache[cache_key] = formatted
        return formatted

    def browse(self, browse_id: str) -> Dict[str, Any]:
        cache_key = f"browse_{browse_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        data = {"browseId": browse_id}
        result = self._make_request("browse", data)
        self.cache[cache_key] = result
        return result

    def trending(self) -> Dict[str, Any]:
        cache_key = "trending_videos"
        if cache_key in self.cache:
            return self.cache[cache_key]
        data = {"browseId": "FEtrending", "params": "CAASAhAB"}
        result = self._make_request("browse", data)
        self.cache[cache_key] = result
        return result

    def homepage(self) -> Dict[str, Any]:
        cache_key = "homepage_feed"
        if cache_key in self.cache:
            return self.cache[cache_key]
        data = {"browseId": "FEwhat_to_watch"}
        result = self._make_request("browse", data)
        self.cache[cache_key] = result
        return result

    def video_metadata(self, video_id: str) -> Dict[str, Any]:
        cache_key = f"video_{video_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        data = {"videoId": video_id}
        result = self._make_request("player", data)
        self.cache[cache_key] = result
        return result

    def player(self, video_id: str) -> Dict[str, Any]:
        cache_key = f"player_{video_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        data = {"videoId": video_id}
        result = self._make_request("player", data)
        formats = []
        streaming_data = result.get("streamingData", {})
        for fmt in streaming_data.get("formats", []):
            formats.append({
                "itag": fmt.get("itag"),
                "mime_type": fmt.get("mimeType"),
                "quality": fmt.get("quality"),
                "url": fmt.get("url"),
                "bitrate": fmt.get("bitrate"),
                "width": fmt.get("width"),
                "height": fmt.get("height")
            })
        adaptive_formats = []
        for fmt in streaming_data.get("adaptiveFormats", []):
            adaptive_formats.append({
                "itag": fmt.get("itag"),
                "mime_type": fmt.get("mimeType"),
                "quality": fmt.get("quality"),
                "url": fmt.get("url"),
                "bitrate": fmt.get("bitrate"),
                "width": fmt.get("width"),
                "height": fmt.get("height")
            })
        self.cache[cache_key] = {
            "video_id": video_id,
            "formats": formats,
            "adaptive_formats": adaptive_formats,
            "expires_in": streaming_data.get("expiresInSeconds")
        }
        return self.cache[cache_key]

    def next_videos(self, video_id: str) -> Dict[str, Any]:
        cache_key = f"next_{video_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        data = {"videoId": video_id}
        result = self._make_request("next", data)
        self.cache[cache_key] = result
        return result

    def captions(self, video_id: str) -> Dict[str, Any]:
        cache_key = f"captions_{video_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        data = {"videoId": video_id}
        result = self._make_request("player", data)
        caption_tracks = []
        captions_data = result.get("captions", {}).get("playerCaptionsTracklistRenderer", {})
        for track in captions_data.get("captionTracks", []):
            caption_tracks.append({
                "language": track.get("languageCode"),
                "name": track.get("name", {}).get("simpleText", ""),
                "url": track.get("baseUrl"),
                "auto_generated": track.get("isAutoGenerated", False)
            })
        self.cache[cache_key] = {
            "video_id": video_id,
            "caption_tracks": caption_tracks,
            "default_language": captions_data.get("defaultLanguage", "en")
        }
        return self.cache[cache_key]

    def channel(self, channel_id: str) -> Dict[str, Any]:
        cache_key = f"channel_{channel_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        data = {"browseId": channel_id}
        result = self._make_request("browse", data)
        self.cache[cache_key] = result
        return result

    def channel_videos(self, channel_id: str, max_results: int = 50) -> Dict[str, Any]:
        cache_key = f"channel_videos_{channel_id}_{max_results}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        data = {"browseId": channel_id, "params": "EgIQAQ%3D%3D", "maxResults": max_results}
        result = self._make_request("browse", data)
        self.cache[cache_key] = result
        return result

    def playlist(self, playlist_id: str) -> Dict[str, Any]:
        cache_key = f"playlist_{playlist_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        data = {"browseId": f"VL{playlist_id}"}
        result = self._make_request("browse", data)
        self.cache[cache_key] = result
        return result

    def _format_search_response(self, raw_data: Dict, max_results: int) -> Dict:
        items = []
        results = raw_data.get("contents", {}).get("twoColumnSearchResultsRenderer", {})
        contents = results.get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
        for section in contents:
            items_section = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items_section:
                if len(items) >= max_results:
                    break
                parsed = self._parse_search_item(item)
                if parsed:
                    items.append(parsed)
        return {"query": raw_data.get("query", ""), "result_count": len(items), "items": items}

    def _parse_search_item(self, item: Dict) -> Optional[Dict]:
        if "videoRenderer" in item:
            video = item["videoRenderer"]
            return {
                "type": "video",
                "id": video.get("videoId"),
                "title": video.get("title", {}).get("runs", [{}])[0].get("text", ""),
                "channel": video.get("ownerText", {}).get("runs", [{}])[0].get("text", ""),
                "channel_id": video.get("ownerText", {}).get("runs", [{}])[0].get("navigationEndpoint", {}).get("browseEndpoint", {}).get("browseId"),
                "views": video.get("viewCount", {}).get("simpleText", ""),
                "uploaded": video.get("publishedTimeText", {}).get("simpleText", ""),
                "thumbnail": video.get("thumbnail", {}).get("thumbnails", [{}])[-1].get("url", ""),
                "duration": video.get("lengthText", {}).get("simpleText", "")
            }
        elif "channelRenderer" in item:
            channel = item["channelRenderer"]
            return {
                "type": "channel",
                "id": channel.get("channelId"),
                "name": channel.get("title", {}).get("simpleText", ""),
                "subscribers": channel.get("subscriberCountText", {}).get("simpleText", ""),
                "videos": channel.get("videoCountText", {}).get("simpleText", ""),
                "thumbnail": channel.get("thumbnail", {}).get("thumbnails", [{}])[-1].get("url", "")
            }
        elif "playlistRenderer" in item:
            playlist = item["playlistRenderer"]
            return {
                "type": "playlist",
                "id": playlist.get("playlistId"),
                "title": playlist.get("title", {}).get("simpleText", ""),
                "video_count": playlist.get("videoCount", ""),
                "channel": playlist.get("ownerName", {}).get("simpleText", ""),
                "thumbnail": playlist.get("thumbnail", {}).get("thumbnails", [{}])[-1].get("url", "")
            }
        return None
