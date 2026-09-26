import requests
import json
from typing import Dict, Any, Optional

class LitterboxUploader:
    def __init__(self):
        self.upload_url = "https://litterbox.catbox.moe/upload"

    def upload(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        files = {'files[]': (filename, file_data, 'audio/mpeg')}
        data = {'duration': '72h'}
        response = requests.post(self.upload_url, files=files, data=data, timeout=120.0)
        response.raise_for_status()
        result = response.text.strip()
        if "https://" in result:
            return {"success": True, "url": result, "filename": filename, "expires": "72h"}
        return {"success": False, "error": result}
