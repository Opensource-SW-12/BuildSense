import pytest
from src.analysis.score_gpu_vram import score_gpu_vram


def _gpu(p80=0.0, high_load_ratio=0.0, not_detected_ratio=0.0):
    return {
        "raw": {"percentile_80": p80},
        "high_load_ratio": high_load_ratio,
        "gpu_not_detected_ratio": not_detected_ratio,
    }


def _vram(p80=0.0, high_load_ratio=0.0):
    return {
        "usage_percent": {"raw": {"percentile_80": p80}},
        "high_load_ratio": high_load_ratio,
    }


class TestScoreGpuGrade:
    def test_low_when_all_zero(self):
        assert score_gpu_vram(_gpu(), _vram())["grade"] == "low"

    def test_high_by_gpu_p80(self):
        assert score_gpu_vram(_gpu(p80=90.0), _vram())["grade"] == "high"

    def test_high_by_gpu_high_load(self):
        assert score_gpu_vram(_gpu(high_load_ratio=0.45), _vram())["grade"] == "high"

    def test_high_by_vram_p80(self):
        assert score_gpu_vram(_gpu(), _vram(p80=90.0))["grade"] == "high"

    def test_medium_by_gpu_p80(self):
        assert score_gpu_vram(_gpu(p80=72.0), _vram())["grade"] == "medium"

    def test_medium_by_vram_p80(self):
        assert score_gpu_vram(_gpu(), _vram(p80=72.0))["grade"] == "medium"

    def test_unknown_when_not_detected(self):
        result = score_gpu_vram(_gpu(not_detected_ratio=0.95), _vram())
        assert result["grade"] == "unknown"
        assert result["score"] == 0.0


class TestScoreGpuScore:
    def test_zero_input_gives_zero_score(self):
        assert score_gpu_vram(_gpu(), _vram())["score"] == 0.0

    def test_score_capped_at_one(self):
        result = score_gpu_vram(_gpu(p80=100.0, high_load_ratio=1.0), _vram(p80=100.0, high_load_ratio=1.0))
        assert result["score"] <= 1.0

    def test_score_increases_with_load(self):
        low  = score_gpu_vram(_gpu(p80=30.0), _vram())["score"]
        high = score_gpu_vram(_gpu(p80=90.0, high_load_ratio=0.5), _vram(p80=80.0))["score"]
        assert high > low

    def test_no_vram_uses_gpu_only_weight(self):
        result = score_gpu_vram(_gpu(p80=100.0, high_load_ratio=1.0), _vram())
        assert result["score"] == 1.0

    def test_unknown_returns_none_factors(self):
        result = score_gpu_vram(_gpu(not_detected_ratio=1.0), _vram())
        assert result["factors"]["gpu_p80_percent"] is None


class TestScoreGpuEdgeCases:
    def test_none_gpu_values(self):
        result = score_gpu_vram({"raw": None, "high_load_ratio": None}, _vram())
        assert result["score"] == 0.0

    def test_empty_dicts(self):
        result = score_gpu_vram({}, {})
        assert result["score"] == 0.0
