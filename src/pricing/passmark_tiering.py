import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from src.pricing.exchange_rate import convert_usd_to_krw
from src.pricing.price_fetcher import (
    build_search_query,
    search_naver_shopping,
    extract_naver_candidates,
    search_ebay,
    extract_ebay_candidates
)


CPU_MAX_SCORE = 80000
GPU_MAX_SCORE = 41588
MAX_TIER = 29

CPU_PASSMARK_URL = "https://www.cpubenchmark.net/multithread/"
GPU_PASSMARK_URL = "https://www.videocardbenchmark.net/high_end_gpus.html"

CPU_SPECS_PATH = Path("data/specs/cpu_specs.json")
GPU_SPECS_PATH = Path("data/specs/gpu_specs.json")


def normalize_text(text):
    if text is None:
        return ""

    text = str(text).lower()
    text = re.sub(r"[^a-z0-9가-힣]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def fetch_html(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.read().decode("utf-8")

    except OSError as error:
        raise RuntimeError(
            f"PassMark 페이지 요청 실패: {url}"
        ) from error


class SimpleTableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_cell = False
        self.current_cell = ""
        self.current_row = []
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag in ("td", "th"):
            self.in_cell = True
            self.current_cell = ""

    def handle_endtag(self, tag):
        if tag in ("td", "th"):
            cell = self.current_cell.strip()

            if cell:
                self.current_row.append(cell)

            self.in_cell = False

        if tag == "tr":
            if self.current_row:
                self.rows.append(self.current_row)

            self.current_row = []

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data


def parse_passmark_rows(html):
    parser = SimpleTableParser()
    parser.feed(html)

    return parser.rows


def parse_score(score_text):
    if score_text in (None, "", "NA"):
        return None

    score_text = str(score_text).replace(",", "").strip()

    try:
        return int(score_text)

    except ValueError:
        return None


def parse_price_usd(price):
    if price in (None, "", "NA"):
        return "NA"

    price_text = str(price).replace("$", "").replace(",", "").strip()

    try:
        return float(price_text)

    except ValueError:
        return "NA"


def load_cpu_passmark_items():
    html = fetch_html(CPU_PASSMARK_URL)
    rows = parse_passmark_rows(html)

    items = []

    for row in rows:
        if len(row) < 3:
            continue

        name = row[0]
        score = parse_score(row[1])
        price = row[-1]

        if score is None:
            continue

        items.append({
            "name": name,
            "score": score,
            "price_usd": price
        })

    return items


def load_gpu_passmark_items():
    html = fetch_html(GPU_PASSMARK_URL)
    rows = parse_passmark_rows(html)

    items = []

    for row in rows:
        if len(row) < 3:
            continue

        name = row[0]
        score = parse_score(row[1])
        price = row[-1]

        if score is None:
            continue

        items.append({
            "name": name,
            "score": score,
            "price_usd": price
        })

    return items


def load_json(path):
    path = Path(path)

    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            return list(data.values())

        return []

    except json.JSONDecodeError as error:
        raise RuntimeError(f"JSON 해석 실패: {path}") from error

    except OSError as error:
        raise RuntimeError(f"JSON 파일 읽기 실패: {path}") from error


def save_json(data, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    except OSError as error:
        raise RuntimeError(f"JSON 파일 저장 실패: {path}") from error


def calculate_performance_tier(score, max_score, max_tier=MAX_TIER):
    if score in (None, "", "NA"):
        return None

    try:
        score = float(str(score).replace(",", ""))
    except ValueError:
        return None

    if max_score <= 0:
        return None

    tier = int((score / max_score) * max_tier)

    if tier < 1:
        return 1

    if tier > max_tier:
        return max_tier

    return tier


def calculate_cpu_tier(score):
    return calculate_performance_tier(score, CPU_MAX_SCORE)


def calculate_gpu_tier(score):
    return calculate_performance_tier(score, GPU_MAX_SCORE)


def find_matching_passmark_data(part_name, passmark_items):
    normalized_part_name = normalize_text(part_name)

    for item in passmark_items:
        passmark_name = item.get("name")
        normalized_passmark_name = normalize_text(passmark_name)

        if normalized_part_name == normalized_passmark_name:
            return item

    return None


def fetch_price_candidates_when_na(part):
    query = build_search_query(part)

    price_candidates = []

    try:
        naver_result = search_naver_shopping(query)
        price_candidates.extend(
            extract_naver_candidates(naver_result)
        )

    except Exception as error:
        price_candidates.append({
            "source": "naver",
            "error": str(error)
        })

    try:
        ebay_result = search_ebay(query)
        price_candidates.extend(
            extract_ebay_candidates(ebay_result)
        )

    except Exception as error:
        price_candidates.append({
            "source": "ebay",
            "error": str(error)
        })

    return price_candidates


def enrich_parts_with_passmark(parts, passmark_items, category):
    enriched_parts = []

    for part in parts:
        part_name = part.get("name")
        passmark_data = find_matching_passmark_data(part_name, passmark_items)

        if passmark_data is None:
            continue

        score = passmark_data.get("score")
        price_usd = parse_price_usd(passmark_data.get("price_usd", "NA"))

        if category == "cpu":
            tier = calculate_cpu_tier(score)
        elif category == "gpu":
            tier = calculate_gpu_tier(score)
        else:
            tier = None

        part["passmark_score"] = score
        part["performance_tier"] = tier
        part["passmark_price_usd"] = price_usd

        if price_usd == "NA":
            part["passmark_price_krw"] = "NA"
            part["price_candidates"] = fetch_price_candidates_when_na(part)
        else:
            part["passmark_price_krw"] = convert_usd_to_krw(price_usd)
            part["price_candidates"] = []

        enriched_parts.append(part)

    return enriched_parts


def update_cpu_gpu_with_passmark():
    cpu_parts = load_json(CPU_SPECS_PATH)
    gpu_parts = load_json(GPU_SPECS_PATH)

    cpu_passmark_items = load_cpu_passmark_items()
    gpu_passmark_items = load_gpu_passmark_items()

    enriched_cpu_parts = enrich_parts_with_passmark(
        cpu_parts,
        cpu_passmark_items,
        "cpu"
    )

    enriched_gpu_parts = enrich_parts_with_passmark(
        gpu_parts,
        gpu_passmark_items,
        "gpu"
    )

    save_json(enriched_cpu_parts, CPU_SPECS_PATH)
    save_json(enriched_gpu_parts, GPU_SPECS_PATH)

    return {
        "cpu_count": len(enriched_cpu_parts),
        "gpu_count": len(enriched_gpu_parts)
    }