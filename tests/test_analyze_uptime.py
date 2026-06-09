"""
analyze_uptime 테스트 — 절전 시간 제외 여부 및 일 평균 가동 시간 계산 검증.
"""
import pytest
from datetime import datetime, timedelta, timezone
from src.analysis.usage_pattern_summary import analyze_uptime

_BASE = datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc)


def _ts(offset_minutes: float) -> str:
    return (_BASE + timedelta(minutes=offset_minutes)).isoformat()


def _logs(offsets_minutes, uptime_seconds=None):
    """offsets_minutes: 분 단위 오프셋 목록 → 스냅샷 생성."""
    logs = []
    for i, m in enumerate(offsets_minutes):
        log = {"timestamp": _ts(m)}
        if uptime_seconds is not None:
            log["uptime_seconds"] = uptime_seconds[i] if hasattr(uptime_seconds, "__iter__") else uptime_seconds
        logs.append(log)
    return logs


class TestAnalyzeUptimeBasic:
    def test_empty_logs(self):
        result = analyze_uptime([])
        assert result["average_uptime_hours"] == 0
        assert result["long_usage_ratio"] == 0

    def test_single_snapshot(self):
        result = analyze_uptime(_logs([0]))
        assert result["average_uptime_hours"] > 0

    def test_continuous_session_duration(self):
        # 0~119분 (2시간) 연속 → 세션 1개
        offsets = list(range(0, 120, 1))
        result = analyze_uptime(_logs(offsets))
        # 분석 기간 < 1일 → 1일로 clamp, 세션 ~2시간
        assert 1.5 < result["average_uptime_hours"] < 3.0


class TestAnalyzeUptimeSleepExclusion:
    def test_sleep_gap_excluded(self):
        """절전(2시간+ 공백) 구간은 가동 시간에 포함되지 않아야 한다."""
        # 세션 A: 0~59분 (1시간), 절전 6시간, 세션 B: 420~479분 (1시간)
        session_a = list(range(0, 60, 1))
        session_b = list(range(420, 480, 1))
        logs = _logs(session_a + session_b)
        result = analyze_uptime(logs)
        # 총 가동 시간 ≈ 2시간, 분석 기간 ≈ 8시간(0.33일) → clamp 1일
        # average ≈ 2 / 1 = 2시간 (6시간 절전 제외)
        assert result["average_uptime_hours"] < 4.0

    def test_sleep_not_counted_as_long_session(self):
        """절전 포함 부팅 시간이 길어도 세션이 짧으면 long_usage_ratio = 0."""
        # 짧은 세션(30분), uptime_seconds=20*3600(20시간)으로 잘못된 데이터 포함
        logs = _logs(list(range(0, 30, 1)), uptime_seconds=72000)
        result = analyze_uptime(logs)
        assert result["long_usage_ratio"] == 0.0


class TestAnalyzeUptimeLongRatio:
    def test_long_session_detected(self):
        """9시간 연속 세션 → long_usage_ratio = 1.0."""
        offsets = list(range(0, 541, 1))  # 0~540분 = 9시간
        result = analyze_uptime(_logs(offsets))
        assert result["long_usage_ratio"] == 1.0

    def test_short_session_not_long(self):
        """4시간 세션 → long_usage_ratio = 0."""
        offsets = list(range(0, 240, 1))
        result = analyze_uptime(_logs(offsets))
        assert result["long_usage_ratio"] == 0.0

    def test_mixed_sessions(self):
        """긴 세션(9h) + 짧은 세션(1h) → long_ratio는 긴 세션 스냅샷 비율."""
        long_session  = list(range(0, 541, 1))    # 541 스냅샷
        short_session = list(range(1000, 1060, 1)) # 60 스냅샷 (2h+ 공백으로 분리)
        result = analyze_uptime(_logs(long_session + short_session))
        expected = 541 / (541 + 60)
        assert abs(result["long_usage_ratio"] - expected) < 0.01


class TestAnalyzeUptimeDailyAverage:
    def test_daily_average_multiday(self):
        """이틀에 걸쳐 하루 2시간씩 사용 → average ≈ 2시간."""
        # day1: 0~119분, day2: 1440~1559분 (24h + 0~119분)
        day1 = list(range(0, 120, 1))
        day2 = list(range(1440, 1560, 1))
        result = analyze_uptime(_logs(day1 + day2))
        # 분석 기간 ≈ 26시간 = 1.08일, 총 가동 ≈ 4시간 → 평균 ≈ 3.7시간
        assert 2.0 < result["average_uptime_hours"] < 5.0
