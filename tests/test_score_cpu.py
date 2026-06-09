import pytest
from src.analysis.score_cpu import score_cpu


def _cpu(p80=0.0, high_load_ratio=0.0, episodes=0):
    return {
        "raw": {"percentile_80": p80},
        "high_load_ratio": high_load_ratio,
        "sustained_high_load": {"episode_count": episodes},
    }


class TestScoreCpuGrade:
    def test_low_when_all_zero(self):
        assert score_cpu(_cpu())["grade"] == "low"

    def test_low_below_thresholds(self):
        assert score_cpu(_cpu(p80=50.0, high_load_ratio=0.10))["grade"] == "low"

    def test_medium_by_p80(self):
        assert score_cpu(_cpu(p80=65.0))["grade"] == "medium"

    def test_medium_by_high_load_ratio(self):
        assert score_cpu(_cpu(high_load_ratio=0.20))["grade"] == "medium"

    def test_high_by_both_p80_and_ratio(self):
        assert score_cpu(_cpu(p80=85.0, high_load_ratio=0.35))["grade"] == "high"

    def test_high_by_episodes_alone(self):
        assert score_cpu(_cpu(episodes=3))["grade"] == "high"

    def test_high_episodes_overrides_low_usage(self):
        assert score_cpu(_cpu(p80=10.0, high_load_ratio=0.01, episodes=5))["grade"] == "high"


class TestScoreCpuScore:
    def test_zero_input_gives_zero_score(self):
        assert score_cpu(_cpu())["score"] == 0.0

    def test_score_increases_with_load(self):
        low  = score_cpu(_cpu(p80=30.0, high_load_ratio=0.10))["score"]
        high = score_cpu(_cpu(p80=90.0, high_load_ratio=0.50))["score"]
        assert high > low

    def test_score_capped_at_one(self):
        assert score_cpu(_cpu(p80=100.0, high_load_ratio=1.0, episodes=10))["score"] <= 1.0

    def test_score_range(self):
        result = score_cpu(_cpu(p80=70.0, high_load_ratio=0.25, episodes=2))
        assert 0.0 <= result["score"] <= 1.0

    def test_episodes_capped_at_sustained_cap(self):
        s5  = score_cpu(_cpu(episodes=5))["score"]
        s10 = score_cpu(_cpu(episodes=10))["score"]
        assert s5 == s10  # _SUSTAINED_CAP=5 이상은 동일


class TestScoreCpuFactors:
    def test_factors_present(self):
        result = score_cpu(_cpu(p80=60.0, high_load_ratio=0.20, episodes=1))
        assert "p80_percent" in result["factors"]
        assert "high_load_ratio" in result["factors"]
        assert "sustained_episodes" in result["factors"]

    def test_factors_reflect_input(self):
        result = score_cpu(_cpu(p80=72.5, high_load_ratio=0.33, episodes=2))
        assert result["factors"]["p80_percent"] == 72.5
        assert result["factors"]["sustained_episodes"] == 2


class TestScoreCpuEdgeCases:
    def test_none_values_handled(self):
        result = score_cpu({"raw": None, "high_load_ratio": None, "sustained_high_load": None})
        assert result["score"] == 0.0
        assert result["grade"] == "low"

    def test_empty_dict(self):
        result = score_cpu({})
        assert result["score"] == 0.0
