import json
import re
import anthropic
from src.config import settings
from src.models import VideoData, ChannelData, TrendsData, NicheStats, NicheAnalysis, RssData


def analyze_niche(
    niche: dict,
    stats: NicheStats,
    top_videos: list[VideoData],
    top_channels: list[ChannelData],
    trends: TrendsData | None,
    rss: RssData | None,
) -> NicheAnalysis:
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    prompt = _build_prompt(niche, stats, top_videos, top_channels, trends, rss)

    message = client.messages.create(
        model=settings.analysis_model,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse(message.content[0].text, niche)


def _build_prompt(niche, stats, top_videos, top_channels, trends, rss) -> str:
    videos_text = "\n".join(
        f"  #{i+1} \"{v.title}\" | {v.channel_title} | {v.views:,} views | "
        f"{v.likes:,} likes | {v.comments:,} comments | {v.published_at[:10]} | {v.duration_seconds // 60}min"
        for i, v in enumerate(top_videos[:15])
    )
    channels_text = "\n".join(
        f"  #{i+1} {c.title} | {c.subscribers:,} subs | avg {c.avg_views_per_video:,} views/video | "
        f"{c.videos_per_week} vid/week | best: {c.best_video_views:,} views"
        for i, c in enumerate(top_channels[:10])
    )
    trends_text = ""
    if trends:
        rising = "\n".join(f"  - {q.query}: {q.value}" for q in trends.rising_queries) or "  none"
        trends_text = f"""
=== GOOGLE TRENDS ===
Interest 30d: {trends.interest_30d}/100 | Growth 30d: {trends.growth_30d_pct:+.1f}%
Interest 90d: {trends.interest_90d}/100 | Growth 90d: {trends.growth_90d_pct:+.1f}%
Seasonal: {trends.is_seasonal}
Rising queries:
{rising}"""

    rss_text = ""
    if rss and rss.entries:
        titles = "\n".join(f"  • \"{t}\"" for t in rss.recent_titles[:8])
        rss_text = f"""
=== RSS (competitor activity last 14 days) ===
Active channels: {rss.active_channels_count} | Avg videos/channel: {rss.avg_videos_per_channel}
Recent uploads:
{titles}"""

    return f"""You are a YouTube niche analyst. Provide a deep analysis of this niche.

NICHE: "{niche['niche_name']}"
WHY TRENDING: {niche['why_trending_now']}
CATEGORY: {niche['category']}

=== YOUTUBE STATS ===
Videos analyzed: {stats.videos_analyzed} | Channels: {stats.channels_analyzed}
Total views (top videos): {stats.total_views_top_videos:,}
Average views/video: {stats.avg_views:,}
Median views/video: {stats.median_views:,}
Avg video duration: {stats.avg_video_duration_min} min
Avg like ratio: {stats.avg_likes_ratio}%
New channels (90d): {stats.new_channels_count}

=== TOP VIDEOS ===
{videos_text}

=== TOP CHANNELS ===
{channels_text}
{trends_text}
{rss_text}

=== TASK ===
Give a deep, data-driven analysis. Reference REAL competitor names and ACTUAL view numbers from the data above.
Return ONLY valid JSON:

{{
  "niche_name": "{niche['niche_name']}",
  "niche_description": "2-sentence description of this niche and its audience",
  "category": "{niche['category']}",
  "competition_level": "Low|Medium|High|Very High",
  "opportunity_score": 7.5,
  "competition_score": 8.1,
  "growth_score": 9.3,
  "overall_score": 8.2,
  "estimated_cpm_min": 4.0,
  "estimated_cpm_max": 14.0,
  "sponsor_potential": "Low|Medium|High|Very High",
  "barrier_to_entry": "Easy|Medium|Hard|Very Hard",
  "viral_patterns": "2-3 sentences: what makes videos go viral in this niche? What titles/formats/angles get the most views? Reference actual top video titles from the data.",
  "audience_profile": "Who exactly watches this content? Age, interests, why they watch, what problem they're solving.",
  "top_channel_analysis": "Analyze the top 2-3 competitors: what they do well, how often they post, their weak spots, what they DON'T cover.",
  "content_angles": [
    "Specific angle #1 — what's missing + exact video title example you could make",
    "Specific angle #2 — what's missing + exact video title example",
    "Specific angle #3 — what's missing + exact video title example",
    "Specific angle #4 — what's missing + exact video title example",
    "Specific angle #5 — what's missing + exact video title example"
  ],
  "channel_concept": "CONCRETE channel concept: exact name idea, exact niche positioning, exact content pillars (3-4 recurring series), exact upload schedule, exact video length. This should be specific enough to start tomorrow.",
  "first_10_videos": [
    "Exact title for video #1 you should make first",
    "Exact title for video #2",
    "Exact title for video #3",
    "Exact title for video #4",
    "Exact title for video #5"
  ],
  "why_trending_now": "{niche['why_trending_now']}",
  "monetization_breakdown": "How exactly to monetize: AdSense CPM range, which sponsors are realistic, affiliate programs, merch potential, membership potential.",
  "strategy": "5-6 sentences: concrete 90-day strategy with milestones. Reference competitor names and actual numbers. What to do week 1, month 1, month 3.",
  "recommendation": "3-4 sentences: honest final verdict. Should they enter? What's the biggest risk? What's the biggest opportunity?",
  "worth_entering": true
}}"""


def _parse(text: str, niche: dict) -> NicheAnalysis:
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        print(f"  ⚠️  Claude parse error: no JSON found for '{niche.get('niche_name')}'")
        return _default(niche)
    try:
        data = json.loads(text[start:end])
        return NicheAnalysis(**data)
    except Exception as e:
        print(f"  ⚠️  Claude parse error for '{niche.get('niche_name')}': {e}")
        print(f"  Raw (first 300): {text[:300]}")
        return _default(niche)


def _default(niche: dict) -> NicheAnalysis:
    return NicheAnalysis(
        niche_name=niche.get("niche_name", "Unknown"),
        niche_description="Analysis unavailable.",
        competition_level="Unknown",
        opportunity_score=5.0, competition_score=5.0,
        growth_score=5.0, overall_score=5.0,
        estimated_cpm_min=2.0, estimated_cpm_max=8.0,
        sponsor_potential="Medium", barrier_to_entry="Medium",
        content_angles=["Analysis unavailable"],
        why_trending_now=niche.get("why_trending_now", ""),
        strategy="Analysis unavailable.",
        recommendation="Analysis unavailable.",
        worth_entering=False,
    )
