import json
import anthropic
from src.config import settings

from src.models import RawTrendingData


def discover_niches(raw: RawTrendingData, top_n: int = 10) -> list[dict]:
    """
    Send all trending data to Claude.
    Returns list of dicts: [{niche_name, search_keyword, why_trending_now, category}, ...]
    """
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    prompt = _build_prompt(raw, top_n)

    message = client.messages.create(
        model=settings.discovery_model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    return _parse(message.content[0].text, top_n)


def _build_prompt(raw: RawTrendingData, top_n: int) -> str:
    yt_text = "\n".join(
        f"  [{v.category}] \"{v.title}\" — {v.channel_title} | {v.views:,} views"
        for v in raw.trending_videos[:50]
    )
    google_text = "\n".join(f"  - {t}" for t in raw.google_trending[:20]) or "  нет данных"
    reddit_text = "\n".join(
        f"  [{p.subreddit}] {p.title} ({p.score} pts)"
        for p in raw.reddit_hot[:20]
    ) or "  нет данных"
    hn_text = "\n".join(
        f"  {p.title} ({p.points} pts, {p.num_comments} comments)"
        for p in raw.hn_front_page[:15]
    ) or "  нет данных"

    return f"""You are a YouTube niche discovery analyst. Analyze ALL trending signals below and identify the TOP {top_n} YouTube content niches that are HOT right now.

=== YOUTUBE TRENDING (top 100 mostPopular videos, region: {raw.region}) ===
{yt_text}

=== GOOGLE TRENDING SEARCHES TODAY ===
{google_text}

=== REDDIT r/all HOT POSTS ===
{reddit_text}

=== HACKERNEWS FRONT PAGE ===
{hn_text}

=== YOUR TASK ===
Based on ALL signals above, identify the TOP {top_n} YouTube content niches that:
1. Are clearly trending RIGHT NOW (multiple signals confirm it)
2. A new YouTube creator could realistically enter
3. Have content potential (not just news events)

Group related videos/topics into niches. For example, multiple AI videos = "AI Tools & Productivity" niche.

Return ONLY valid JSON array:

[
  {{
    "niche_name": "Human-readable niche name (e.g. 'AI Productivity Tools')",
    "search_keyword": "Short 2-4 word YouTube search keyword with GUARANTEED results (e.g. 'AI productivity tools'). Must be a common search term people actually type.",
    "search_keyword_fallback": "Even shorter 1-2 word fallback keyword if main fails (e.g. 'AI tools')",
    "why_trending_now": "One sentence: why this niche is hot right now based on the data",
    "category": "Tech|Finance|Gaming|Fitness|Education|Entertainment|Lifestyle|Business|Science|Other"
  }},
  ...
]

IMPORTANT for search_keyword:
- Use SHORT, COMMON search terms (2-4 words max)
- Avoid overly specific phrases — broad enough to return 30+ videos
- Examples of GOOD keywords: "minecraft survival", "roblox gameplay", "AI tools 2026", "stock market investing"
- Examples of BAD keywords: "Pokemon Champions competitive strategy guide for beginners"

Return exactly {top_n} niches, ranked from hottest to least hot. No extra text, only JSON."""


def _parse(text: str, top_n: int) -> list[dict]:
    start = text.find("[")
    end = text.rfind("]") + 1
    if start == -1 or end == 0:
        return []
    try:
        niches = json.loads(text[start:end])
        return niches[:top_n]
    except Exception:
        return []
