import pytest
from src.analysis.score_ram import score_ram


def _ram(p80=0.0, high_load_ratio=0.0, max_sustained_min=0.0):
    return {
        "raw": {"percentile_80": p80},
        "high_load_ratio": high_load_ratio,
        "max_sustained_high_load_minutes": max_sustained_min,
    }


class TestScoreRamGrade:
    def test_low_when_all_zero(self):
        assert score_ram(_ram())["grade"] == "low"

    def test_low_below_thresholds(self):
        assert score_ram(_ram(p80=60.0, high_load_ratio=0.05))["grade"] == "low"

    def test_medium_by_p80(self):
        assert score_ram(_ram(p80=78.0))["grade"] == "medium"

    def test_medium_by_high_load_ratio(self):
        assert score_ram(_ram(high_load_ratio=0.12))["grade"] == "medium"

    def test_high_by_p80_and_ratio(self):
        assert score_ram(_ram(p80=88.0, high_load_ratio=0.25))["grade"] == "high"

    def test_high_by_sustained_alone(self):
        assert score_ram(_ram(max_sustained_min=35.0))["grade"] == "high"


class TestScoreRamScore:
    def test_zero_input_gives_zero_score(self):
        assert score_ram(_ram())["score"] == 0.0

    def test_score_capped_at_one(self):
        result = score_ram(_ram(p80=100.0, high_load_ratio=1.0, max_sustained_min=120.0))
        assert result["score"] <= 1.0

    def test_score_increases_with_load(self):
        low  = score_ram(_ram(p80=40.0, high_load_ratio=0.05))["score"]
        high = score_ram(_ram(p80=90.0, high_load_ratio=0.40))["score"]
        assert high > low

    def test_sustained_cap_at_60_minutes(self):
        s60  = score_ram(_ram(max_sustained_min=60.0))["score"]
        s120 = score_ram(_ram(max_sustained_min=120.0))["score"]
        assert s60 == s120


class TestScoreRamEdgeCases:
    def test_none_values(self):
        result = score_ram({"raw": None, "high_load_ratio": None})
        assert result["score"] == 0.0
        assert result["grade"] == "low"

    def test_empty_dict(self):
        result = score_ram({})
        assert result["score"] == 0.0
