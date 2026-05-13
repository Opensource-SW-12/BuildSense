import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_ROOT / "open-db" / "RAM"
OUTPUT_FILE = PROJECT_ROOT / "data" / "specs" / "ram_specs.json"


def to_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def normalize_ram(raw_data, opendb_id, index):
    metadata = raw_data.get("metadata", {})
    specs = raw_data.get("specifications", {})
    modules = specs.get("modules", {})
    timings = specs.get("timings", {})
    appearance = raw_data.get("appearance", {})

    release_year = to_int(metadata.get("releaseYear"))

    return {
        "part_id": f"ram_{index:04d}",
        "opendb_id": opendb_id,
        "category": "ram",

        "name": metadata.get("name", ""),
        "manufacturer": metadata.get("manufacturer", ""),
        "series": metadata.get("series", ""),
        "variant": metadata.get("variant", ""),
        "release_year": release_year,

        "ram_type": specs.get("type", None),
        "speed": specs.get("speed", None),

        "modules_quantity": modules.get("quantity", None),
        "modules_capacity_gb": modules.get("capacityGb", None),
        "total_capacity_gb": specs.get("capacityGb", None),

        "form_factor": specs.get("formFactor", None),
        "cas_latency": specs.get("casLatency", None),
        "timings": timings,
        "voltage": specs.get("voltage", None),

        "ecc": specs.get("ecc", None),
        "registered": specs.get("registered", None),
        "rgb": specs.get("rgb", None),

        "color": appearance.get("color", []),
        "lighting": appearance.get("lighting", None),
        "manufacturer_color": appearance.get("manufacturerColor", None)
    }


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    normalized_rams = []

    ram_files = sorted(INPUT_DIR.glob("*.json"))

    for index, ram_file in enumerate(ram_files, start=1):
        try:
            with ram_file.open("r", encoding="utf-8") as file:
                raw_data = json.load(file)
        except json.JSONDecodeError:
            print(f"skip: {ram_file.name}")
            continue

        opendb_id = ram_file.stem
        normalized_rams.append(normalize_ram(raw_data, opendb_id, index))

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(normalized_rams, file, indent=2, ensure_ascii=False)

    print(f"RAM specs normalized: {len(normalized_rams)}")


if __name__ == "__main__":
    main()