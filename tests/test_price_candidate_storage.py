import pytest

from src.pricing.price_candidate_storage import save_price_candidates, load_price_candidates


class TestSaveLoadRoundTrip:
    def test_save_then_load_returns_same_data(self, tmp_path):
        path = tmp_path / "prices" / "cpu_abc123.json"
        candidates = [{"title": "Ryzen 7 9800X3D", "price_krw": 599000}]
        save_price_candidates(candidates, path)
        assert load_price_candidates(path) == candidates

    def test_save_creates_missing_parent_directories(self, tmp_path):
        path = tmp_path / "nested" / "dir" / "data.json"
        save_price_candidates([{"a": 1}], path)
        assert path.exists()


class TestLoadMissingFile:
    def test_returns_empty_list_when_file_missing(self, tmp_path):
        assert load_price_candidates(tmp_path / "does_not_exist.json") == []


class TestSaveErrors:
    def test_non_serializable_data_raises_runtime_error(self, tmp_path):
        path = tmp_path / "bad.json"
        with pytest.raises(RuntimeError):
            save_price_candidates({"set": {1, 2, 3}}, path)
