from flask import Blueprint, request
from ..services.soundcloud_service import SoundCloudService
from ..utils.cache_manager import CacheManager
from ..utils.response_formatter import api_response, error_response
from ..utils.rate_limiter import limiter

soundcloud_bp = Blueprint('soundcloud', __name__, url_prefix='/soundcloud')
soundcloud_service = SoundCloudService()
cache_manager = CacheManager()

@soundcloud_bp.route('/search', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=300)
def search_soundcloud():
    query = request.args.get('query')
    if not query:
        return error_response("query parameter required", 400)
    try:
        result = soundcloud_service.search(query)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 500)

@soundcloud_bp.route('/track', methods=['GET'])
@limiter.limit("100 per minute")
@cache_manager.cached(ttl=300)
def get_track():
    url = request.args.get('url')
    if not url:
        return error_response("url parameter required", 400)
    try:
        result = soundcloud_service.get_track(url)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 400)

@soundcloud_bp.route('/user', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=300)
def get_user():
    url = request.args.get('url')
    if not url:
        return error_response("url parameter required", 400)
    try:
        result = soundcloud_service.get_user(url)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 400)

@soundcloud_bp.route('/playlist', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=300)
def get_playlist():
    url = request.args.get('url')
    if not url:
        return error_response("url parameter required", 400)
    try:
        result = soundcloud_service.get_playlist(url)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 400)

@soundcloud_bp.route('/usertracks', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=300)
def get_user_tracks():
    url = request.args.get('url')
    limit = int(request.args.get('limit', 50))
    if not url:
        return error_response("url parameter required", 400)
    try:
        result = soundcloud_service.get_user_tracks(url, limit)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 400)

@soundcloud_bp.route('/related', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=300)
def get_related():
    url = request.args.get('url')
    count = int(request.args.get('count', 10))
    if not url:
        return error_response("url parameter required", 400)
    try:
        result = soundcloud_service.get_related(url, count)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 400)

@soundcloud_bp.route('/download', methods=['GET'])
@limiter.limit("30 per minute")
def download_audio():
    url = request.args.get('url')
    upload_to_litterbox = request.args.get('upload_to_litterbox', 'false').lower() == 'true'
    if not url:
        return error_response("url parameter required", 400)
    try:
        result = soundcloud_service.download_audio(url, upload_to_litterbox)
        if upload_to_litterbox:
            return api_response(result)
        from flask import send_file
        import io
        return send_file(io.BytesIO(result), mimetype='audio/mpeg', as_attachment=True, download_name='track.mp3')
    except Exception as e:
        return error_response(str(e), 400)
