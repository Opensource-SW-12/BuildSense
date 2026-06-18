import pytest
from unittest.mock import patch
from src.analysis.process_usage import analyze_process_usage, _load_path_overrides, _resolve_category, _load_categories


def _make_logs(procs_per_snapshot):
    """procs_per_snapshot: list of list[dict] — 각 스냅샷의 프로세스 목록."""
    return [{"processes": procs} for procs in procs_per_snapshot]


def _proc(name, cpu=0.0, mem=100.0, exe=""):
    return {"name": name, "cpu_percent": cpu, "memory_mb": mem, "exe": exe}


MOCK_CATEGORIES = {
    "game": ["game.exe", "javaw.exe"],
    "creative": ["photoshop.exe"],
    "browser": ["chrome.exe"],
    "messenger": ["update.exe"],
}

MOCK_PATH_OVERRIDES = {
    "javaw.exe": [("jetbrains", "development"), ("minecraft", "game")],
}


@pytest.fixture(autouse=True)
def patch_categories():
    flat = {name: cat for cat, names in MOCK_CATEGORIES.items() for name in names}
    with patch("src.analysis.process_usage._get_categories", return_value=flat), \
         patch("src.analysis.process_usage._get_path_overrides", return_value=MOCK_PATH_OVERRIDES):
        yield


class TestAnalyzeProcessUsageBasic:
    def test_known_process_categorized(self):
        logs = _make_logs([[_proc("game.exe", cpu=50.0)]] * 10)
        result = analyze_process_usage(logs)
        summary = result["category_summary"]
        assert "game" in summary

    def test_unknown_process_goes_to_etc(self):
        logs = _make_logs([[_proc("unknown_tool.exe", cpu=30.0)]] * 5)
        result = analyze_process_usage(logs)
        assert "etc" in result["category_summary"]

    def test_top_by_frequency_ordered(self):
        logs = _make_logs(
            [[_proc("game.exe")]] * 8 + [[_proc("photoshop.exe")]] * 3
        )
        result = analyze_process_usage(logs)
        freq = [e["name"] for e in result["top_by_frequency"]]
        assert freq.index("game.exe") < freq.index("photoshop.exe")

    def test_top_by_cpu_ordered(self):
        logs = _make_logs([
            [_proc("game.exe", cpu=80.0), _proc("photoshop.exe", cpu=20.0)]
        ] * 5)
        result = analyze_process_usage(logs)
        cpu_names = [e["name"] for e in result["top_by_cpu"]]
        assert cpu_names[0] == "game.exe"

    def test_appearance_ratio_correct(self):
        logs = _make_logs([[_proc("game.exe")]] * 6 + [[]] * 4)
        result = analyze_process_usage(logs)
        entry = next(e for e in result["top_by_frequency"] if e["name"] == "game.exe")
        assert abs(entry["appearance_ratio"] - 0.6) < 1e-9


class TestAnalyzeProcessUsageExtraCategories:
    def test_extra_category_overrides_etc(self):
        logs = _make_logs([[_proc("custom_tool.exe", cpu=40.0)]] * 5)
        result = analyze_process_usage(logs, extra_categories={"custom_tool.exe": "development"})
        assert result["category_summary"].get("development", 0) > 0
        assert "etc" not in result["category_summary"]

    def test_extra_category_case_insensitive(self):
        logs = _make_logs([[_proc("MyApp.exe", cpu=30.0)]] * 3)
        result = analyze_process_usage(logs, extra_categories={"MYAPP.EXE": "creative"})
        assert result["category_summary"].get("creative", 0) > 0

    def test_extra_category_does_not_affect_known_processes(self):
        logs = _make_logs([[_proc("game.exe", cpu=50.0)]] * 5)
        result = analyze_process_usage(logs, extra_categories={"game.exe": "creative"})
        # extra_categories takes priority — game.exe should now be creative
        assert result["category_summary"].get("creative", 0) > 0

    def test_none_extra_categories(self):
        logs = _make_logs([[_proc("game.exe", cpu=50.0)]] * 5)
        result = analyze_process_usage(logs, extra_categories=None)
        assert "game" in result["category_summary"]


