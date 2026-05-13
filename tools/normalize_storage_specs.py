import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_ROOT / "open-db" / "Storage"
OUTPUT_FILE = PROJECT_ROOT / "data" / "specs" / "storage_specs.json"


def to_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def normalize_storage(raw_data, opendb_id, index):
    metadata = raw_data.get("metadata", {})
    specs = raw_data.get("specifications", {})
    appearance = raw_data.get("appearance", {})

    release_year = to_int(metadata.get("releaseYear"))

    return {
        "part_id": f"storage_{index:04d}",
        "opendb_id": opendb_id,
        "category": "storage",

        "name": metadata.get("name", ""),
        "manufacturer": metadata.get("manufacturer", ""),
        "series": metadata.get("series", ""),
        "variant": metadata.get("variant", ""),
        "release_year": release_year,

        "storage_type": specs.get("type", None),
        "capacity_gb": specs.get("capacityGb", None),
        "form_factor": specs.get("formFactor", None),
        "interface": specs.get("interface", None),

        "nvme": specs.get("nvme", None),
        "cache_mb": specs.get("cacheMb", None),

        "lighting": appearance.get("lighting", None)
    }


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    normalized_storage = []

    storage_files = sorted(INPUT_DIR.glob("*.json"))

    for index, storage_file in enumerate(storage_files, start=1):
        try:
            with storage_file.open("r", encoding="utf-8") as file:
                raw_data = json.load(file)
        except json.JSONDecodeError:
            print(f"skip: {storage_file.name}")
            continue

        opendb_id = storage_file.stem

        normalized_storage.append(
            normalize_storage(raw_data, opendb_id, index)
        )

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(normalized_storage, file, indent=2, ensure_ascii=False)

    print(f"Storage specs normalized: {len(normalized_storage)}")


if __name__ == "__main__":
    main()