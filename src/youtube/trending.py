import re
from src.youtube.client import get_client
from src.models import VideoData

CATEGORY_NAMES = {
    "1": "Film & Animation", "2": "Autos & Vehicles", "10": "Music",
    "15": "Pets & Animals", "17": "Sports", "19": "Travel & Events",
    "20": "Gaming", "22": "People & Blogs", "23": "Comedy",
    "24": "Entertainment", "25": "News & Politics", "26": "How-to & Style",
    "27": "Education", "28": "Science & Technology", "29": "Nonprofits",
}


def get_trending_videos(region: str = "US", max_results: int = 100) -> list[VideoData]:
    youtube = get_client()
    all_videos: list[VideoData] = []
    seen: set[str] = set()

    # Fetch trending across all categories
    video_ids: list[str] = []
    next_page = None

    while len(video_ids) < max_results:
        params = dict(
            part="id",
            chart="mostPopular",
            regionCode=region,
            maxResults=50,
        )
        if next_page:
            params["pageToken"] = next_page

        resp = youtube.videos().list(**params).execute()
        for item in resp.get("items", []):
            vid = item["id"]
            if vid not in seen:
                seen.add(vid)
                video_ids.append(vid)

        next_page = resp.get("nextPageToken")
        if not next_page:
            break

    # Fetch full details in chunks of 50
    for chunk in _chunks(video_ids[:max_results], 50):
        resp = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(chunk),
        ).execute()

        for item in resp.get("items", []):
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            cat_id = snippet.get("categoryId", "")
            all_videos.append(VideoData(
                video_id=item["id"],
                title=snippet.get("title", ""),
                channel_id=snippet.get("channelId", ""),
                channel_title=snippet.get("channelTitle", ""),
                views=int(stats.get("viewCount", 0)),
                likes=int(stats.get("likeCount", 0)),
                comments=int(stats.get("commentCount", 0)),
                duration_seconds=_parse_duration(
                    item.get("contentDetails", {}).get("duration", "PT0S")
                ),
                published_at=snippet.get("publishedAt", ""),
                category=CATEGORY_NAMES.get(cat_id, cat_id),
                description=snippet.get("description", "")[:200],
            ))

    return sorted(all_videos, key=lambda v: v.views, reverse=True)


def get_videos_by_keyword(keyword: str, region: str = "US", max_results: int = 30) -> list[VideoData]:
    """Deep-dive search for a specific niche keyword."""
    youtube = get_client()
    video_ids: list[str] = []
    seen: set[str] = set()

    for order in ("viewCount", "relevance"):
        resp = youtube.search().list(
            q=keyword,
            part="id",
            type="video",
            maxResults=min(max_results, 50),
            order=order,
            regionCode=region,
        ).execute()
        for item in resp.get("items", []):
            vid = item["id"]["videoId"]
            if vid not in seen:
                seen.add(vid)
                video_ids.append(vid)

    videos: list[VideoData] = []
    for chunk in _chunks(video_ids[:max_results], 50):
        resp = youtube.videos().list(
            part="snippet,statistics,contentDetails",
            id=",".join(chunk),
        ).execute()
        for item in resp.get("items", []):
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            videos.append(VideoData(
                video_id=item["id"],
                title=snippet.get("title", ""),
                channel_id=snippet.get("channelId", ""),
                channel_title=snippet.get("channelTitle", ""),
                views=int(stats.get("viewCount", 0)),
                likes=int(stats.get("likeCount", 0)),
                comments=int(stats.get("commentCount", 0)),
                duration_seconds=_parse_duration(
                    item.get("contentDetails", {}).get("duration", "PT0S")
                ),
                published_at=snippet.get("publishedAt", ""),
                category=CATEGORY_NAMES.get(snippet.get("categoryId", ""), ""),
                description=snippet.get("description", "")[:200],
            ))

    return sorted(videos, key=lambda v: v.views, reverse=True)


def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def _parse_duration(duration: str) -> int:
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
    if not match:
        return 0
    h = int(match.group(1) or 0)
    m = int(match.group(2) or 0)
    s = int(match.group(3) or 0)
    return h * 3600 + m * 60 + s
