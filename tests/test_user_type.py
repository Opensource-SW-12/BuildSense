import pytest
from src.analysis.user_type import classify_user_type, _apply_hardware_boosts, _category_base_scores


def _analysis(category_summary, gpu_high_load=0.0, cpu_episodes=0, vram_p80=0.0):
    return {
        "process_usage": {"category_summary": category_summary},
        "resource_usage": {
            "cpu": {"sustained_high_load": {"episode_count": cpu_episodes}},
            "gpu": {"high_load_ratio": gpu_high_load},
            "vram": {"usage_percent": {"raw": {"percentile_80": vram_p80}}},
        },
    }


class TestCategoryBaseScores:
    def test_noise_categories_filtered(self):
        scores = _category_base_scores({"browser": 100, "game": 200, "etc": 50}, total_snapshots=350)
        assert "browser" not in scores
        assert "etc" not in scores
        assert "game" in scores

    def test_scores_sum_to_one(self):
        scores = _category_base_scores({"game": 300, "creative": 100, "development": 100}, total_snapshots=500)
        assert abs(sum(scores.values()) - 1.0) < 1e-9

    def test_empty_returns_empty(self):
        assert _category_base_scores({}, total_snapshots=100) == {}

    def test_all_noise_returns_empty(self):
        assert _category_base_scores({"browser": 100, "etc": 200}, total_snapshots=300) == {}


class TestApplyHardwareBoosts:
    def test_gpu_boost_only_when_game_present(self):
        scores = {"creative": 1.0}
        boosted = _apply_hardware_boosts(scores, {"gpu_high_load_ratio": 0.9, "cpu_sustained_episodes": 0, "vram_p80": 0.0})
        assert "game" not in boosted

    def test_gpu_boost_applied_when_game_present(self):
        scores = {"game": 0.5}
        boosted = _apply_hardware_boosts(scores, {"gpu_high_load_ratio": 0.9, "cpu_sustained_episodes": 0, "vram_p80": 0.0})
        assert boosted["game"] > 0.5

    def test_vram_boost_only_when_game_present(self):
        scores = {"creative": 0.8}
        boosted = _apply_hardware_boosts(scores, {"gpu_high_load_ratio": 0.0, "cpu_sustained_episodes": 0, "vram_p80": 80.0})
        assert "game" not in boosted

    def test_cpu_boost_creates_development_if_absent(self):
        scores = {"game": 0.5}
        boosted = _apply_hardware_boosts(scores, {"gpu_high_load_ratio": 0.0, "cpu_sustained_episodes": 3, "vram_p80": 0.0})
        assert "development" in boosted

    def test_scores_capped_at_one(self):
        scores = {"game": 0.95}
        boosted = _apply_hardware_boosts(scores, {"gpu_high_load_ratio": 0.9, "cpu_sustained_episodes": 0, "vram_p80": 90.0})
        assert boosted["game"] <= 1.0


class TestClassifyUserType:
    def test_game_dominant(self):
        analysis = _analysis({"game": 800, "browser": 100})
        result = classify_user_type(analysis, total_snapshots=900)
        assert result["user_type"][0] == "game"

    def test_creative_dominant(self):
        analysis = _analysis({"creative": 600, "game": 100})
        result = classify_user_type(analysis, total_snapshots=700)
        assert result["user_type"][0] == "creative"

    def test_no_game_from_gpu_alone(self):
        # 게임 프로세스 없이 GPU만 높아도 game 타입 생성 안 됨
        analysis = _analysis({"creative": 500}, gpu_high_load=0.9)
        result = classify_user_type(analysis, total_snapshots=500)
        assert "game" not in result["user_type"]

    def test_game_boosted_when_game_exists_and_gpu_high(self):
        analysis = _analysis({"game": 300, "creative": 300}, gpu_high_load=0.9)
        result = classify_user_type(analysis, total_snapshots=600)
        assert "game" in result["user_type"]
        assert result["category_scores"]["game"] > 0.5

    def test_browser_and_etc_filtered_out(self):
        analysis = _analysis({"browser": 900, "etc": 900})
        result = classify_user_type(analysis, total_snapshots=1800)
        assert result["user_type"] == []

    def test_presence_threshold_filters_minor(self):
        # creative=950, game=50 → game 비율 0.05 < 0.10 threshold → 제외
        analysis = _analysis({"creative": 950, "game": 50})
        result = classify_user_type(analysis, total_snapshots=1000)
        assert "game" not in result["user_type"]

    def test_result_sorted_by_score_descending(self):
        analysis = _analysis({"game": 500, "creative": 300, "development": 200})
        result = classify_user_type(analysis, total_snapshots=1000)
        scores = result["category_scores"]
        types  = result["user_type"]
        for i in range(len(types) - 1):
            assert scores[types[i]] >= scores[types[i + 1]]

    def test_hardware_signals_in_result(self):
        analysis = _analysis({"game": 500}, gpu_high_load=0.5, cpu_episodes=2)
        result = classify_user_type(analysis, total_snapshots=500)
        assert result["hardware_signals"]["gpu_high_load_ratio"] == 0.5
        assert result["hardware_signals"]["cpu_sustained_episodes"] == 2
