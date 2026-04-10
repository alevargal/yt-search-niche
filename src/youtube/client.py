from googleapiclient.discovery import build
from src.config import settings

_client = None


def get_client():
    global _client
    if _client is None:
        _client = build("youtube", "v3", developerKey=settings.youtube_api_key)
    return _client
