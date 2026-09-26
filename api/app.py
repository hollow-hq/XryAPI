from flask import Flask
from flask_cors import CORS
from .routes.youtube_routes import youtube_bp
from .routes.soundcloud_routes import soundcloud_bp
from .routes.spotify_routes import spotify_bp
from .utils.rate_limiter import limiter
from .utils.response_formatter import error_response
import os

def create_app():
    app = Flask(__name__)
    app.config['JSON_SORT_KEYS'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
    CORS(app, origins=['*'])
    limiter.init_app(app)
    app.register_blueprint(youtube_bp)
    app.register_blueprint(soundcloud_bp)
    app.register_blueprint(spotify_bp)

    @app.route('/')
    def health():
        return {
            "success": True,
            "name": "HAPI2",
            "version": "1.0.0",
            "services": ["youtube", "soundcloud", "spotify"],
            "status": "operational"
        }

    @app.errorhandler(404)
    def not_found(e):
        return error_response("Endpoint not found", 404)

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return error_response("Rate limit exceeded. Please wait before making more requests.", 429)

    @app.errorhandler(500)
    def internal_error(e):
        return error_response("Internal server error", 500)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
