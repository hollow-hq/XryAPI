import re
import time

import httpx
import cachetools
from typing import Dict, Any, List, Optional, Tuple
from cachetools import TTLCache

class InnertubeClient:
    """Um client do Innertube (nome interno, id numerico, versao, extras)."""

    def __init__(self, name: str, client_id: str, version: str, user_agent: str, **extra: Any):
        self.name = name
        self.client_id = client_id
        self.version = version
        self.user_agent = user_agent
        self.extra = extra


# YouTube recusa clients desatualizados com UNPLAYABLE / "page needs to be reloaded".
# A versao do WEB precisa ser a atual (extraida da pagina a cada inicializacao).
DEFAULT_WEB_VERSION = "2.20260925.01.00"

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
)

# Ordem importa: WEB primeiro (melhor metadado), depois os clients moveis
# que costumam devolver streamingData sem PO token.
PLAYER_CLIENTS = [
    InnertubeClient("ANDROID", "3", "20.10.38",
                    "com.google.android.youtube/20.10.38 (Linux; U; Android 14)"),
    InnertubeClient("ANDROID", "3", "21.05.34",
                    "com.google.android.youtube/21.05.34 (Linux; U; Android 14)"),
    InnertubeClient("ANDROID_VR", "28", "1.65.10",
                    "com.google.android.apps.youtube.vr.oculus/1.65.10 (Linux; U; Android 12)"),
    InnertubeClient("IOS", "5", "20.10.4",
                    "com.google.ios.youtube/20.10.4 (iPhone16,2; U; CPU iOS 18_3 like Mac OS X)"),
    InnertubeClient("TVHTML5", "7", "7.20250316.18.00",
                    "Mozilla/5.0 (PlayStation; PlayStation 4/12.00) AppleWebKit/605.1.15"),
    InnertubeClient("WEB", "1", DEFAULT_WEB_VERSION, CHROME_UA),
    InnertubeClient("MWEB", "2", DEFAULT_WEB_VERSION, CHROME_UA),
]


