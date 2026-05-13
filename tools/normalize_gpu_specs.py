import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_ROOT / "open-db" / "GPU"
OUTPUT_FILE = PROJECT_ROOT / "data" / "specs" / "gpu_specs.json"


def normalize_gpu(raw_data, opendb_id, index):
    metadata = raw_data.get("metadata", {})

    release_year = metadata.get("releaseYear", None)
    if release_year is not None:
        try:
            release_year = int(release_year)
        except (ValueError, TypeError):
            release_year = None

    return {
        "part_id": f"gpu_{index:04d}",
        "opendb_id": opendb_id,
        "category": "gpu",
        "name": metadata.get("name", ""),
        "manufacturer": metadata.get("manufacturer", ""),
        "series": metadata.get("series", ""),
        "variant": metadata.get("variant", ""),
        "release_year": release_year
    }


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    normalized_gpus = []

    gpu_files = sorted(INPUT_DIR.glob("*.json"))

    for index, gpu_file in enumerate(gpu_files, start=1):
        try:
            with gpu_file.open("r", encoding="utf-8") as file:
                raw_data = json.load(file)
        except json.JSONDecodeError:
            print(f"skip: {gpu_file.name}")
            continue

        opendb_id = gpu_file.stem

        normalized_gpus.append(
            normalize_gpu(raw_data, opendb_id, index)
        )

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(normalized_gpus, file, indent=2, ensure_ascii=False)

    print(f"GPU specs normalized: {len(normalized_gpus)}")


if __name__ == "__main__":
    main()