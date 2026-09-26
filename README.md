# HAPI2

Comprehensive Python/Flask data aggregation API serving YouTube, SoundCloud, and Spotify content.

## Base URL

| Environment | URL |
|-------------|-----|
| Production | `https://HAPI2.vercel.app` |
| Local | `http://localhost:5000` |

## Response Format

All responses follow a consistent JSON envelope:

**Success (2xx):**

```json
{
  "success": true,
  "status_code": 200,
  "data": { ... }
}
```

**Error (4xx/5xx):**

```json
{
  "success": false,
  "status_code": 400,
  "error": "query parameter required"
}
```

## Cross-Origin Resource Sharing (CORS)

CORS is enabled for all origins (`*`).

## Rate Limiting

Default: **1000 requests/hour** and **100 requests/minute** per IP. Individual endpoints may have stricter limits (noted below).

## Health Check

```
GET /
```

Returns the API status and available services.

```json
{
  "success": true,
  "name": "HAPI2",
  "version": "1.0.0",
  "services": ["youtube", "soundcloud", "spotify"],
  "status": "operational"
}
```

---

## YouTube

All YouTube endpoints use the Innertube API.

### Search

```
GET /youtube/search
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `query` | Query | **Yes** | — | Search term |
| `max_results` | Query | No | `20` | Maximum number of results to return |

Rate limit: 50/min | Cache TTL: 300s

### Browse

```
GET /youtube/browse/<browse_id}
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `browse_id` | Path | **Yes** | — | YouTube browse ID (e.g., `FEtrending`) |

Rate limit: 50/min | Cache TTL: 300s

### Trending

```
GET /youtube/trending
```

No parameters.

Rate limit: 50/min | Cache TTL: 600s

### Homepage

```
GET /youtube/homepage
```

No parameters.

Rate limit: 50/min | Cache TTL: 300s

### Video Metadata

```
GET /youtube/video/<video_id>
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `video_id` | Path | **Yes** | — | YouTube video ID |

Rate limit: 100/min | Cache TTL: 300s

### Player Streams

```
GET /youtube/player/<video_id>
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `video_id` | Path | **Yes** | — | YouTube video ID |

Returns available streaming formats and adaptive formats with direct URLs.

Rate limit: 100/min | Cache TTL: 300s

### Up Next / Related

```
GET /youtube/next/<video_id>
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `video_id` | Path | **Yes** | — | YouTube video ID |

Rate limit: 50/min | Cache TTL: 300s

### Captions

```
GET /youtube/captions/<video_id>
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `video_id` | Path | **Yes** | — | YouTube video ID |

Returns available caption tracks with language, name, URL, and auto-generated flag.

Rate limit: 50/min | Cache TTL: 600s

### Channel Info

```
GET /youtube/channel/<channel_id>
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `channel_id` | Path | **Yes** | — | YouTube channel ID |

Rate limit: 50/min | Cache TTL: 300s

### Channel Videos

```
GET /youtube/channel/<channel_id>/videos
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `channel_id` | Path | **Yes** | — | YouTube channel ID |
| `max_results` | Query | No | `50` | Maximum number of videos to return |

Rate limit: 50/min | Cache TTL: 300s

### Playlist

```
GET /youtube/playlist/<playlist_id>
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `playlist_id` | Path | **Yes** | — | YouTube playlist ID |

Rate limit: 50/min | Cache TTL: 300s

---

## SoundCloud

### Search

```
GET /soundcloud/search
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `query` | Query | **Yes** | — | Search term |

Rate limit: 50/min | Cache TTL: 300s

### Track

```
GET /soundcloud/track
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `url` | Query | **Yes** | — | SoundCloud track URL |

Rate limit: 100/min | Cache TTL: 300s

### User

```
GET /soundcloud/user
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `url` | Query | **Yes** | — | SoundCloud user/profile URL |

Rate limit: 50/min | Cache TTL: 300s

### Playlist

```
GET /soundcloud/playlist
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `url` | Query | **Yes** | — | SoundCloud playlist URL |

Rate limit: 50/min | Cache TTL: 300s

### User Tracks

```
GET /soundcloud/usertracks
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `url` | Query | **Yes** | — | SoundCloud user/profile URL |
| `limit` | Query | No | `50` | Maximum number of tracks to return |

Rate limit: 50/min | Cache TTL: 300s

### Related Tracks

