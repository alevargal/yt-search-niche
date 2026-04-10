from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from src.models import FullDiscoveryReport, NicheReport

console = Console(width=170)


def print_report(report: FullDiscoveryReport) -> None:
    console.print()
    console.rule(f"[bold cyan]  YOUTUBE НИШЕ-РАЗВЕДЧИК — ГОРЯЧИЕ НИШИ ПРЯМО СЕЙЧАС  [/bold cyan]", style="cyan")
    console.print(
        f"[dim]  Дата: {datetime.now().strftime('%d %b %Y %H:%M')} | "
        f"Регион: {report.region} | "
        f"Trending видео проанализировано: {len(report.raw.trending_videos)} | "
        f"Ниш найдено: {len(report.niches)}[/dim]"
    )
    console.print()

    # ── Summary table ──
    _print_summary_table(report.niches)
    console.print()

    # ── Raw signals ──
    _print_raw_signals(report)
    console.print()

    # ── Per-niche detailed blocks ──
    for i, niche_report in enumerate(report.niches):
        _print_niche_block(i + 1, niche_report)
        console.print()


def _print_summary_table(niches: list[NicheReport]) -> None:
    table = Table(box=box.DOUBLE_EDGE, show_header=True, padding=(0, 1), title="📊 СВОДНЫЙ РЕЙТИНГ НИШИ")
    table.add_column("#", style="dim", width=3)
    table.add_column("Ниша", style="bold white", min_width=22, max_width=30, no_wrap=False)
    table.add_column("Кат.", style="cyan", width=11)
    table.add_column("Overall", style="bold yellow", justify="center", width=9)
    table.add_column("Возможность", justify="center", width=11)
    table.add_column("Конкуренция", justify="center", width=11)
    table.add_column("Рост", justify="center", width=8)
    table.add_column("CPM", justify="center", width=10)
    table.add_column("Входить?", justify="center", width=9)

    for i, nr in enumerate(niches):
        a = nr.analysis
        worth = "[green]✅ Да[/green]" if a.worth_entering else "[red]⚠️  Нет[/red]"
        overall_color = "green" if a.overall_score >= 7 else "yellow" if a.overall_score >= 5 else "red"
        table.add_row(
            str(i + 1),
            a.niche_name[:28],
            a.category,
            f"[{overall_color}]{a.overall_score:.1f}[/{overall_color}]",
            f"{a.opportunity_score:.1f}",
            f"{a.competition_score:.1f}",
            f"{a.growth_score:.1f}",
            f"${a.estimated_cpm_min:.0f}–${a.estimated_cpm_max:.0f}",
            worth,
        )

    console.print(table)


def _print_raw_signals(report: FullDiscoveryReport) -> None:
    google_text = "\n".join(f"  [cyan]→[/cyan] {t}" for t in report.raw.google_trending[:10]) or "  нет"
    reddit_text = "\n".join(
        f"  [yellow]▲[/yellow] [{p.subreddit}] {p.title[:70]} ({p.score} pts)"
        for p in report.reddit.posts[:5]
    ) or "  нет"
    hn_text = "\n".join(
        f"  [orange3]▶[/orange3] {p.title[:70]} ({p.points} pts)"
        for p in report.hn.posts[:5]
    ) or "  нет"

    body = (
        f"[bold]Google Trends сегодня:[/bold]\n{google_text}\n\n"
        f"[bold]Reddit r/all горячее:[/bold]\n{reddit_text}\n\n"
        f"[bold]HackerNews топ:[/bold]\n{hn_text}"
    )
    console.print(Panel(body, title="[bold]🌐 СЫРЫЕ СИГНАЛЫ (на основе которых найдены ниши)[/bold]", border_style="dim"))


