import time
from pytrends.request import TrendReq
from src.models import TrendsData, TrendPoint, RelatedQuery


def get_trending_searches(region: str = "US") -> list[str]:
    """Return today's trending search terms from Google Trends."""
    pytrends = TrendReq(hl="en-US", tz=0, timeout=(10, 25), retries=2, backoff_factor=0.5)
    country_map = {"US": "united_states", "RU": "russia", "GB": "united_kingdom",
                   "DE": "germany", "FR": "france", "BR": "brazil", "IN": "india"}
    pn = country_map.get(region, "united_states")
    try:
        df = pytrends.trending_searches(pn=pn)
        if df is not None and not df.empty:
            return df[0].tolist()[:30]
        # Fallback: realtime trends
        df2 = pytrends.realtime_trending_searches(pn=pn)
        if df2 is not None and not df2.empty:
            return df2["title"].tolist()[:30]
        return []
    except Exception:
        return []


def get_trends(keyword: str, region: str = "US") -> TrendsData:
    pytrends = TrendReq(hl="en-US", tz=0, timeout=(15, 30), retries=3, backoff_factor=1.0)
    geo = "" if region in ("global", "") else region

    interest_90d, timeline = _get_interest_with_timeline(pytrends, keyword, geo, "today 3-m")
    time.sleep(4)
    interest_30d = _calc_last_month_interest(timeline)
    rising, _ = _get_related_queries(pytrends, keyword, geo)

    growth_30d = _calc_growth(timeline, points=4)
    growth_90d = _calc_growth(timeline, points=12)
    is_seasonal = _detect_seasonality(timeline)

    return TrendsData(
        keyword=keyword,
        interest_30d=interest_30d,
        interest_90d=interest_90d,
        growth_30d_pct=growth_30d,
        growth_90d_pct=growth_90d,
        is_seasonal=is_seasonal,
        rising_queries=rising[:5],
        timeline=timeline,
    )


def _get_avg_interest(pytrends, keyword, geo, timeframe) -> int:
    try:
        pytrends.build_payload([keyword], geo=geo, timeframe=timeframe)
        df = pytrends.interest_over_time()
        if df.empty or keyword not in df.columns:
            return 0
        return int(df[keyword].mean())
    except Exception:
        return 0


def _get_interest_with_timeline(pytrends, keyword, geo, timeframe) -> tuple[int, list[TrendPoint]]:
    try:
        pytrends.build_payload([keyword], geo=geo, timeframe=timeframe)
        df = pytrends.interest_over_time()
        if df.empty or keyword not in df.columns:
            return 0, []
        timeline = [TrendPoint(date=str(idx.date()), value=int(row[keyword])) for idx, row in df.iterrows()]
        return int(df[keyword].mean()), timeline
    except Exception:
        return 0, []


def _get_related_queries(pytrends, keyword, geo) -> tuple[list[RelatedQuery], list[RelatedQuery]]:
    try:
        pytrends.build_payload([keyword], geo=geo, timeframe="today 3-m")
        related = pytrends.related_queries().get(keyword, {})
        rising_df = related.get("rising")
        top_df = related.get("top")
        rising = []
        if rising_df is not None and not rising_df.empty:
            for _, row in rising_df.iterrows():
                val = str(row.get("value", ""))
                if val == "Breakout":
                    val = "+5000%"
                rising.append(RelatedQuery(query=str(row["query"]), value=f"+{val}%" if "%" not in val else val))
        top = []
        if top_df is not None and not top_df.empty:
            for _, row in top_df.iterrows():
                top.append(RelatedQuery(query=str(row["query"]), value=str(row.get("value", ""))))
        return rising, top
    except Exception:
        return [], []


def _calc_last_month_interest(timeline: list[TrendPoint]) -> int:
    """Calculate average interest for last 4 weeks from 3-month timeline."""
    if not timeline:
        return 0
    last_4 = timeline[-4:]
    return int(sum(p.value for p in last_4) / len(last_4))


def _calc_growth(timeline: list[TrendPoint], points: int) -> float:
    if len(timeline) < 2:
        return 0.0
    recent = timeline[-points:] if len(timeline) >= points else timeline[-2:]
    old = timeline[:points] if len(timeline) >= points * 2 else timeline[:2]
    avg_r = sum(p.value for p in recent) / len(recent) if recent else 0
    avg_o = sum(p.value for p in old) / len(old) if old else 1
    if avg_o == 0:
        return 0.0
    return round((avg_r - avg_o) / avg_o * 100, 1)


def _detect_seasonality(timeline: list[TrendPoint]) -> bool:
    if len(timeline) < 12:
        return False
    values = [p.value for p in timeline]
    half = len(values) // 2
    a = sum(values[:half]) / half
    b = sum(values[half:]) / half
    return abs(a - b) / max(a, 1) > 0.3
