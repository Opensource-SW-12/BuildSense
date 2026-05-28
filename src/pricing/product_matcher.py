import re

_MANUFACTURER_ALIASES = {
    "samsung":        ["삼성", "삼성전자"],
    "lg":             ["엘지", "엘지전자"],
    "sk":             ["에스케이", "sk하이닉스"],
    "intel":          ["인텔"],
    "amd":            ["에이엠디"],
    "asus":           ["에이수스"],
    "gigabyte":       ["기가바이트"],
    "msi":            ["엠에스아이"],
    "seagate":        ["씨게이트"],
    "western digital": ["웨스턴디지털", "웨스턴 디지털"],
    "wd":             ["웨스턴디지털"],
    "corsair":        ["커세어"],
    "kingston":       ["킹스턴"],
    "crucial":        ["크루셜"],
}


def normalize_text(text):
    if text is None:
        return ""

    text = str(text).lower()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^a-z0-9가-힣]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def contains_normalized_keyword(normalized_text, keyword):
    normalized_keyword = normalize_text(keyword)

    if not normalized_keyword:
        return True

    return normalized_keyword in normalized_text

def _manufacturer_matches(title_norm: str, manufacturer: str) -> bool:
    mfr_norm = normalize_text(manufacturer)
    if not mfr_norm:
        return True
    if contains_normalized_keyword(title_norm, mfr_norm):
        return True
    for alias in _MANUFACTURER_ALIASES.get(mfr_norm, []):
        if contains_normalized_keyword(title_norm, alias):
            return True
    return False


def is_matching_product(product_title, part):
    title = normalize_text(product_title)

    manufacturer = part.get("manufacturer", "")
    name = part.get("name", "")
    category = part.get("category", "")

    if manufacturer and not _manufacturer_matches(title, manufacturer):
        return False

    name_tokens = normalize_text(name).split()

    important_tokens = [
        token for token in name_tokens
        if len(token) >= 2
    ]

    matched_count = sum(
        1 for token in important_tokens
        if contains_normalized_keyword(title, token)
    )

    if important_tokens and matched_count < max(1, len(important_tokens) // 2):
        return False

    if category == "gpu":
        chipset = part.get("chipset")
        memory = part.get("memory", {})

        if chipset and not contains_normalized_keyword(title, chipset):
            return False

        if memory.get("capacity_gb"):
            capacity_text = str(memory["capacity_gb"])

            if capacity_text not in title:
                return False

    if category == "cpu":
        series = part.get("series")
        variant = part.get("variant")

        if series and not contains_normalized_keyword(title, series):
            return False

        if variant and not contains_normalized_keyword(title, variant):
            return False

    if category in ["ssd", "hdd"]:
        capacity_gb = part.get("capacity_gb")
        storage_type = part.get("storage_type")

        if storage_type and not contains_normalized_keyword(title, storage_type):
            return False

        if capacity_gb:
            capacity_gb = int(capacity_gb)

            if capacity_gb >= 1000:
                capacity_tb = str(capacity_gb // 1000)

                if capacity_tb not in title and str(capacity_gb) not in title:
                    return False

            else:
                if str(capacity_gb) not in title:
                    return False

    return True