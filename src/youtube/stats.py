import statistics
from datetime import datetime, timezone, timedelta
from src.models import VideoData, ChannelData, NicheStats


def compute_niche_stats(keyword: str, videos: list[VideoData], channels: list[ChannelData]) -> NicheStats:
    if not videos:
        return NicheStats(
            keyword=keyword, total_views_top_videos=0, avg_views=0,
            median_views=0, videos_analyzed=0, channels_analyzed=0,
            avg_video_duration_min=0.0, avg_likes_ratio=0.0, new_channels_count=0,
        )

    views = [v.views for v in videos]
    durations = [v.duration_seconds for v in videos if v.duration_seconds > 0]
    like_ratios = [v.likes / v.views for v in videos if v.views > 0]

    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    new_channels = sum(
        1 for ch in channels
        if _parse_date(ch.published_at) and _parse_date(ch.published_at) > cutoff
    )

    return NicheStats(
        keyword=keyword,
        total_views_top_videos=sum(views),
        avg_views=int(statistics.mean(views)),
        median_views=int(statistics.median(views)),
        videos_analyzed=len(videos),
        channels_analyzed=len(channels),
        avg_video_duration_min=round(statistics.mean(durations) / 60, 1) if durations else 0.0,
        avg_likes_ratio=round(statistics.mean(like_ratios) * 100, 2) if like_ratios else 0.0,
        new_channels_count=new_channels,
    )


def get_channel_details(channel_ids: list[str]) -> list[ChannelData]:
    from src.youtube.client import get_client
    from datetime import datetime, timezone

    if not channel_ids:
        return []

    youtube = get_client()
    channels = []

    for chunk in _chunks(list(set(channel_ids)), 50):
        resp = youtube.channels().list(
            part="snippet,statistics",
            id=",".join(chunk),
        ).execute()

        for item in resp.get("items", []):
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            subscribers = int(stats.get("subscriberCount", 0))
            total_views = int(stats.get("viewCount", 0))
            video_count = int(stats.get("videoCount", 1))
            published_at = snippet.get("publishedAt", "")
            age_weeks = _channel_age_weeks(published_at)
            channels.append(ChannelData(
                channel_id=item["id"],
                title=snippet.get("title", ""),
                subscribers=subscribers,
                total_views=total_views,
                video_count=video_count,
                published_at=published_at,
                avg_views_per_video=total_views // max(video_count, 1),
                videos_per_week=round(video_count / max(age_weeks, 1), 1),
            ))

    return sorted(channels, key=lambda c: c.subscribers, reverse=True)


def enrich_channels_with_best_video(channels: list[ChannelData], videos: list[VideoData]) -> list[ChannelData]:
    best: dict[str, int] = {}
    for v in videos:
        if v.views > best.get(v.channel_id, 0):
            best[v.channel_id] = v.views
    for ch in channels:
        ch.best_video_views = best.get(ch.channel_id, 0)
    return channels


def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def _parse_date(date_str: str) -> datetime | None:
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return None


def _channel_age_weeks(published_at: str) -> int:
    d = _parse_date(published_at)
    if not d:
        return 52
    return max((datetime.now(timezone.utc) - d).days // 7, 1)
