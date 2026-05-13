import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_ROOT / "open-db" / "CPU"
OUTPUT_FILE = PROJECT_ROOT / "data" / "specs" / "cpu_specs.json"


def normalize_cpu(raw_data, opendb_id, index):
    metadata = raw_data.get("metadata", {})

    release_year = metadata.get("releaseYear", None)
    if release_year is not None:
        try:
            release_year = int(release_year)
        except (ValueError, TypeError):
            release_year = None

    return {
        "part_id": f"cpu_{index:04d}",
        "opendb_id": opendb_id,
        "category": "cpu",
        "name": metadata.get("name", ""),
        "manufacturer": metadata.get("manufacturer", ""),
        "series": metadata.get("series", ""),
        "variant": metadata.get("variant", ""),
        "release_year": release_year
    }


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    normalized_cpus = []

    cpu_files = sorted(INPUT_DIR.glob("*.json"))

    for index, cpu_file in enumerate(cpu_files, start=1):
        try:
            with cpu_file.open("r", encoding="utf-8") as file:
                raw_data = json.load(file)
        except json.JSONDecodeError:
            print(f"skip: {cpu_file.name}")
            continue

        opendb_id = cpu_file.stem

        normalized_cpus.append(
            normalize_cpu(raw_data, opendb_id, index)
        )

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(normalized_cpus, file, indent=2, ensure_ascii=False)

    print(f"CPU specs normalized: {len(normalized_cpus)}")


if __name__ == "__main__":
    main()