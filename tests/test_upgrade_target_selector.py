import pytest
from src.recommendation.upgrade_target_selector import select_upgrade_targets


def _scores(cpu_grade="low", gpu_grade="low", ram_grade="low",
            ssd_score=0.2, ssd_grade="low"):
    return {
        "cpu":      {"score": 0.3, "grade": cpu_grade},
        "ram":      {"score": 0.2, "grade": ram_grade},
        "gpu_vram": {"score": 0.4, "grade": gpu_grade},
        "ssd":      {"score": ssd_score, "grade": ssd_grade},
        "hdd":      None,
        "user_classification": {"user_type": []},
    }


def _profile(parts=None):
    default = {
        "CPU": {"option": "recommend"},
        "GPU": {"option": "recommend"},
        "RAM": {"option": "recommend"},
        "SSD": {"option": "recommend"},
        "HDD": {"option": "recommend"},
    }
    if parts:
        default.update(parts)
    return {"parts": default}


class TestSelectUpgradeTargetsFiltering:
    def test_low_grade_excluded(self):
        scores = _scores(cpu_grade="low", gpu_grade="low")
        result = select_upgrade_targets(scores, _profile(), None)
        parts = [t["part"] for t in result]
        assert "CPU" not in parts
        assert "GPU" not in parts

    def test_high_grade_included(self):
        scores = _scores(cpu_grade="high")
        result = select_upgrade_targets(scores, _profile(), None)
        assert any(t["part"] == "CPU" for t in result)

    def test_medium_grade_included(self):
        scores = _scores(ram_grade="medium")
        result = select_upgrade_targets(scores, _profile(), None)
        assert any(t["part"] == "RAM" for t in result)

    def test_exclude_option_skips_part(self):
        scores = _scores(cpu_grade="high")
        profile = _profile({"CPU": {"option": "exclude"}})
        result = select_upgrade_targets(scores, profile, None)
        assert not any(t["part"] == "CPU" for t in result)

    def test_keep_option_skips_part(self):
        scores = _scores(gpu_grade="high")
        profile = _profile({"GPU": {"option": "keep"}})
        result = select_upgrade_targets(scores, profile, None)
        assert not any(t["part"] == "GPU" for t in result)

    def test_none_score_skipped(self):
        scores = _scores()
        scores["hdd"] = None
        result = select_upgrade_targets(scores, _profile(), None)
        assert not any(t["part"] == "HDD" for t in result)


class TestSelectUpgradeTargetsPriority:
    def test_sorted_by_priority_descending(self):
        scores = _scores(cpu_grade="high", gpu_grade="medium", ram_grade="high")
        result = select_upgrade_targets(scores, _profile(), None)
        priorities = [t["priority"] for t in result]
        assert priorities == sorted(priorities, reverse=True)

    def test_high_grade_has_higher_priority_than_medium(self):
        scores = _scores(cpu_grade="high", ram_grade="medium")
        result = select_upgrade_targets(scores, _profile(), None)
        cpu_p = next(t["priority"] for t in result if t["part"] == "CPU")
        ram_p = next(t["priority"] for t in result if t["part"] == "RAM")
        assert cpu_p > ram_p

    def test_user_type_boost_increases_priority(self):
        scores_no_boost = _scores(gpu_grade="medium")
        scores_no_boost["user_classification"] = {"user_type": []}

        scores_boost = _scores(gpu_grade="medium")
        scores_boost["user_classification"] = {"user_type": ["game"]}

        r_no  = select_upgrade_targets(scores_no_boost, _profile(), None)
        r_yes = select_upgrade_targets(scores_boost, _profile(), None)

        p_no  = next(t["priority"] for t in r_no  if t["part"] == "GPU")
        p_yes = next(t["priority"] for t in r_yes if t["part"] == "GPU")
        assert p_yes > p_no


class TestSelectUpgradeTargetsReason:
    def test_reason_present(self):
        scores = _scores(cpu_grade="high")
        result = select_upgrade_targets(scores, _profile(), None)
        cpu = next(t for t in result if t["part"] == "CPU")
        assert isinstance(cpu["reason"], str) and len(cpu["reason"]) > 0

    def test_user_type_prefix_in_reason(self):
        scores = _scores(gpu_grade="high")
        scores["user_classification"] = {"user_type": ["game"]}
        result = select_upgrade_targets(scores, _profile(), None)
        gpu = next(t for t in result if t["part"] == "GPU")
        assert "게임" in gpu["reason"]

    def test_gpu_unknown_included_with_low_priority(self):
        scores = _scores()
        scores["gpu_vram"] = {"score": 0.0, "grade": "unknown"}
        result = select_upgrade_targets(scores, _profile(), None)
        gpu = next((t for t in result if t["part"] == "GPU"), None)
        assert gpu is not None
        assert gpu["priority"] == 0.1
