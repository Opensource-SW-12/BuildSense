import json
from collections import defaultdict

from src.config import PROCESS_CATEGORIES_PATH, PROCESS_PATH_OVERRIDES_PATH

_CATEGORIES_PATH = PROCESS_CATEGORIES_PATH
_PATH_OVERRIDES_PATH = PROCESS_PATH_OVERRIDES_PATH
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


_CATEGORIES: dict[str, str] | None = None


def _get_categories() -> dict[str, str]:
    global _CATEGORIES
    if _CATEGORIES is None:
        _CATEGORIES = _load_categories()
    return _CATEGORIES


def _load_path_overrides() -> dict[str, list[tuple[str, str]]]:
    """프로세스 이름만으로 분류가 모호한 경우(javaw.exe 등) 실행 경로의
    키워드로 카테고리를 재지정한다. {process_name: [(path_keyword, category), ...]}"""
    try:
        with open(_PATH_OVERRIDES_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return {
            name.lower(): [(keyword.lower(), category) for keyword, category in rules]
            for name, rules in raw.items()
        }
    except Exception:
        return {}


_PATH_OVERRIDES: dict[str, list[tuple[str, str]]] | None = None


def _get_path_overrides() -> dict[str, list[tuple[str, str]]]:
    global _PATH_OVERRIDES
    if _PATH_OVERRIDES is None:
        _PATH_OVERRIDES = _load_path_overrides()
    return _PATH_OVERRIDES


def _resolve_category(name: str, exe: str, name_to_category: dict[str, str], path_overrides: dict[str, list[tuple[str, str]]]) -> str:
    for keyword, category in path_overrides.get(name, []):
        if keyword in exe:
            return category
    return name_to_category.get(name, "etc")


def analyze_process_usage(logs, top_n: int = _TOP_N, extra_categories: dict | None = None) -> dict:
    """extra_categories: {process_name_lower: category} — user_preferences의 수동 분류를 반영한다."""
    name_to_category = _get_categories()
    path_overrides = _get_path_overrides()
    _extra = {k.lower(): v for k, v in (extra_categories or {}).items()}
    total_snapshots = len(logs)

    appearance: dict[str, int]    = defaultdict(int)
    cpu_sum:    dict[str, float]   = defaultdict(float)
    cpu_cnt:    dict[str, int]     = defaultdict(int)
    mem_sum:    dict[str, float]   = defaultdict(float)
    mem_cnt:    dict[str, int]     = defaultdict(int)
    exe_path:   dict[str, str]     = {}

    for log in logs:
        seen = set()
        for proc in log.get("processes", []):
            name = (proc.get("name") or "").lower()
            if not name or name in seen:
                continue
            seen.add(name)
            appearance[name] += 1

            if name not in exe_path:
                exe_path[name] = (proc.get("exe") or "").lower()

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
            "category":         _extra.get(name) or _resolve_category(name, exe_path.get(name, ""), name_to_category, path_overrides),
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
