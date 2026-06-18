from src.recommendation.price_resolver import _parse_query_capacity_gb, _parse_title_capacity_gb


class TestParseQueryCapacityGb:
    def test_plain_gb(self):
        assert _parse_query_capacity_gb("DDR4 RAM 48GB") == 48

    def test_tb_converted_to_gb(self):
        assert _parse_query_capacity_gb("PCIe 4.0 NVMe SSD 1TB") == 1000

    def test_no_capacity_returns_none(self):
        assert _parse_query_capacity_gb("DDR4 RAM") is None


class TestParseTitleCapacityGb:
    def test_plain_total_capacity(self):
        assert _parse_title_capacity_gb("삼성전자 DDR4 48GB PC4-25600") == 48

    def test_kit_notation_gb_x_count(self):
        """실제 쇼핑몰에서는 '24GBx2'처럼 개당 용량 x 키트 수량으로 표기되는 경우가
        더 흔하다 — 이 표기를 인식해 총 용량(48GB)으로 환산해야 한다."""
        assert _parse_title_capacity_gb("G.SKILL DDR4 48GB(24GBx2) 3200") == 48

    def test_kit_notation_count_x_gb(self):
        assert _parse_title_capacity_gb("DDR5 64GB (2x32GB) 6000MHz") == 64

    def test_kit_notation_with_multiplication_sign(self):
        assert _parse_title_capacity_gb("DDR4 32GB×2") == 64

    def test_mismatched_single_module_not_confused_with_kit(self):
        """킷 표기가 없는 단일 모듈 8GB 제품은 그대로 8GB로 인식되어야 한다
        (목표가 48GB일 때 이런 제품이 후보로 잘못 선정되던 버그의 핵심 원인)."""
        assert _parse_title_capacity_gb("삼성전자 DDR4 8GB PC4-25600 단일") == 8

    def test_no_capacity_returns_none(self):
        assert _parse_title_capacity_gb("그냥 메모리") is None
