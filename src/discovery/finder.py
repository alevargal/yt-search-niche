from src.models import RawTrendingData


def collect_all(region: str = "US") -> RawTrendingData:
    """Collect all trending data sequentially from all sources."""
    youtube_videos = []
    google_trending = []
    reddit_hot = []
    hn_front_page = []

    try:
        youtube_videos = _get_youtube_trending(region)
    except Exception as e:
        print(f"  ⚠️  YouTube failed: {e}")

    try:
        google_trending = _get_google_trending(region)
    except Exception as e:
        print(f"  ⚠️  Google Trends failed: {e}")

    try:
        reddit_hot = _get_reddit_hot()
    except Exception as e:
        print(f"  ⚠️  Reddit failed: {e}")

    try:
        hn_front_page = _get_hn_front_page()
    except Exception as e:
        print(f"  ⚠️  HackerNews failed: {e}")

    return RawTrendingData(
        trending_videos=youtube_videos,
        google_trending=google_trending,
        reddit_hot=reddit_hot,
        hn_front_page=hn_front_page,
        region=region,
    )


def _get_youtube_trending(region: str):
    from src.youtube.trending import get_trending_videos
    return get_trending_videos(region=region, max_results=100)


def _get_google_trending(region: str):
    from src.trends.google import get_trending_searches
    return get_trending_searches(region=region)


def _get_reddit_hot():
    from src.reddit.search import get_hot_posts
    data = get_hot_posts(limit=50)
    return data.posts


def _get_hn_front_page():
    from src.hackernews.search import get_front_page
    data = get_front_page(limit=30)
    return data.posts


