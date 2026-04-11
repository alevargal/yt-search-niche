from pydantic import BaseModel


# ── YouTube ──────────────────────────────────────────────────────────────────

class VideoData(BaseModel):
    video_id: str
    title: str
    channel_id: str
    channel_title: str
    views: int
    likes: int
    comments: int
    duration_seconds: int
    published_at: str
    category: str = ""
    description: str = ""


class ChannelData(BaseModel):
    channel_id: str
    title: str
    subscribers: int
    total_views: int
    video_count: int
    published_at: str
    avg_views_per_video: int = 0
    videos_per_week: float = 0.0
    best_video_views: int = 0


# ── Trends ───────────────────────────────────────────────────────────────────

class TrendPoint(BaseModel):
    date: str
    value: int


class RelatedQuery(BaseModel):
    query: str
    value: str


class TrendsData(BaseModel):
    keyword: str
    interest_30d: int
    interest_90d: int
    growth_30d_pct: float
    growth_90d_pct: float
    is_seasonal: bool
    rising_queries: list[RelatedQuery]
    timeline: list[TrendPoint]


# ── Reddit ───────────────────────────────────────────────────────────────────

class RedditPost(BaseModel):
    post_id: str
    title: str
    subreddit: str
    score: int
    upvote_ratio: float
    num_comments: int
    url: str
    created_utc: str
    selftext: str = ""


class RedditData(BaseModel):
    posts: list[RedditPost]
    total_posts_found: int


# ── HackerNews ───────────────────────────────────────────────────────────────

class HNPost(BaseModel):
    post_id: str
    title: str
    points: int
    num_comments: int
    url: str
    created_at: str


class HNData(BaseModel):
    posts: list[HNPost]
    total_found: int


# ── RSS ──────────────────────────────────────────────────────────────────────

class RssEntry(BaseModel):
    video_id: str
    title: str
    channel_id: str
    channel_title: str
    published: str
    views: int = 0
    url: str = ""


class RssData(BaseModel):
    entries: list[RssEntry]
    recent_titles: list[str]
    active_channels_count: int
    avg_videos_per_channel: float
    days_back: int


# ── Raw trending data (before Claude clustering) ──────────────────────────────

class RawTrendingData(BaseModel):
    trending_videos: list[VideoData]          # YouTube mostPopular
    google_trending: list[str]                # today's trending searches
    reddit_hot: list[RedditPost]              # r/all hot
    hn_front_page: list[HNPost]              # HN front page
    region: str


# ── Per-niche analysis ────────────────────────────────────────────────────────

class NicheStats(BaseModel):
    keyword: str
    total_views_top_videos: int
    avg_views: int
    median_views: int
    videos_analyzed: int
    channels_analyzed: int
    avg_video_duration_min: float
    avg_likes_ratio: float
    new_channels_count: int


class NicheAnalysis(BaseModel):
    niche_name: str
    niche_description: str
    category: str = "Other"
    competition_level: str
    opportunity_score: float
    competition_score: float
    growth_score: float
    overall_score: float
    estimated_cpm_min: float
    estimated_cpm_max: float
    sponsor_potential: str
    barrier_to_entry: str
    viral_patterns: str = ""
    audience_profile: str = ""
    top_channel_analysis: str = ""
    content_angles: list[str]
    channel_concept: str = ""
    first_10_videos: list[str] = []
    why_trending_now: str
    monetization_breakdown: str = ""
    strategy: str
    recommendation: str
    worth_entering: bool


class NicheReport(BaseModel):
    analysis: NicheAnalysis
    stats: NicheStats
    top_videos: list[VideoData]
    top_channels: list[ChannelData]
    trends: TrendsData | None
    rss: RssData | None


# ── Full discovery report ─────────────────────────────────────────────────────

class FullDiscoveryReport(BaseModel):
    region: str
    niches: list[NicheReport]                 # ranked by overall_score desc
    raw: RawTrendingData
    reddit: RedditData
    hn: HNData
