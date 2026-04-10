import httpx
from src.models import HNPost, HNData

HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"


def get_front_page(limit: int = 30) -> HNData:
    """Fetch HN front page top stories — no keyword needed."""
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(HN_TOP_URL)
            if resp.status_code != 200:
                return HNData(posts=[], total_found=0)
            story_ids = resp.json()[:limit]

        posts: list[HNPost] = []
        for sid in story_ids:
            post = _fetch_item(sid)
            if post:
                posts.append(post)

        posts.sort(key=lambda p: p.points, reverse=True)
        return HNData(posts=posts, total_found=len(posts))
    except Exception:
        return HNData(posts=[], total_found=0)


def _fetch_item(item_id: int) -> HNPost | None:
    try:
        with httpx.Client(timeout=8) as client:
            resp = client.get(HN_ITEM_URL.format(item_id))
            if resp.status_code != 200:
                return None
            d = resp.json()
        if not d or d.get("type") != "story":
            return None
        return HNPost(
            post_id=str(d.get("id", "")),
            title=d.get("title", ""),
            points=d.get("score", 0),
            num_comments=d.get("descendants", 0),
            url=d.get("url", f"https://news.ycombinator.com/item?id={d.get('id')}"),
            created_at=str(d.get("time", "")),
        )
    except Exception:
        return None
