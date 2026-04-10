import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def main():
    parser = argparse.ArgumentParser(description="YouTube Niche Discovery Agent")
    parser.add_argument("--region", default="US", help="Region code (default: US)")
    parser.add_argument("--top", type=int, default=10, help="Number of niches to discover (default: 10)")
    args = parser.parse_args()

    region = args.region.upper()
    top_n = min(max(args.top, 3), 20)

    console.print(f"\n[bold cyan]YouTube Нише-Разведчик[/bold cyan]")
    console.print(f"[dim]Регион: {region} | Ищем топ {top_n} горячих ниш прямо сейчас...[/dim]\n")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("🌐 Собираем данные со всех источников...", total=None)

        # Phase 1: Parallel data collection
        from src.discovery.finder import collect_all
        raw = collect_all(region=region)
        progress.update(task, description=(
            f"✅ Собрано: {len(raw.trending_videos)} YouTube видео | "
            f"{len(raw.google_trending)} Google трендов | "
            f"{len(raw.reddit_hot)} Reddit постов | "
            f"{len(raw.hn_front_page)} HN постов"
        ))

        if not raw.trending_videos:
            progress.stop()
            console.print("[red]YouTube API не вернул данные. Проверь YOUTUBE_API_KEY в .env[/red]")
            sys.exit(1)

        # Phase 2: Claude discovers niches
        progress.update(task, description=f"🧠 Claude анализирует тренды и находит топ {top_n} ниш...")
        from src.discovery.claude_discover import discover_niches
        niches = discover_niches(raw, top_n=top_n)

        if not niches:
            progress.stop()
            console.print("[red]Claude не смог определить ниши. Проверь ANTHROPIC_API_KEY в .env[/red]")
            sys.exit(1)

        progress.update(task, description=f"✅ Claude нашёл {len(niches)} ниш: {', '.join(n['niche_name'] for n in niches[:3])}...")

        # Phase 3: Deep dive per niche (parallel)
        progress.update(task, description=f"🔍 Глубокий анализ {len(niches)} ниш параллельно...")
        niche_reports = _analyze_niches_parallel(niches, region, progress, task)

        progress.update(task, description=f"✅ Анализ завершён — {len(niche_reports)} ниш проанализировано")

    # Print full report
    from src.models import FullDiscoveryReport, RedditData, HNData
    from src.report.formatter import print_report

    reddit_data = RedditData(posts=raw.reddit_hot, total_posts_found=len(raw.reddit_hot))
    hn_data = HNData(posts=raw.hn_front_page, total_found=len(raw.hn_front_page))

    niche_reports.sort(key=lambda nr: nr.analysis.overall_score, reverse=True)

    report = FullDiscoveryReport(
        region=region,
        niches=niche_reports,
        raw=raw,
        reddit=reddit_data,
        hn=hn_data,
    )
    print_report(report)


def _analyze_niches_parallel(niches, region, progress, task) -> list:
    from src.youtube.trending import get_videos_by_keyword
    from src.youtube.stats import get_channel_details, enrich_channels_with_best_video, compute_niche_stats
    from src.trends.google import get_trends
    from src.rss.youtube import get_channel_rss
    from src.ai.claude import analyze_niche
    from src.models import NicheReport

    def process_niche(niche: dict):
        keyword = niche["search_keyword"]

        # YouTube search
        videos = get_videos_by_keyword(keyword, region=region, max_results=30)
        if not videos:
            return None

        # Channel details
        channel_ids = list(dict.fromkeys(v.channel_id for v in videos))[:15]
        channels = get_channel_details(channel_ids)
        channels = enrich_channels_with_best_video(channels, videos)

        # Stats
        stats = compute_niche_stats(keyword, videos, channels)

        # Trends (may fail — non-critical)
        trends = None
        try:
            import time
            time.sleep(1)
            trends = get_trends(keyword, region)
        except Exception:
            pass

        # RSS (non-critical)
        rss = None
        try:
            rss = get_channel_rss(channel_ids[:10], days_back=14)
        except Exception:
            pass

        # Claude deep analysis
        analysis = analyze_niche(niche, stats, videos, channels, trends, rss)

        return NicheReport(
            analysis=analysis,
            stats=stats,
            top_videos=videos[:10],
            top_channels=channels[:8],
            trends=trends,
            rss=rss,
        )

    results = []
    for i, niche in enumerate(niches):
        progress.update(task, description=f"🔍 [{i+1}/{len(niches)}] Анализируем: {niche['niche_name']}...")
        try:
            result = process_niche(niche)
            if result:
                results.append(result)
        except Exception as e:
            progress.update(task, description=f"⚠️  Ошибка {niche['niche_name']}: {e}")

    return results


if __name__ == "__main__":
    main()
