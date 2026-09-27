import requests
from typing import Dict, Any

class LitterboxUploader:
    """Uploader for Litterbox using the documented internal API.

    API endpoint: https://litterbox.catbox.moe/resources/internals/api.php
    Only request type: fileupload (multipart/form-data).
    """

    VALID_DURATIONS = ("1h", "12h", "24h", "72h")

    def __init__(self):
        self.upload_url = "https://litterbox.catbox.moe/resources/internals/api.php"

    def upload(self, file_data: bytes, filename: str, duration: str = "72h", content_type: str = "audio/mpeg") -> Dict[str, Any]:
        if duration not in self.VALID_DURATIONS:
            return {"success": False, "error": f"Invalid duration '{duration}'. Valid: {', '.join(self.VALID_DURATIONS)}"}
        if not file_data:
            return {"success": False, "error": "Empty file data"}

        data = {
            "reqtype": "fileupload",
            "time": duration,
        }
        files = {
            "fileToUpload": (filename, file_data, content_type),
        }

        try:
            response = requests.post(
                self.upload_url,
                data=data,
                files=files,
                timeout=120.0,
                headers={"User-Agent": "HAPI2/1.0 (hollow-phi.vercel.app)"},
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            return {"success": False, "error": f"Upload request failed: {exc}"}

        result = response.text.strip()

        # API returns the plain URL on success, or an error string on failure.
        if result.startswith("https://litter.catbox.moe/"):
            return {"success": True, "url": result, "filename": filename, "expires": duration}
        return {"success": False, "error": result or "Empty response from Litterbox API"}