class YouTubeError(Exception):
    def __init__(self, message: str, status: Optional[str] = None, reason: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.reason = reason


class YouTubeService:
    def __init__(self):
        self.base_url = "https://www.youtube.com/youtubei/v1"
        self.api_key = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
        self.client_version = DEFAULT_WEB_VERSION
        self.cache = TTLCache(maxsize=100, ttl=300)
        self.session = httpx.Client(timeout=30.0, follow_redirects=True)
        self.visitor_data: Optional[str] = None
        self._visitor_ts = 0.0
        self._fetch_visitor_data()

    def _fetch_visitor_data(self) -> None:
        """visitorData + clientVersion atuais, lidos da pagina /embed.

        Sem isso o WEB responde UNPLAYABLE ('Video unavailable').
        """
        try:
            r = self.session.get(
                "https://www.youtube.com/embed/dQw4w9WgXcQ",
                headers={"User-Agent": CHROME_UA, "Accept-Language": "en-US,en;q=0.9"},
            )
            vm = re.search(r'"visitorData":"([^"]+)"', r.text)
            if vm:
                self.visitor_data = vm.group(1)
            ver = re.search(r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"', r.text)
            if ver:
                self.client_version = ver.group(1)
            key = re.search(r'"INNERTUBE_API_KEY":"([^"]+)"', r.text)
            if key:
                self.api_key = key.group(1)
            self._visitor_ts = time.time()
        except Exception:
            pass

    def _maybe_refresh_visitor(self) -> None:
        if not self.visitor_data or time.time() - self._visitor_ts > 1800:
            self._fetch_visitor_data()

    def _make_request(self, endpoint: str, data: Dict, client: Optional[InnertubeClient] = None) -> Dict:
        client = client or PLAYER_CLIENTS[0]
        version = client.version
        if client.name in ("WEB", "MWEB"):
            self._maybe_refresh_visitor()
            version = self.client_version

        context_client: Dict[str, Any] = {
            "hl": "en",
            "gl": "US",
            "clientName": client.name,
            "clientVersion": version,
        }
        context_client.update(client.extra)
        # visitorData pertence ao client WEB. Reutilizar esse token em clients
        # mobile/TV faz o YouTube responder 400 (Precondition check failed).
        uses_visitor = client.name in ("WEB", "MWEB")
        if self.visitor_data and uses_visitor:
            context_client["visitorData"] = self.visitor_data

        context: Dict[str, Any] = {"client": context_client}
        if client.extra.get("clientScreen") == "EMBED":
            context["thirdParty"] = {"embedUrl": "https://www.youtube.com/"}
        elif client.name.startswith("TVHTML5"):
            context["thirdParty"] = {"embedUrl": "https://www.youtube.com/"}

        payload: Dict[str, Any] = {"context": context, **data}
        if endpoint == "player":
            payload.setdefault("contentCheckOk", True)
            payload.setdefault("racyCheckOk", True)

        headers = {
            "Content-Type": "application/json",
            "X-YouTube-Client-Name": client.client_id,
            "X-YouTube-Client-Version": version,
            "Origin": "https://www.youtube.com",
            "Referer": "https://www.youtube.com/",
            "User-Agent": client.user_agent,
            "Accept-Language": "en-US,en;q=0.9",
        }
        if self.visitor_data and uses_visitor:
            headers["X-Goog-Visitor-Id"] = self.visitor_data

        url = f"{self.base_url}/{endpoint}"
        # Android/iOS exigem a API key na query string.
        if client.name in ("ANDROID", "IOS"):
            url = f"{url}?key={self.api_key}"
        response = self.session.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _playability(result: Dict) -> tuple:
        ps = result.get("playabilityStatus", {}) or {}
        return ps.get("status"), ps.get("reason"), ps.get("errorScreen", {})

    def _player_request(self, video_id: str, clients: Optional[List[InnertubeClient]] = None) -> Dict:
        """Chama /player; se um client falhar, tenta o proximo. Erro final elanca YouTubeError."""
        clients = clients or PLAYER_CLIENTS
        last_status = None
        last_reason = None
        for client in clients:
            try:
                result = self._make_request("player", {"videoId": video_id}, client)
            except Exception as e:
                last_status, last_reason = "REQUEST_FAILED", str(e)
                continue
            status, reason, _ = self._playability(result)
            if status == "OK" and result.get("streamingData"):
                result["_client_used"] = client.name
                return result
            if status == "OK":
                result["_client_used"] = client.name
                return result
            last_status, last_reason = status, reason
        raise YouTubeError(last_reason or "no formats returned by YouTube", last_status, last_reason)

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
        result = self._player_request(video_id)
        self.cache[cache_key] = result
        return result

    @staticmethod
    def _format_entry(fmt: Dict) -> Dict[str, Any]:
        return {
            "itag": fmt.get("itag"),
            "mime_type": fmt.get("mimeType"),
            "quality": fmt.get("qualityLabel") or fmt.get("quality"),
            "url": fmt.get("url"),
            "cipher": fmt.get("signatureCipher"),
            "bitrate": fmt.get("bitrate"),
            "fps": fmt.get("fps"),
            "width": fmt.get("width"),
            "height": fmt.get("height"),
            "audio_quality": fmt.get("audioQuality"),
            "content_length": fmt.get("contentLength"),
            "approx_duration_ms": fmt.get("approxDurationMs"),
        }

    def player(self, video_id: str) -> Dict[str, Any]:
        cache_key = f"player_{video_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        result = self._player_request(video_id)
        formats = []
        streaming_data = result.get("streamingData", {}) or {}
        for fmt in streaming_data.get("formats", []):
            formats.append(self._format_entry(fmt))
        adaptive_formats = []
        for fmt in streaming_data.get("adaptiveFormats", []):
            adaptive_formats.append(self._format_entry(fmt))
        video_details = result.get("videoDetails", {}) or {}
        self.cache[cache_key] = {
            "video_id": video_id,
            "title": video_details.get("title"),
            "length_seconds": video_details.get("lengthSeconds"),
            "is_live": (result.get("playabilityStatus", {}) or {}).get("liveStreamability") is not None
                        or video_details.get("isLive", False),
            "client_used": result.get("_client_used"),
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
        result = self._make_request("next", data, PLAYER_CLIENTS[0])
        self.cache[cache_key] = result
        return result

    def captions(self, video_id: str) -> Dict[str, Any]:
        cache_key = f"captions_{video_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        result = self._player_request(video_id)
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
