from flask import Blueprint, request, send_file
from ..services.spotify_service import SpotifyService
from ..utils.cache_manager import CacheManager
from ..utils.response_formatter import api_response, error_response
from ..utils.rate_limiter import limiter
import io

spotify_bp = Blueprint('spotify', __name__, url_prefix='/spotify')
spotify_service = SpotifyService()
cache_manager = CacheManager()


@spotify_bp.route('/search', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=300)
def search_spotify():
    query = request.args.get('query')
    limit = int(request.args.get('limit', 20))
    if not query:
        return error_response("query parameter required", 400)
    try:
        result = spotify_service.search(query, limit)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 500)


@spotify_bp.route('/track', methods=['GET'])
@limiter.limit("100 per minute")
@cache_manager.cached(ttl=300)
def get_track():
    track_id = request.args.get('id') or request.args.get('url')
    if not track_id:
        return error_response("id or url parameter required", 400)
    try:
        result = spotify_service.get_track(track_id)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 400)


@spotify_bp.route('/download', methods=['GET'])
@limiter.limit("30 per minute")
def download_audio():
    url = request.args.get('url')
    upload_to_litterbox = request.args.get('upload_to_litterbox', 'false').lower() == 'true'
    if not url:
        return error_response("url parameter required", 400)
    try:
        result = spotify_service.download_audio(url, upload_to_litterbox)
        if upload_to_litterbox:
            return api_response(result)
        return send_file(io.BytesIO(result), mimetype='audio/flac', as_attachment=True, download_name='track.flac')
    except Exception as e:
        return error_response(str(e), 400)


@spotify_bp.route('/download/playlist', methods=['GET'])
@limiter.limit("20 per minute")
def download_playlist():
    url = request.args.get('url')
    upload_to_litterbox = request.args.get('upload_to_litterbox', 'false').lower() == 'true'
    if not url:
        return error_response("url parameter required", 400)
    try:
        result = spotify_service.download_playlist(url, upload_to_litterbox)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 400)


@spotify_bp.route('/download/album', methods=['GET'])
@limiter.limit("20 per minute")
def download_album():
    url = request.args.get('url')
    upload_to_litterbox = request.args.get('upload_to_litterbox', 'false').lower() == 'true'
    if not url:
        return error_response("url parameter required", 400)
    try:
        result = spotify_service.download_album(url, upload_to_litterbox)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 400)


@spotify_bp.route('/album', methods=['GET'])
@limiter.limit("50 per minute")
@cache_manager.cached(ttl=300)
def get_album():
    album_id = request.args.get('id') or request.args.get('url')
    if not album_id:
        return error_response("id or url parameter required", 400)
    try:
        result = spotify_service.get_album(album_id)
        return api_response(result)
    except Exception as e:
        return error_response(str(e), 400)
