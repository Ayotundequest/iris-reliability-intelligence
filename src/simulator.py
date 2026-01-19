import random
import time
import json
from datetime import datetime
from statistics import mean, stdev

# -----------------------------
# IRIS Day 5: Persistence Logic
# -----------------------------

def percentile(sorted_values, p: float) -> float:
    if not sorted_values:
        raise ValueError("Empty list")
    k = (len(sorted_values) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)

def compute_stats(latencies):
    lat_sorted = sorted(latencies)
    return {
        "mean_ms": mean(latencies),
        "std_ms": stdev(latencies) if len(latencies) >= 2 else 0.0,
        "p95_ms": percentile(lat_sorted, 95),
    }

def generate_latency(step, drift_total, samples):
    base = random.uniform(20, 50)
    drift = (step / max(samples - 1, 1)) * drift_total
    jitter = random.uniform(-2, 2)
    return base + drift + jitter

def load_baseline(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

if __name__ == "__main__":
    region = "Region_A"
    baseline = load_baseline("data/baseline_region_a.json")

    if baseline is None:
        baseline_lat = [random.uniform(20, 50) for _ in range(120)]
        baseline_stats = compute_stats(baseline_lat)
        baseline = {
            "mean_ms": baseline_stats["mean_ms"],
            "std_ms": baseline_stats["std_ms"],
            "p95_ms": baseline_stats["p95_ms"],
        }

    windows = 3
    samples_per_window = 120
    drift_total_ms = 8.0

    persistence_count = 0

    print("\n=== IRIS PERSISTENCE CHECK ===")

    for w in range(1, windows + 1):
        latencies = [
            generate_latency(i, drift_total_ms, samples_per_window)
            for i in range(samples_per_window)
        ]

        stats = compute_stats(latencies)

        d_mean = stats["mean_ms"] - baseline["mean_ms"]
        d_p95 = stats["p95_ms"] - baseline["p95_ms"]
        std_ratio = stats["std_ms"] / (baseline["std_ms"] or 1e-9)

        deviation = (
            d_mean > 3 or
            d_p95 > 3 or
            std_ratio > 1.3
        )

        if deviation:
            persistence_count += 1
            status = "DEVIATION"
        else:
            persistence_count = 0
            status = "NORMAL"

        print(
            f"Window {w}: {status} | "
            f"ΔMean={d_mean:+.2f}ms "
            f"ΔP95={d_p95:+.2f}ms "
            f"StdRatio={std_ratio:.2f}x"
        )

    print("\n=== IRIS INTERPRETATION ===")
    if persistence_count >= 3:
        print("Persistent deviation detected across multiple windows.")
        print("This is likely a real reliability issue (not noise).")
    elif persistence_count >= 1:
        print("Intermittent deviation observed.")
        print("Continue monitoring; no action yet.")
    else:
        print("Behaviour consistent with baseline.")
