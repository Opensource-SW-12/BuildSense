import pytest
from src.pricing.passmark_tiering import (
    normalize_text,
    parse_price_usd,
    calculate_performance_tier,
    calculate_cpu_tier,
    calculate_gpu_tier,
    CPU_MAX_SCORE,
    GPU_MAX_SCORE,
    MAX_TIER,
)


class TestNormalizeText:
    def test_lowercase(self):
        assert normalize_text("Intel Core i9") == "intel core i9"

    def test_special_chars_removed(self):
        assert normalize_text("RTX 4090 (Ti)") == "rtx 4090 ti"

    def test_none_returns_empty(self):
        assert normalize_text(None) == ""

    def test_multiple_spaces_collapsed(self):
        assert normalize_text("Core   i7   12700K") == "core i7 12700k"

    def test_korean_preserved(self):
        result = normalize_text("삼성 DDR5")
        assert "삼성" in result


class TestParsePriceUsd:
    def test_valid_price(self):
        assert parse_price_usd("$1,299.99") == 1299.99

    def test_na_string(self):
        assert parse_price_usd("NA") == "NA"

    def test_none(self):
        assert parse_price_usd(None) == "NA"

    def test_empty_string(self):
        assert parse_price_usd("") == "NA"

    def test_plain_number(self):
        assert parse_price_usd("599") == 599.0

    def test_invalid_string(self):
        assert parse_price_usd("N/A price") == "NA"


class TestCalculatePerformanceTier:
    def test_max_score_gives_max_tier(self):
        assert calculate_performance_tier(CPU_MAX_SCORE, CPU_MAX_SCORE) == MAX_TIER

    def test_zero_score_gives_tier_zero_clamped_to_one(self):
        # int(0/max * 29) = 0 → clamped to 1
        assert calculate_performance_tier(1, CPU_MAX_SCORE) == 1

    def test_half_score_gives_half_tier(self):
        result = calculate_performance_tier(CPU_MAX_SCORE // 2, CPU_MAX_SCORE)
        assert result == MAX_TIER // 2

    def test_none_score_returns_none(self):
        assert calculate_performance_tier(None, CPU_MAX_SCORE) is None

    def test_na_score_returns_none(self):
        assert calculate_performance_tier("NA", CPU_MAX_SCORE) is None

    def test_score_above_max_clamped(self):
        assert calculate_performance_tier(CPU_MAX_SCORE * 2, CPU_MAX_SCORE) == MAX_TIER

    def test_zero_max_score_returns_none(self):
        assert calculate_performance_tier(1000, 0) is None

    def test_comma_in_score_string(self):
        assert calculate_performance_tier("40,000", CPU_MAX_SCORE) is not None


class TestCpuGpuTier:
    def test_cpu_tier_uses_cpu_max(self):
        tier = calculate_cpu_tier(CPU_MAX_SCORE)
        assert tier == MAX_TIER

    def test_gpu_tier_uses_gpu_max(self):
        tier = calculate_gpu_tier(GPU_MAX_SCORE)
        assert tier == MAX_TIER

    def test_same_score_different_tier_by_max(self):
        score = 20000
        cpu_tier = calculate_cpu_tier(score)
        gpu_tier = calculate_gpu_tier(score)
        # GPU max(41588) < CPU max(80000) → same score → higher GPU tier
        assert gpu_tier > cpu_tier

    def test_tier_in_valid_range(self):
        for score in [1000, 10000, 30000, 60000, 80000]:
            t = calculate_cpu_tier(score)
            assert 1 <= t <= MAX_TIER
