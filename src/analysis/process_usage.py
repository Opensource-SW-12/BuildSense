import json
from collections import defaultdict
from pathlib import Path

_CATEGORIES_PATH = Path(__file__).resolve().parent / "process_categories.json"
_TOP_N = 10


def _load_categories() -> dict[str, str]:
    try:
        with open(_CATEGORIES_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        name_to_category = {}
        for category, names in raw.items():
            for name in names:
                name_to_category[name.lower()] = category
        return name_to_category
    except Exception:
        return {}


def analyze_process_usage(logs, top_n: int = _TOP_N) -> dict:
    name_to_category = _load_categories()
    total_snapshots = len(logs)

    appearance: dict[str, int]    = defaultdict(int)
    cpu_sum:    dict[str, float]   = defaultdict(float)
    cpu_cnt:    dict[str, int]     = defaultdict(int)
    mem_sum:    dict[str, float]   = defaultdict(float)
    mem_cnt:    dict[str, int]     = defaultdict(int)

    for log in logs:
        seen = set()
        for proc in log.get("processes", []):
            name = (proc.get("name") or "").lower()
            if not name or name in seen:
                continue
            seen.add(name)
            appearance[name] += 1

            cpu = proc.get("cpu_percent")
            if cpu is not None:
                cpu_sum[name] += cpu
                cpu_cnt[name] += 1

            mem = proc.get("memory_mb")
            if mem is not None:
                mem_sum[name] += mem
                mem_cnt[name] += 1

    def _stats(name):
        return {
            "appearance_count": appearance[name],
            "appearance_ratio": appearance[name] / total_snapshots if total_snapshots > 0 else 0,
            "avg_cpu_percent":  cpu_sum[name] / cpu_cnt[name] if cpu_cnt[name] > 0 else None,
            "avg_memory_mb":    mem_sum[name] / mem_cnt[name] if mem_cnt[name] > 0 else None,
            "category":         name_to_category.get(name, "etc"),
        }

    all_stats = {name: _stats(name) for name in appearance}

    top_by_frequency = _top(all_stats, "appearance_ratio", top_n)
    top_by_cpu       = _top(
        {n: s for n, s in all_stats.items() if s["avg_cpu_percent"] is not None},
        "avg_cpu_percent", top_n,
    )
    top_by_memory    = _top(
        {n: s for n, s in all_stats.items() if s["avg_memory_mb"] is not None},
        "avg_memory_mb", top_n,
    )

    category_summary: dict[str, int] = defaultdict(int)
    for name, stats in all_stats.items():
        category_summary[stats["category"]] += stats["appearance_count"]

    return {
        "top_by_frequency": top_by_frequency,
        "top_by_cpu":       top_by_cpu,
        "top_by_memory":    top_by_memory,
        "category_summary": dict(category_summary),
    }


def _top(stats: dict, key: str, n: int) -> list[dict]:
    ranked = sorted(stats.items(), key=lambda x: x[1][key], reverse=True)[:n]
    return [{"name": name, **s} for name, s in ranked]
