import random
import time
import json
from datetime import datetime
from statistics import mean, stdev

def generate_latency_healthy() -> float:
    """Simulate healthy network latency in milliseconds."""
    return random.uniform(20, 50)

def percentile(sorted_values, p: float) -> float:
    """
    Simple percentile implementation.
    p is between 0 and 100 (e.g., 95 for p95).
    Assumes sorted_values is already sorted.
    """
    if not sorted_values:
        raise ValueError("Cannot compute percentile of empty list.")
    if p <= 0:
        return sorted_values[0]
    if p >= 100:
        return sorted_values[-1]

    k = (len(sorted_values) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    # Linear interpolation between the two closest ranks
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)

if __name__ == "__main__":
    # ---- Config (keep simple and adjustable) ----
    region = "Region_A"
    samples = 120          # number of observations (e.g., 120 seconds ~ 2 minutes)
    interval_sec = 1       # delay between samples

    # ---- Data collection ----
    latencies = []

 
    log_path = "data/latency.log"
    with open(log_path, "w") as log_file:
        for i in range(samples):
            latency = generate_latency_healthy()
            timestamp = datetime.now().isoformat()

            latencies.append(latency)

            line = f"{timestamp}, latency={latency:.2f}ms\n"
            print(line.strip())
            log_file.write(line)

            time.sleep(interval_sec)

    # ---- Baseline computation ----
    lat_sorted = sorted(latencies)

    baseline = {
        "region": region,
        "samples": samples,
        "interval_sec": interval_sec,
        "created_at": datetime.now().isoformat(),

        # Core baseline stats
        "mean_ms": round(mean(latencies), 3),
        "std_ms": round(stdev(latencies), 3) if len(latencies) >= 2 else 0.0,
        "min_ms": round(min(latencies), 3),
        "max_ms": round(max(latencies), 3),

        # Tail latency matters in real systems
        "p95_ms": round(percentile(lat_sorted, 95), 3),
    }

    # ---- Save baseline (IRIS memory of "normal") ----
    baseline_path = "data/baseline_region_a.json"
    with open(baseline_path, "w") as f:
        json.dump(baseline, f, indent=2)

    # ---- Human-readable summary ----
    print("\n=== IRIS BASELINE ESTABLISHED ===")
    print(f"Region: {baseline['region']}")
    print(f"Samples: {baseline['samples']} @ every {baseline['interval_sec']}s")
    print(f"Mean latency: {baseline['mean_ms']} ms")
    print(f"Std (jitter): {baseline['std_ms']} ms")
    print(f"Min/Max: {baseline['min_ms']} / {baseline['max_ms']} ms")
    print(f"P95 latency: {baseline['p95_ms']} ms")
    print(f"Saved baseline to: {baseline_path}")
    print(f"Raw log saved to: {log_path}")
