import httpx
from src.models import RedditPost, RedditData

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; yt-niche-analyzer/1.0)"}


def get_hot_posts(limit: int = 50) -> RedditData:
    """Fetch hot posts from r/all — no keyword, pure trending."""
    posts: list[RedditPost] = []
    posts += _fetch("https://www.reddit.com/r/all/hot.json", limit=limit)
    posts += _fetch("https://www.reddit.com/r/all/rising.json", limit=25)

    seen = set()
    unique = []
    for p in posts:
        if p.post_id not in seen:
            seen.add(p.post_id)
            unique.append(p)

    unique.sort(key=lambda p: p.score, reverse=True)
    return RedditData(posts=unique[:40], total_posts_found=len(unique))


def _fetch(url: str, limit: int) -> list[RedditPost]:
    try:
        with httpx.Client(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            resp = client.get(url, params={"limit": limit})
            if resp.status_code != 200:
                return []
            data = resp.json()
        posts = []
        for item in data.get("data", {}).get("children", []):
            d = item.get("data", {})
            posts.append(RedditPost(
                post_id=d.get("id", ""),
                title=d.get("title", ""),
                subreddit=d.get("subreddit", ""),
                score=d.get("score", 0),
                upvote_ratio=round(d.get("upvote_ratio", 0), 2),
                num_comments=d.get("num_comments", 0),
                url=f"https://reddit.com{d.get('permalink', '')}",
                created_utc=str(int(d.get("created_utc", 0))),
                selftext=(d.get("selftext", "") or "")[:300],
            ))
        return posts
    except Exception:
        return []
