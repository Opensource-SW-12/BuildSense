from src.analysis.score_disk_base import capacity_score

_HDD_FLOOR = 0.3

# 규칙 기반 grade 임계값
# HDD 존재 자체가 SSD 교체 신호 → 기본 medium 보장
# 용량 문제까지 겹치면 high
_HIGH_P80_THRESHOLD    = 70.0
_HIGH_DANGER_THRESHOLD = 0.10


def _grade(percent_p80: float, danger_ratio: float) -> str:
    if percent_p80 >= _HIGH_P80_THRESHOLD or danger_ratio >= _HIGH_DANGER_THRESHOLD:
        return "high"
    return "medium"  # HDD 존재 자체 = 최소 medium


def _score_drive(drive: dict) -> float:
    return round(min(max(capacity_score(drive), _HDD_FLOOR), 1.0), 4)


def _grade_drive(drive: dict) -> str:
    percent_p80  = (drive.get("percent_stats") or {}).get("percentile_80") or 0.0
    danger_ratio = drive.get("danger_ratio") or 0.0
    return _grade(percent_p80, danger_ratio)


def score_hdd(disk_usage: dict) -> dict | None:
    """
    disk_usage: result["disk_usage"] from analyze_disk_usage()
    HDD 드라이브만 스코어링. HDD 존재 자체 = 최소 medium.
    score — 연속값 (강도 측정 / 세션 간 비교용)
    grade — 규칙 기반 (업그레이드 추천 결정 기준)
    HDD 드라이브가 없으면 None 반환.
    """
    hdd_drives = {
        mp: drive for mp, drive in disk_usage.items()
        if drive.get("drive_type") == "HDD"
    }
    if not hdd_drives:
        return None

    drive_scores = {
        mp: {
            "score":      _score_drive(drive),
            "grade":      _grade_drive(drive),
            "drive_type": "HDD",
        }
        for mp, drive in hdd_drives.items()
    }

    worst = max(drive_scores.values(), key=lambda d: d["score"])

    return {
        "score":        worst["score"],
        "grade":        worst["grade"],
        "drive_scores": drive_scores,
    }
