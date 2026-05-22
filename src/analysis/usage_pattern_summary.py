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

    sorted_times = sorted(parsed_times)

    total_seconds = (sorted_times[-1] - sorted_times[0]).total_seconds()
    expected_snapshot_count = int(total_seconds / interval_seconds) + 1

    if expected_snapshot_count <= 0:
        return 0

    return len(sorted_times) / expected_snapshot_count


def calculate_continuous_usage_segments(parsed_times):
    if not parsed_times:
        return []

    sorted_times = sorted(parsed_times)

    segments = []
    current_segment = [sorted_times[0]]

    for index in range(1, len(sorted_times)):
        gap_seconds = (sorted_times[index] - sorted_times[index - 1]).total_seconds()

        if gap_seconds >= 7200:
            segments.append(current_segment)
            current_segment = [sorted_times[index]]
        else:
            current_segment.append(sorted_times[index])

    segments.append(current_segment)

    return segments


def calculate_inactive_segments(parsed_times):
    if len(parsed_times) < 2:
        return []

    sorted_times = sorted(parsed_times)
    inactive = []

    for index in range(1, len(sorted_times)):
        gap_seconds = (sorted_times[index] - sorted_times[index - 1]).total_seconds()

        if gap_seconds >= 7200:
            inactive.append({
                "start": sorted_times[index - 1].isoformat(),
                "end":   sorted_times[index].isoformat(),
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


def analyze_uptime(logs):
    uptime_values = [
        log.get("uptime_seconds")
        for log in logs
        if log.get("uptime_seconds") is not None
    ]

    if not uptime_values:
        return {
            "average_uptime_hours": 0,
            "long_usage_ratio": 0
        }

    average_uptime_hours = sum(uptime_values) / len(uptime_values) / 3600

    long_usage_count = sum(
        1 for value in uptime_values
        if value >= 8 * 3600
    )

    long_usage_ratio = long_usage_count / len(uptime_values)

    return {
        "average_uptime_hours": average_uptime_hours,
        "long_usage_ratio": long_usage_ratio
    }


def create_usage_pattern_summary(logs):
    time_analysis = analyze_time_patterns(logs)
    parsed_times = time_analysis["parsed_times"]

    return {
        "time_period_count": time_analysis["time_period_count"],
        "weekday_count": time_analysis["weekday_count"],
        "active_snapshot_ratio": calculate_active_snapshot_ratio(parsed_times),
        "average_continuous_usage_hours": calculate_average_continuous_usage_hours(parsed_times),
        "inactive_segments": calculate_inactive_segments(parsed_times),
        "uptime": analyze_uptime(logs),
    }


def save_normalized_usage(result, output_filename="normalized_usage.json"):
    output_path = Path(ANALYSIS_DIR) / output_filename

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)