class TestAnalyzeProcessUsagePathOverrides:
    def test_path_override_reclassifies_by_keyword(self):
        logs = _make_logs([[_proc("javaw.exe", cpu=40.0, exe=r"C:\Program Files\JetBrains\IntelliJ\jbr\bin\javaw.exe")]] * 5)
        result = analyze_process_usage(logs)
        assert result["category_summary"].get("development", 0) > 0
        assert "game" not in result["category_summary"]

    def test_no_matching_keyword_falls_back_to_default_category(self):
        logs = _make_logs([[_proc("javaw.exe", cpu=40.0, exe=r"C:\Users\me\AppData\Roaming\Unknown\javaw.exe")]] * 5)
        result = analyze_process_usage(logs)
        assert result["category_summary"].get("game", 0) > 0
        assert "development" not in result["category_summary"]

    def test_missing_exe_path_falls_back_to_default_category(self):
        logs = _make_logs([[_proc("javaw.exe", cpu=40.0)]] * 5)
        result = analyze_process_usage(logs)
        assert result["category_summary"].get("game", 0) > 0

    def test_extra_categories_take_priority_over_path_override(self):
        logs = _make_logs([[_proc("javaw.exe", cpu=40.0, exe=r"C:\JetBrains\bin\javaw.exe")]] * 5)
        result = analyze_process_usage(logs, extra_categories={"javaw.exe": "creative"})
        assert result["category_summary"].get("creative", 0) > 0
        assert "development" not in result["category_summary"]

    def test_process_without_override_rules_unaffected(self):
        logs = _make_logs([[_proc("update.exe", cpu=10.0, exe=r"C:\Users\me\AppData\Local\Discord\Update.exe")]] * 5)
        result = analyze_process_usage(logs)
        assert result["category_summary"].get("messenger", 0) > 0


@pytest.fixture(scope="module")
def real_overrides():
    return _load_path_overrides()


@pytest.fixture(scope="module")
def real_categories():
    return _load_categories()


class TestRealProcessPathOverridesFile:
    """data/process_path_overrides.json(실 파일) 회귀 테스트.
    generic 키워드("python")가 구체적 키워드("blender")보다 앞에 있으면
    먼저 매칭되어버려 뒤의 규칙이 영원히 도달 못 하는 버그가 있었음(KAN-209)."""

    def test_blender_python_resolves_to_creative_not_development(self, real_overrides, real_categories):
        exe = r"C:\Program Files\Blender Foundation\Blender 4.4\4.4\python\bin\python.exe"
        category = _resolve_category("python.exe", exe.lower(), real_categories, real_overrides)
        assert category == "creative"

    def test_plain_python_falls_back_to_default_category(self, real_overrides, real_categories):
        exe = r"C:\Program Files\Python311\python.exe"
        category = _resolve_category("python.exe", exe.lower(), real_categories, real_overrides)
        assert category == "development"

    def test_javaw_jetbrains_resolves_to_development(self, real_overrides, real_categories):
        exe = r"C:\Program Files\JetBrains\IntelliJ\jbr\bin\javaw.exe"
        category = _resolve_category("javaw.exe", exe.lower(), real_categories, real_overrides)
        assert category == "development"

    def test_javaw_minecraft_resolves_to_game(self, real_overrides, real_categories):
        exe = r"C:\Users\me\AppData\Roaming\PrismLauncher\java\bin\javaw.exe"
        category = _resolve_category("javaw.exe", exe.lower(), real_categories, real_overrides)
        assert category == "game"

    def test_update_notion_resolves_to_document_not_messenger(self, real_overrides, real_categories):
        exe = r"C:\Users\me\AppData\Local\Notion\Update.exe"
        category = _resolve_category("update.exe", exe.lower(), real_categories, real_overrides)
        assert category == "document"


class TestAnalyzeProcessUsageEdgeCases:
    def test_empty_logs(self):
        result = analyze_process_usage([])
        assert result["top_by_frequency"] == []
        assert result["category_summary"] == {}

    def test_duplicate_process_per_snapshot_counted_once(self):
        logs = _make_logs([[_proc("game.exe"), _proc("game.exe")]] * 4)
        result = analyze_process_usage(logs)
        entry = next(e for e in result["top_by_frequency"] if e["name"] == "game.exe")
        assert entry["appearance_count"] == 4

    def test_top_n_respected(self):
        procs = [_proc(f"proc_{i}.exe", cpu=float(i)) for i in range(20)]
        logs  = _make_logs([procs] * 5)
        result = analyze_process_usage(logs, top_n=5)
        assert len(result["top_by_frequency"]) <= 5