def _print_niche_block(rank: int, nr: NicheReport) -> None:
    a = nr.analysis
    s = nr.stats

    overall_color = "green" if a.overall_score >= 7 else "yellow" if a.overall_score >= 5 else "red"
    comp_color = {"Low": "green", "Medium": "yellow", "High": "red", "Very High": "bold red"}.get(a.competition_level, "white")
    sponsor_color = {"Low": "red", "Medium": "yellow", "High": "green", "Very High": "bold green"}.get(a.sponsor_potential, "white")

    console.rule(f"[bold]#{rank} — {a.niche_name.upper()}[/bold]", style="cyan")
    console.print(f"[dim]{a.niche_description}[/dim]")
    console.print(f"[dim]Почему трендит: {a.why_trending_now}[/dim]")
    console.print()

    # Stats row
    stats_table = Table(box=box.SIMPLE_HEAVY, show_header=False, padding=(0, 2))
    stats_table.add_column(style="dim")
    stats_table.add_column(style="bold white")
    stats_table.add_column(style="dim")
    stats_table.add_column(style="bold white")
    stats_table.add_row(
        "Видео проанализировано:", str(s.videos_analyzed),
        "Суммарных просмотров:", _fmt(s.total_views_top_videos),
    )
    stats_table.add_row(
        "Среднее просмотров:", _fmt(s.avg_views),
        "Медиана просмотров:", _fmt(s.median_views),
    )
    stats_table.add_row(
        "Ср. длина видео:", f"{s.avg_video_duration_min} мин",
        "Ср. лайков:", f"{s.avg_likes_ratio}%",
    )
    console.print(Panel(stats_table, title="[bold]📊 СТАТИСТИКА[/bold]", border_style="blue"))

    # Top videos
    if nr.top_videos:
        vt = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
        vt.add_column("#", width=3, style="dim")
        vt.add_column("Название", max_width=45)
        vt.add_column("Канал", max_width=20, style="cyan")
        vt.add_column("Просмотры", style="bold yellow", justify="right")
        vt.add_column("Лайки", justify="right")
        vt.add_column("Дата", style="dim")
        vt.add_column("Длина", style="dim")
        for i, v in enumerate(nr.top_videos[:8]):
            vt.add_row(
                str(i + 1),
                v.title[:43] + "…" if len(v.title) > 45 else v.title,
                v.channel_title[:18] + "…" if len(v.channel_title) > 20 else v.channel_title,
                _fmt(v.views),
                _fmt(v.likes),
                v.published_at[:10],
                f"{v.duration_seconds // 60}:{v.duration_seconds % 60:02d}",
            )
        console.print(Panel(vt, title="[bold]🏆 ТОП ВИДЕО[/bold]", border_style="yellow"))

    # Top channels
    if nr.top_channels:
        ct = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
        ct.add_column("#", width=3, style="dim")
        ct.add_column("Канал", max_width=25, style="cyan")
        ct.add_column("Подписчики", style="bold magenta", justify="right")
        ct.add_column("Ср. просм.", style="yellow", justify="right")
        ct.add_column("Вид/нед.", justify="right")
        ct.add_column("Лучшее видео", style="bold yellow", justify="right")
        for i, c in enumerate(nr.top_channels[:6]):
            ct.add_row(
                str(i + 1),
                c.title[:23] + "…" if len(c.title) > 25 else c.title,
                _fmt(c.subscribers),
                _fmt(c.avg_views_per_video),
                str(c.videos_per_week),
                _fmt(c.best_video_views),
            )
        console.print(Panel(ct, title="[bold]👥 ТОП КОНКУРЕНТЫ[/bold]", border_style="magenta"))

    # Trends
    if nr.trends:
        t = nr.trends
        trend_body = (
            f"  Интерес 30д: [bold]{t.interest_30d}/100[/bold] {_arrow(t.growth_30d_pct)} {t.growth_30d_pct:+.1f}%  |  "
            f"Интерес 90д: [bold]{t.interest_90d}/100[/bold] {_arrow(t.growth_90d_pct)} {t.growth_90d_pct:+.1f}%\n"
        )
        if t.rising_queries:
            trend_body += "\n  Растущие запросы:\n"
            trend_body += "\n".join(f"  [cyan]↑[/cyan] {q.query} — [green]{q.value}[/green]" for q in t.rising_queries)
        console.print(Panel(trend_body, title="[bold]📈 GOOGLE TRENDS[/bold]", border_style="green"))

    # Competition + monetization
    comp_mon = (
        f"  Конкуренция: [{comp_color}]{a.competition_level}[/{comp_color}]  |  "
        f"Порог входа: [bold]{a.barrier_to_entry}[/bold]  |  "
        f"CPM: [bold]${a.estimated_cpm_min:.0f}–${a.estimated_cpm_max:.0f}[/bold]  |  "
        f"Sponsor: [{sponsor_color}]{a.sponsor_potential}[/{sponsor_color}]  |  "
        f"Доход/1M: [bold]${a.estimated_cpm_min*1000:.0f}–${a.estimated_cpm_max*1000:.0f}[/bold]"
    )
    console.print(Panel(comp_mon, title="[bold]⚔️  КОНКУРЕНЦИЯ & 💰 МОНЕТИЗАЦИЯ[/bold]", border_style="red"))

    # Content angles
    angles = "\n".join(f"  [cyan]→[/cyan] {angle}" for angle in a.content_angles)
    console.print(Panel(angles, title="[bold]🎯 НЕЗАКРЫТЫЕ УГЛЫ[/bold]", border_style="cyan"))

    # Final recommendation
    worth = "[bold green]✅ ДА — стоит входить[/bold green]" if a.worth_entering else "[bold red]⚠️  С ОГОВОРКАМИ[/bold red]"
    scores = (
        f"  Overall: [{overall_color}]{a.overall_score:.1f}[/{overall_color}]/10  |  "
        f"Opportunity: [cyan]{a.opportunity_score:.1f}[/cyan]/10  |  "
        f"Competition: [red]{a.competition_score:.1f}[/red]/10  |  "
        f"Growth: [green]{a.growth_score:.1f}[/green]/10\n"
    )
    rec_body = (
        f"  {worth}\n\n{scores}\n"
        f"  [bold]Стратегия:[/bold] {a.strategy}\n\n"
        f"  [bold]Вывод:[/bold] [italic]{a.recommendation}[/italic]"
    )
    console.print(Panel(rec_body, title=f"[bold]📋 РЕКОМЕНДАЦИЯ CLAUDE[/bold]", border_style="bold cyan"))


def _fmt(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def _arrow(pct: float) -> str:
    if pct > 50:
        return "[bold green]▲▲[/bold green]"
    elif pct > 0:
        return "[green]▲[/green]"
    elif pct > -20:
        return "[yellow]▼[/yellow]"
    else:
        return "[red]▼▼[/red]"