```
GET /soundcloud/related
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `url` | Query | **Yes** | — | SoundCloud track URL |
| `count` | Query | No | `10` | Number of related tracks to return |

Rate limit: 50/min | Cache TTL: 300s

### Download

```
GET /soundcloud/download
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `url` | Query | **Yes** | — | SoundCloud track URL |
| `upload_to_litterbox` | Query | No | `false` | If `true`, uploads to Litterbox and returns a URL instead of raw audio |

Rate limit: 30/min

When `upload_to_litterbox` is `false`, the response is a direct MP3 file download. When `true`, a JSON response with the Litterbox URL is returned.

---

## Spotify

### Search

```
GET /spotify/search
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `query` | Query | **Yes** | — | Search term |
| `limit` | Query | No | `20` | Maximum results per type (track, artist, album, playlist) |

Rate limit: 50/min | Cache TTL: 300s

### Track

```
GET /spotify/track
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `id` | Query | **Yes*** | — | Spotify track ID |
| `url` | Query | **Yes*** | — | Spotify track URL (alternative to `id`) |

*Either `id` or `url` must be provided.

Rate limit: 100/min | Cache TTL: 300s

### Album

```
GET /spotify/album
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `id` | Query | **Yes*** | — | Spotify album ID |
| `url` | Query | **Yes*** | — | Spotify album URL (alternative to `id`) |

*Either `id` or `url` must be provided.

Rate limit: 50/min | Cache TTL: 300s

### Download Track

```
GET /spotify/download
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `url` | Query | **Yes** | — | Spotify track URL |
| `upload_to_litterbox` | Query | No | `false` | If `true`, uploads to Litterbox and returns a URL instead of raw audio |

Rate limit: 30/min

When `upload_to_litterbox` is `false`, the response is a direct FLAC file download. When `true`, a JSON response with the Litterbox URL is returned.

### Download Playlist

```
GET /spotify/download/playlist
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `url` | Query | **Yes** | — | Spotify playlist URL |
| `upload_to_litterbox` | Query | No | `false` | If `true`, uploads each track to Litterbox and returns URLs |

Rate limit: 20/min

Returns a JSON summary with total tracks, downloaded count, and per-track results.

### Download Album

```
GET /spotify/download/album
```

| Parameter | Location | Required | Default | Description |
|-----------|----------|----------|---------|-------------|
| `url` | Query | **Yes** | — | Spotify album URL |
| `upload_to_litterbox` | Query | No | `false` | If `true`, uploads each track to Litterbox and returns URLs |

Rate limit: 20/min

Returns a JSON summary with total tracks and per-track results.

---

## Litterbox Integration

All download endpoints support optional upload to [Litterbox](https://litterbox.catbox.moe/) (a temporary file host with 72-hour expiry) via the `upload_to_litterbox=true` query parameter. When enabled, instead of streaming raw audio bytes, the API uploads the file and returns a JSON object:

```json
{
  "success": true,
  "url": "https://litterbox.catbox.moe/...",
  "filename": "track.mp3",
  "expires": "72h"
}
```

---

## Setup

### Prerequisites

- Python 3.11+

### Installation

```bash
pip install -r requirements.txt
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SPOTIFY_CLIENT_ID` | Yes* | Spotify API client ID |
| `SPOTIFY_CLIENT_SECRET` | Yes* | Spotify API client secret |
| `CACHE_TTL` | No | Default cache TTL in seconds (default: `300`) |
| `RATE_LIMIT` | No | Default rate limit string (default: `1000 per hour`) |

\*Required only for Spotify endpoints.

### Run

```bash
python api/app.py
```

The server starts on `0.0.0.0:5000` with debug mode enabled.

### Docker

```bash
docker build -t HAPI2 .
docker run -p 5000:5000 --env-file .env HAPI2
```

### Deploy to Vercel

The project includes a `vercel.json` configuration. Connect the repository to Vercel and set the environment variables in the dashboard.

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 3.0.0 | Web framework |
| Flask-CORS | 4.0.0 | CORS support |
| Flask-Limiter | 4.1.1 | Rate limiting |
| requests | 2.31.0 | HTTP client |
| spotipy | 2.24.0 | Spotify Web API |
| spotiflac | ≥1.4.0 | Spotify audio download |
| soundcloud-lib | 0.6.1 | SoundCloud API |
| cachetools | 5.3.2 | In-memory TTL cache |
| python-dotenv | 1.0.0 | .env file loading |
| httpx | — | Async HTTP client |
| Pillow | 10.2.0 | Image processing |
| pydub | 0.25.1 | Audio conversion |
| ffmpeg-python | 0.2.0 | FFmpeg wrapper |
| tqdm | 4.66.1 | Progress bars |
