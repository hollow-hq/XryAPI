from flask import Blueprint, request
from ..services.youtube_service import YouTubeService, YouTubeError
from ..utils.cache_manager import CacheManager
from ..utils.response_formatter import api_response, error_response
from ..utils.rate_limiter import limiter

youtube_bp = Blueprint('youtube', __name__, url_prefix='/youtube')
youtube_service = YouTubeService()
cache_manager = CacheManager()

@youtube_bp.route('/search', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=300)
def search_youtube():
    query = request.args.get('query')
    max_results = int(request.args.get('max_results', 20))
    if not query:
        return error_response("query parameter required", 400)
    try:
        result = youtube_service.search(query, max_results)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 500)

@youtube_bp.route('/browse/<browse_id>', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=300)
def browse_youtube(browse_id):
    try:
        result = youtube_service.browse(browse_id)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 500)

@youtube_bp.route('/trending', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=600)
def trending_youtube():
    try:
        result = youtube_service.trending()
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 500)

@youtube_bp.route('/homepage', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=300)
def homepage_youtube():
    try:
        result = youtube_service.homepage()
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 500)

@youtube_bp.route('/video/<video_id>', methods=['GET'])
@limiter.limit("100 per minute")
@cache_manager.cached(ttl=300)
def video_metadata(video_id):
    try:
        result = youtube_service.video_metadata(video_id)
        return api_response(result)
    except YouTubeError as e:
        return error_response(e.reason or str(e), 502)
    except Exception as e:
        return error_response(str(e), 500)

@youtube_bp.route('/player/<video_id>', methods=['GET'])
@limiter.limit("100 per minute")
@cache_manager.cached(ttl=300)
def player_streams(video_id):
    try:
        result = youtube_service.player(video_id)
        return api_response(result)
    except YouTubeError as e:
        # Antes devolvia 200 com arrays vazios; agora o motivo real volta ao cliente.
        return error_response(e.reason or str(e), 502)
    except Exception as e:
        return error_response(str(e), 500)

@youtube_bp.route('/next/<video_id>', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=300)
def next_videos(video_id):
    try:
        result = youtube_service.next_videos(video_id)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 500)

@youtube_bp.route('/captions/<video_id>', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=600)
def video_captions(video_id):
    try:
        result = youtube_service.captions(video_id)
        return api_response(result)
    except YouTubeError as e:
        return error_response(e.reason or str(e), 502)
    except Exception as e:
        return error_response(str(e), 500)

@youtube_bp.route('/channel/<channel_id>', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=300)
def channel_info(channel_id):
    try:
        result = youtube_service.channel(channel_id)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 500)

@youtube_bp.route('/channel/<channel_id>/videos', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=300)
def channel_videos(channel_id):
    max_results = int(request.args.get('max_results', 50))
    try:
        result = youtube_service.channel_videos(channel_id, max_results)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 500)

@youtube_bp.route('/playlist/<playlist_id>', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=300)
def playlist_details(playlist_id):
    try:
        result = youtube_service.playlist(playlist_id)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 500)
