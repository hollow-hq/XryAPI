import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))
    RATE_LIMIT = os.getenv("RATE_LIMIT", "1000 per hour")

settings = Settings()
