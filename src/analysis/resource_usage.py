from src.normalization.core import calculate_basic_stats


def calculate_high_load_ratio(values, threshold):
    valid_values = [value for value in values if value is not None]

    if not valid_values:
        return 0

    high_load_count = sum(1 for value in valid_values if value >= threshold)

    return high_load_count / len(valid_values)


def analyze_cpu_usage(logs):
    cpu_values = [log.get("cpu_percent") for log in logs]

    return {
        "stats": calculate_basic_stats(cpu_values),
        "high_load_ratio": calculate_high_load_ratio(cpu_values, 75)
    }


def analyze_ram_usage(logs):
    ram_values = [log.get("ram_percent") for log in logs]

    return {
        "stats": calculate_basic_stats(ram_values),
        "high_load_ratio": calculate_high_load_ratio(ram_values, 85)
    }


def analyze_gpu_usage(logs):
    gpu_values = [log.get("gpu_percent") for log in logs]

    total_count = len(gpu_values)
    none_count = sum(1 for value in gpu_values if value is None)

    valid_gpu_values = [value for value in gpu_values if value is not None]

    none_ratio = none_count / total_count if total_count > 0 else 0

    return {
        "stats": calculate_basic_stats(valid_gpu_values),
        "gpu_not_detected_ratio": none_ratio,
        "high_load_ratio": calculate_high_load_ratio(valid_gpu_values, 80)
    }


def analyze_vram_usage(logs):
    vram_used_values = []
    vram_usage_percent_values = []

    for log in logs:
        used = log.get("vram_used_mb")
        total = log.get("vram_total_mb")

        if used is None or total is None or total == 0:
            continue

        vram_used_values.append(used)

        usage_percent = (used / total) * 100
        vram_usage_percent_values.append(usage_percent)

    return {
        "used_mb_stats": calculate_basic_stats(vram_used_values),
        "usage_percent_stats": calculate_basic_stats(vram_usage_percent_values),
        "high_load_ratio": calculate_high_load_ratio(vram_usage_percent_values, 90)
    }


def analyze_resource_usage(logs):
    return {
        "cpu": analyze_cpu_usage(logs),
        "ram": analyze_ram_usage(logs),
        "gpu": analyze_gpu_usage(logs),
        "vram": analyze_vram_usage(logs)
    }