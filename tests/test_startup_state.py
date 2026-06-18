from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from src.startup_state import StartupState, detect_startup_state, is_analysis_period_elapsed


def _iso(dt):
    return dt.isoformat()


class TestIsAnalysisPeriodElapsed:
    def test_not_elapsed_when_within_period(self):
        first_ts = _iso(datetime.now(timezone.utc) - timedelta(days=1))
        assert is_analysis_period_elapsed({"analysis_days": 7}, first_ts) is False

    def test_elapsed_when_past_period(self):
        first_ts = _iso(datetime.now(timezone.utc) - timedelta(days=8))
        assert is_analysis_period_elapsed({"analysis_days": 7}, first_ts) is True

    def test_exactly_at_boundary_counts_as_elapsed(self):
        first_ts = _iso(datetime.now(timezone.utc) - timedelta(days=7))
        assert is_analysis_period_elapsed({"analysis_days": 7}, first_ts) is True

    def test_missing_analysis_days_defaults_to_seven(self):
        first_ts = _iso(datetime.now(timezone.utc) - timedelta(days=8))
        assert is_analysis_period_elapsed({}, first_ts) is True

    def test_invalid_timestamp_raises(self):
        import pytest
        with pytest.raises(Exception):
            is_analysis_period_elapsed({"analysis_days": 7}, "not-a-timestamp")


class TestDetectStartupState:
    @patch("src.startup_state.read_user_profile")
    def test_no_profile_is_fresh(self, mock_profile):
        mock_profile.return_value = None
        assert detect_startup_state() == StartupState.FRESH

    @patch("src.startup_state.get_usage_log_first_timestamp")
    @patch("src.startup_state.read_user_profile")
    def test_no_log_yet_is_fresh(self, mock_profile, mock_first_ts):
        mock_profile.return_value = {"analysis_days": 7}
        mock_first_ts.return_value = None
        assert detect_startup_state() == StartupState.FRESH

    @patch("src.startup_state.get_usage_log_first_timestamp")
    @patch("src.startup_state.read_user_profile")
    def test_within_period_is_resume(self, mock_profile, mock_first_ts):
        mock_profile.return_value = {"analysis_days": 7}
        mock_first_ts.return_value = _iso(datetime.now(timezone.utc) - timedelta(days=1))
        assert detect_startup_state() == StartupState.RESUME

    @patch("src.startup_state.get_usage_log_first_timestamp")
    @patch("src.startup_state.read_user_profile")
    def test_period_elapsed_is_analyze(self, mock_profile, mock_first_ts):
        mock_profile.return_value = {"analysis_days": 3}
        mock_first_ts.return_value = _iso(datetime.now(timezone.utc) - timedelta(days=4))
        assert detect_startup_state() == StartupState.ANALYZE

    @patch("src.startup_state.get_usage_log_first_timestamp")
    @patch("src.startup_state.read_user_profile")
    def test_corrupted_timestamp_falls_back_to_fresh(self, mock_profile, mock_first_ts):
        mock_profile.return_value = {"analysis_days": 7}
        mock_first_ts.return_value = "garbage"
        assert detect_startup_state() == StartupState.FRESH
