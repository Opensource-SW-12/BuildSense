import json
from datetime import datetime, timedelta
from pathlib import Path
from src.config import ANALYSIS_DIR

def parse_utc_to_kst(timestamp):
    try:
        if not timestamp:
            return None

        utc_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return utc_time + timedelta(hours=9)

    except ValueError as error:
        print(f"[timestamp 오류] 올바르지 않은 timestamp 형식입니다: {timestamp}, {error}")
        return None

    except TypeError as error:
        print(f"[timestamp 오류] timestamp 값 타입이 올바르지 않습니다: {timestamp}, {error}")
        return None


def classify_time_period(kst_time):
    hour = kst_time.hour

    if 0 <= hour <= 5:
        return "dawn"
    if 6 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 17:
        return "afternoon"
    return "evening"


def classify_weekday(kst_time):
    if kst_time.weekday() < 5:
        return "weekday"
    return "weekend"


def analyze_time_patterns(logs):
    time_period_count = {
        "dawn": 0,
        "morning": 0,
        "afternoon": 0,
        "evening": 0
    }

    weekday_count = {
        "weekday": 0,
        "weekend": 0
    }

    parsed_times = []

    for log in logs:
        timestamp = log.get("timestamp")

        if not timestamp:
            continue

        kst_time = parse_utc_to_kst(timestamp)

        if kst_time is None:
            continue

        parsed_times.append(kst_time)

        time_period = classify_time_period(kst_time)
        weekday_type = classify_weekday(kst_time)

        time_period_count[time_period] += 1
        weekday_count[weekday_type] += 1

    return {
        "time_period_count": time_period_count,
        "weekday_count": weekday_count,
        "parsed_times": parsed_times
    }


def calculate_active_snapshot_ratio(parsed_times, interval_seconds=60):
    if len(parsed_times) < 2:
        return 0

    total_seconds = (parsed_times[-1] - parsed_times[0]).total_seconds()
    expected_snapshot_count = int(total_seconds / interval_seconds) + 1

    if expected_snapshot_count <= 0:
        return 0

    return len(parsed_times) / expected_snapshot_count


def calculate_continuous_usage_segments(parsed_times):
    if not parsed_times:
        return []

    segments = []
    current_segment = [parsed_times[0]]

    for index in range(1, len(parsed_times)):
        gap_seconds = (parsed_times[index] - parsed_times[index - 1]).total_seconds()

        if gap_seconds >= 7200:
            segments.append(current_segment)
            current_segment = [parsed_times[index]]
        else:
            current_segment.append(parsed_times[index])

    segments.append(current_segment)

    return segments


def calculate_inactive_segments(parsed_times):
    if len(parsed_times) < 2:
        return []

    inactive = []

    for index in range(1, len(parsed_times)):
        gap_seconds = (parsed_times[index] - parsed_times[index - 1]).total_seconds()

        if gap_seconds >= 7200:
            inactive.append({
                "start": parsed_times[index - 1].isoformat(),
                "end":   parsed_times[index].isoformat(),
                "duration_hours": round(gap_seconds / 3600, 2),
            })

    return inactive


def calculate_average_continuous_usage_hours(parsed_times):
    segments = calculate_continuous_usage_segments(parsed_times)

    if not segments:
        return 0

    durations = []

    for segment in segments:
        if len(segment) < 2:
            durations.append(0)
        else:
            duration_hours = (segment[-1] - segment[0]).total_seconds() / 3600
            durations.append(duration_hours)

    return sum(durations) / len(durations)


def analyze_uptime(logs, interval_seconds: int = 60):
    """실제 모니터링 스냅샷 타임스탬프로 일 평균 가동 시간을 계산한다.

    uptime_seconds(부팅 후 경과 시간)는 절전 시간을 포함하므로 사용하지 않는다.
    대신 스냅샷 간격과 연속 세그먼트 분리(2h 간격)로 실제 사용 시간만 집계한다.
    """
    parsed_times = sorted(filter(None, [
        parse_utc_to_kst(log.get("timestamp")) for log in logs
    ]))

    if not parsed_times:
        return {"average_uptime_hours": 0, "long_usage_ratio": 0}

    segments = calculate_continuous_usage_segments(parsed_times)

    def _segment_hours(seg):
        # 세그먼트 지속 시간 = 타임스탬프 차 + 마지막 스냅샷 1 interval
        if len(seg) < 2:
            return interval_seconds / 3600
        return (seg[-1] - seg[0]).total_seconds() / 3600 + interval_seconds / 3600

    durations = [_segment_hours(seg) for seg in segments]
    total_active_hours = sum(durations)

    # 분석 기간(일) — 최소 1일로 clamp해 단일 세션 0 나눗셈 방지
    analysis_days = max(
        (parsed_times[-1] - parsed_times[0]).total_seconds() / 86400,
        1.0,
    )
    average_uptime_hours = total_active_hours / analysis_days

    # long_usage_ratio: 4시간 이상 세션에 속한 스냅샷 비율.
    # 세그먼트는 2시간 이상 공백에서 끊기므로, 8시간 기준은 "중간에 2시간
    # 이상 쉬는 일이 전혀 없는 하루"를 요구해 거의 항상 0이 되어버렸다.
    # 4시간은 끊김 없는 장시간 사용을 의미 있게 포착하면서도 실제로 도달 가능하다.
    _LONG_SESSION_HOURS = 4.0
    long_snapshots = sum(
        len(seg) for seg, dur in zip(segments, durations) if dur >= _LONG_SESSION_HOURS
    )
    long_usage_ratio = long_snapshots / len(parsed_times)

    return {
        "average_uptime_hours": average_uptime_hours,
        "long_usage_ratio": long_usage_ratio,
    }


def create_usage_pattern_summary(logs):
    time_analysis = analyze_time_patterns(logs)
    sorted_times = sorted(time_analysis["parsed_times"])

    return {
        "time_period_count": time_analysis["time_period_count"],
        "weekday_count": time_analysis["weekday_count"],
        "active_snapshot_ratio": calculate_active_snapshot_ratio(sorted_times),
        "average_continuous_usage_hours": calculate_average_continuous_usage_hours(sorted_times),
        "inactive_segments": calculate_inactive_segments(sorted_times),
        "uptime": analyze_uptime(logs),
    }


def save_normalized_usage(result, output_filename="normalized_usage.json"):
    output_path = Path(ANALYSIS_DIR) / output_filename

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)