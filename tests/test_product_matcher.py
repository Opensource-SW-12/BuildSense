import pytest
from src.pricing.product_matcher import is_matching_product, normalize_text, _chipset_matches


class TestNormalizeText:
    def test_html_tags_removed(self):
        result = normalize_text("<b>RTX 4090</b>")
        assert "<b>" not in result
        assert "rtx 4090" in result

    def test_lowercase_and_collapse(self):
        assert normalize_text("  Core   I9  ") == "core i9"


class TestChipsetMatches:
    def test_exact_match(self):
        assert _chipset_matches("rtx 4070", "RTX 4070") is True

    def test_variant_suffix_rejects(self):
        assert _chipset_matches("rtx 4070 super", "RTX 4070") is False
        assert _chipset_matches("rtx 4070 ti", "RTX 4070") is False

    def test_xt_suffix_rejects(self):
        assert _chipset_matches("rx 7900 xt", "RX 7900") is False

    def test_different_model_rejects(self):
        assert _chipset_matches("rtx 4080", "RTX 4070") is False


class TestIsMatchingProductGpu:
    def _part(self, chipset, memory_gb=None, manufacturer=None):
        p = {"category": "gpu", "chipset": chipset, "name": chipset or ""}
        if memory_gb:
            p["memory"] = {"capacity_gb": memory_gb}
        if manufacturer:
            p["manufacturer"] = manufacturer
        return p

    def test_exact_gpu_match(self):
        assert is_matching_product("ASUS RTX 4070 12GB Gaming", self._part("RTX 4070", 12))

    def test_gpu_variant_rejected(self):
        assert not is_matching_product("MSI RTX 4070 SUPER 12GB", self._part("RTX 4070", 12))

    def test_gpu_wrong_memory_rejected(self):
        assert not is_matching_product("RTX 4070 8GB", self._part("RTX 4070", 12))

    def test_gpu_manufacturer_korean_alias(self):
        assert is_matching_product("삼성전자 RTX 4070 12GB", self._part("RTX 4070", 12, "samsung"))

    def test_gpu_wrong_manufacturer_rejected(self):
        assert not is_matching_product("ASUS RTX 4070 12GB", self._part("RTX 4070", 12, "msi"))


class TestIsMatchingProductCpu:
    def _part(self, name, series=None, variant=None, manufacturer=None):
        p = {"category": "cpu", "name": name}
        if series:
            p["series"] = series
        if variant:
            p["variant"] = variant
        if manufacturer:
            p["manufacturer"] = manufacturer
        return p

    def test_cpu_match(self):
        assert is_matching_product("인텔 Core i9-13900K 박스", self._part("Core i9-13900K", manufacturer="intel"))

    def test_cpu_series_mismatch(self):
        assert not is_matching_product("Core i7-13700K", self._part("Core i9-13900K", series="i9"))

    def test_cpu_manufacturer_korean(self):
        assert is_matching_product("인텔 i9-13900K", self._part("i9-13900K", manufacturer="intel"))

    def test_cpu_amd_alias(self):
        assert is_matching_product("에이엠디 Ryzen 9 7950X", self._part("Ryzen 9 7950X", manufacturer="amd"))


class TestIsMatchingProductSsd:
    def _part(self, name, capacity_gb=None, storage_type=None):
        p = {"category": "ssd", "name": name}
        if capacity_gb:
            p["capacity_gb"] = capacity_gb
        if storage_type:
            p["storage_type"] = storage_type
        return p

    def test_ssd_capacity_match(self):
        assert is_matching_product("삼성 SSD 1TB NVMe", self._part("삼성 1TB SSD", capacity_gb=1000))

    def test_ssd_capacity_gb_match(self):
        assert is_matching_product("WD SSD 500GB", self._part("WD 500GB", capacity_gb=500))

    def test_ssd_wrong_capacity_rejected(self):
        assert not is_matching_product("WD SSD 250GB", self._part("WD 500GB", capacity_gb=500))

    def test_ssd_storage_type_mismatch_rejected(self):
        assert not is_matching_product("Samsung HDD 1TB", self._part("Samsung 1TB", capacity_gb=1000, storage_type="NVMe"))


class TestIsMatchingProductManufacturer:
    def test_no_manufacturer_always_passes(self):
        part = {"category": "cpu", "name": "i9-13900K"}
        assert is_matching_product("Some Brand i9-13900K", part)

    def test_asus_match(self):
        part = {"category": "gpu", "name": "RTX 4070", "chipset": "RTX 4070", "manufacturer": "asus"}
        assert is_matching_product("에이수스 RTX 4070 12GB", part)
