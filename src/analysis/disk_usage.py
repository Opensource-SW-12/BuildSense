from collections import Counter

from src.normalization.core import calculate_basic_stats


def _mode(values):
    if not values:
        return None
    return Counter(round(v, 1) for v in values).most_common(1)[0][0]


def _free_stats(values):
    valid = [v for v in values if v is not None]
    if not valid:
        return {"min": None, "average": None, "median": None}
    sorted_v = sorted(valid)
    return {
        "min": sorted_v[0],
        "average": sum(valid) / len(valid),
        "median": sorted_v[len(sorted_v) // 2],
    }


def analyze_disk_usage(logs):
    drive_snapshots: dict[str, list[dict]] = {}

    for log in logs:
        for disk in log.get("disks", []):
            mp = disk.get("mountpoint")
            if not mp:
                continue
            drive_snapshots.setdefault(mp, []).append(disk)

    result = {}
    for mountpoint, snapshots in drive_snapshots.items():
        total_values   = [s["total_gb"]  for s in snapshots if s.get("total_gb")  is not None]
        used_values    = [s["used_gb"]   for s in snapshots if s.get("used_gb")   is not None]
        free_values    = [s["free_gb"]   for s in snapshots if s.get("free_gb")   is not None]
        percent_values = [s["percent"]   for s in snapshots if s.get("percent")   is not None]

        total_snapshots = len(snapshots)
        danger_count = sum(1 for p in percent_values if p >= 90)

        result[mountpoint] = {
            "total_gb": _mode(total_values),
            "used_gb_stats": calculate_basic_stats(used_values),
            "free_gb_stats": _free_stats(free_values),
            "percent_stats": calculate_basic_stats(percent_values),
            "danger_ratio": danger_count / total_snapshots if total_snapshots > 0 else 0,
        }

    return result
