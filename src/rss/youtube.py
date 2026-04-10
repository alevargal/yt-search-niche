import feedparser
from datetime import datetime, timezone, timedelta
from src.models import RssEntry, RssData


def get_channel_rss(channel_ids: list[str], days_back: int = 14) -> RssData:
    """Fetch recent videos from YouTube channels via RSS (no API quota)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    all_entries: list[RssEntry] = []

    for channel_id in channel_ids[:15]:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        entries = _fetch_feed(url, cutoff)
        all_entries.extend(entries)

    all_entries.sort(key=lambda e: e.published, reverse=True)

    recent_titles = [e.title for e in all_entries[:20]]
    active_channels = len(set(e.channel_id for e in all_entries))
    avg_videos_per_channel = round(len(all_entries) / max(active_channels, 1), 1)

    return RssData(
        entries=all_entries[:30],
        recent_titles=recent_titles,
        active_channels_count=active_channels,
        avg_videos_per_channel=avg_videos_per_channel,
        days_back=days_back,
    )


def _fetch_feed(url: str, cutoff: datetime) -> list[RssEntry]:
    try:
        feed = feedparser.parse(url)
        entries = []

        for entry in feed.entries:
            published = _parse_date(entry.get("published", ""))
            if published and published < cutoff:
                continue

            views = 0
            for tag in entry.get("media_statistics", [{}]):
                if isinstance(tag, dict):
                    views = int(tag.get("views", 0))

            entries.append(RssEntry(
                video_id=entry.get("yt_videoid", ""),
                title=entry.get("title", ""),
                channel_id=entry.get("yt_channelid", ""),
                channel_title=feed.feed.get("title", ""),
                published=published.isoformat() if published else "",
                views=views,
                url=entry.get("link", ""),
            ))

        return entries
    except Exception:
        return []


def _parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return None
