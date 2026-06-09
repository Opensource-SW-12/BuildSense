import pytest
from src.analysis.score_psu import score_psu


def _pattern(avg_hours=0.0, long_ratio=0.0):
    return {"uptime": {"average_uptime_hours": avg_hours, "long_usage_ratio": long_ratio}}


class TestScorePsuGrade:
    def test_gold_when_low_usage(self):
        assert score_psu(_pattern(avg_hours=4.0))["grade"] == "gold"

    def test_gold_at_boundary(self):
        assert score_psu(_pattern(avg_hours=7.9))["grade"] == "gold"

    def test_platinum_at_8_hours(self):
        assert score_psu(_pattern(avg_hours=8.0))["grade"] == "platinum"

    def test_platinum_in_range(self):
        assert score_psu(_pattern(avg_hours=14.0))["grade"] == "platinum"

    def test_titanium_at_20_hours(self):
        assert score_psu(_pattern(avg_hours=20.0))["grade"] == "titanium"

    def test_titanium_above_threshold(self):
        assert score_psu(_pattern(avg_hours=23.0))["grade"] == "titanium"


class TestScorePsuScore:
    def test_zero_gives_zero_score(self):
        assert score_psu(_pattern())["score"] == 0.0

    def test_score_capped_at_one(self):
        result = score_psu(_pattern(avg_hours=24.0, long_ratio=1.0))
        assert result["score"] <= 1.0

    def test_score_increases_with_hours(self):
        low  = score_psu(_pattern(avg_hours=2.0))["score"]
        high = score_psu(_pattern(avg_hours=20.0))["score"]
        assert high > low

    def test_long_ratio_contributes_to_score(self):
        without = score_psu(_pattern(avg_hours=10.0, long_ratio=0.0))["score"]
        with_   = score_psu(_pattern(avg_hours=10.0, long_ratio=0.5))["score"]
        assert with_ > without


class TestScorePsuEdgeCases:
    def test_empty_dict(self):
        result = score_psu({})
        assert result["score"] == 0.0
        assert result["grade"] == "gold"

    def test_none_uptime(self):
        result = score_psu({"uptime": None})
        assert result["score"] == 0.0
