import urllib.error
from unittest.mock import patch, MagicMock

import pytest

from src.pricing.price_fetcher import (
    build_search_query, safe_int, safe_float,
    extract_naver_candidates, extract_ebay_candidates,
    _proxy_get,
)


class TestBuildSearchQuery:
    def test_combines_manufacturer_and_name(self):
        assert build_search_query({"manufacturer": "AMD", "name": "Ryzen 7 9800X3D"}) == "AMD Ryzen 7 9800X3D"

    def test_missing_manufacturer_strips_leading_space(self):
        assert build_search_query({"name": "RTX 4070"}) == "RTX 4070"

    def test_empty_part_returns_empty_string(self):
        assert build_search_query({}) == ""


class TestSafeInt:
    def test_valid_string(self):
        assert safe_int("123") == 123

    def test_none_returns_none(self):
        assert safe_int(None) is None

    def test_invalid_string_returns_none(self):
        assert safe_int("not_a_number") is None


class TestSafeFloat:
    def test_valid_string(self):
        assert safe_float("1.5") == 1.5

    def test_none_returns_none(self):
        assert safe_float(None) is None

    def test_invalid_string_returns_none(self):
        assert safe_float("abc") is None


class TestExtractCandidatesPassThrough:
    """프록시 전환 후 search_*()가 이미 list[dict]를 반환하므로
    extract_*_candidates()는 단순 pass-through여야 한다."""

    def test_naver_passes_through_list(self):
        items = [{"title": "RTX 4070"}]
        assert extract_naver_candidates(items) == items

    def test_naver_non_list_returns_empty(self):
        assert extract_naver_candidates("unexpected") == []

    def test_ebay_passes_through_list(self):
        items = [{"title": "Ryzen 7"}]
        assert extract_ebay_candidates(items) == items

    def test_ebay_non_list_returns_empty(self):
        assert extract_ebay_candidates(None) == []


class TestProxyGetErrorHandling:
    @patch("src.pricing.price_fetcher.urllib.request.urlopen")
    def test_http_error_wrapped_as_runtime_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://x", code=401, msg="Unauthorized", hdrs=None, fp=MagicMock(read=lambda: b"denied")
        )
        with pytest.raises(RuntimeError, match="401"):
            _proxy_get("/api/naver/search?query=x")

    @patch("src.pricing.price_fetcher.urllib.request.urlopen")
    def test_connection_error_wrapped_as_runtime_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("connection refused")
        with pytest.raises(RuntimeError):
            _proxy_get("/api/naver/search?query=x")
