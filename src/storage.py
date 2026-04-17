import json
from datetime import datetime
from pathlib import Path

from src.models import FullDiscoveryReport

_REPORTS_DIR = Path(__file__).parent.parent / "reports"


def save_report(report: FullDiscoveryReport) -> Path:
    _REPORTS_DIR.mkdir(exist_ok=True)
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M") + f"_{report.region}.json"
    path = _REPORTS_DIR / filename
    path.write_text(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2))
    return path


def list_reports() -> list[dict]:
    if not _REPORTS_DIR.exists():
        return []
    files = sorted(_REPORTS_DIR.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    result = []
    for i, f in enumerate(files):
        try:
            data = json.loads(f.read_text())
            niches = data.get("niches", [])
            top_score = max((n["analysis"]["overall_score"] for n in niches if n.get("analysis")), default=0)
            mtime = f.stat().st_mtime
            dt = datetime.fromtimestamp(mtime)
            months = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
            date_str = f"{dt.day} {months[dt.month - 1]} {dt.year} · {dt.strftime('%H:%M')}"
            result.append({
                "filename": f.name,
                "date_str": date_str,
                "region": data.get("region", "?"),
                "niche_count": len(niches),
                "top_score": round(top_score, 1),
                "is_latest": i == 0,
            })
        except Exception:
            continue
    return result


def load_report(filename: str) -> dict:
    if "/" in filename or "\\" in filename or ".." in filename:
        raise ValueError("Invalid filename")
    path = _REPORTS_DIR / filename
    return json.loads(path.read_text())
