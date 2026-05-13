import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = PROJECT_ROOT / "open-db" / "CPU"
OUTPUT_FILE = PROJECT_ROOT / "data" / "specs" / "cpu_specs.json"


def normalize_cpu(raw_data, opendb_id, index):
    metadata = raw_data.get("metadata", {})

    specs = raw_data.get("specifications", {})
    cores = raw_data.get("cores", {})
    clocks = raw_data.get("clocks", {})
    cache = raw_data.get("cache", {})
    memory = specs.get("memory", {})
    integrated_graphics = specs.get("integratedGraphics", {})

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
        "release_year": release_year,

        "socket": raw_data.get("socket", None),
        "microarchitecture": raw_data.get("microarchitecture", None),

        "cores_total": cores.get("total", None),
        "cores_performance": cores.get("performance", None),
        "cores_efficiency": cores.get("efficiency", None),
        "threads": cores.get("threads", None),

        "clock_base": clocks.get("performance", {}).get("base", None),
        "clock_boost": clocks.get("performance", {}).get("boost", None),
        "clock_efficiency_base": clocks.get("efficiency", {}).get("base", None),
        "clock_efficiency_boost": clocks.get("efficiency", {}).get("boost", None),

        "cache_l2": cache.get("l2", None),
        "cache_l3": cache.get("l3", None),

        "tdp": specs.get("tdp", None),

        "memory_types": memory.get("types", None),
        "memory_channels": memory.get("channels", None),
        "memory_max_gb": memory.get("maxCapacity", None),

        "integrated_graphics": integrated_graphics.get("model", None)
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