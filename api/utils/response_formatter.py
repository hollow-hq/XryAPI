from flask import jsonify
from typing import Any, Dict

def api_response(data: Any, status_code: int = 200):
    return jsonify({
        "success": status_code < 400,
        "status_code": status_code,
        "data": data
    }), status_code

def error_response(message: str, status_code: int = 400):
    return jsonify({
        "success": False,
        "status_code": status_code,
        "error": message
    }), status_code
