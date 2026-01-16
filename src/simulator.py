import random
import time
import json
from datetime import datetime
from statistics import mean, stdev

# -----------------------------
# IRIS Day 4: Deviation Checker
# -----------------------------
# Load baseline ("normal"), generate current behaviour, compute stats,
# and report deviations vs baseline. No alerts, no risk scoring.

def percentile(sorted_values, p: float) -> float:
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
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)

def compute_stats(latencies: list[float]) -> dict:
    lat_sorted = sorted(latencies)
    return {
        "mean_ms": mean(latencies),
        "std_ms": stdev(latencies) if len(latencies) >= 2 else 0.0,
        "min_ms": min(latencies),
        "max_ms": max(latencies),
        "p95_ms": percentile(lat_sorted, 95),
    }

def generate_latency_current(step: int, drift_total_ms: float, samples: int) -> float:
    """
    Current behaviour generator with subtle drift.
    - drift_total_ms: total drift added by the end of the run
    - step: current index
    """
    base = random.uniform(20, 50)

    # Linear drift from 0 -> drift_total_ms across the run
    drift = (step / max(samples - 1, 1)) * drift_total_ms

    # Slight extra jitter 
    jitter = random.uniform(-2, 2)

    return base + drift + jitter

def load_baseline(path: str) -> dict | None:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

if __name__ == "__main__":
    region = "Region_A"

    baseline_path = "data/baseline_region_a.json"
    baseline = load_baseline(baseline_path)

    # ---- If baseline isn't available (because data/ is ignored), fallback safely ----
    if baseline is None:
        print("Baseline file not found. Creating a temporary baseline (fallback) from a healthy run...")
        baseline_samples = 120
        baseline_latencies = [random.uniform(20, 50) for _ in range(baseline_samples)]
        baseline_stats = compute_stats(baseline_latencies)
        baseline = {
            "region": region,
            "samples": baseline_samples,
            "interval_sec": 1,
            "created_at": datetime.now().isoformat(),
            **{k: round(v, 3) for k, v in baseline_stats.items()},
        }
        print("Temporary baseline created.\n")

    # ---- Current run config ----
    current_samples = 120
    interval_sec = 1

    # Subtle drift to simulate early degradation (tunable)
    drift_total_ms = 8.0  # total increase by end of run (subtle)

    # ---- Collect current data ----
    current_latencies = []
    log_path = "data/current_latency.log"
    with open(log_path, "w") as log_file:
        for i in range(current_samples):
            latency = generate_latency_current(i, drift_total_ms, current_samples)
            ts = datetime.now().isoformat()
            current_latencies.append(latency)

            line = f"{ts}, latency={latency:.2f}ms\n"
            print(line.strip())
            log_file.write(line)

            time.sleep(interval_sec)

    # ---- Compute current stats ----
    current_stats = compute_stats(current_latencies)

    # ---- Compute deviations vs baseline ----
    d_mean = current_stats["mean_ms"] - float(baseline["mean_ms"])
    d_std = current_stats["std_ms"] - float(baseline["std_ms"])
    d_p95 = current_stats["p95_ms"] - float(baseline["p95_ms"])

    # Percent change in std (variability) is often more meaningful
    baseline_std = float(baseline["std_ms"]) if float(baseline["std_ms"]) != 0 else 1e-9
    std_ratio = current_stats["std_ms"] / baseline_std

    # ---- Human-readable deviation summary ----
    print("\n=== IRIS DEVIATION SUMMARY (NO ALERTS) ===")
    print(f"Region: {region}")
    print(f"Baseline mean/std/p95: {baseline['mean_ms']} / {baseline['std_ms']} / {baseline['p95_ms']} ms")
    print(f"Current   mean/std/p95: {current_stats['mean_ms']:.3f} / {current_stats['std_ms']:.3f} / {current_stats['p95_ms']:.3f} ms")
    print(f"ΔMean: {d_mean:+.3f} ms")
    print(f"ΔStd : {d_std:+.3f} ms (std ratio: {std_ratio:.2f}x)")
    print(f"ΔP95 : {d_p95:+.3f} ms")
    print(f"Raw current log saved to: {log_path}")

    # ---- Gentle interpretation (still not an alert) ----
    if d_mean > 3 or std_ratio > 1.3 or d_p95 > 3:
        print("\nInterpretation: Current behaviour is drifting away from baseline.")
        print("Next (Day 5): add persistence checks to reduce false positives.")
    else:
        print("\nInterpretation: Current behaviour is consistent with baseline.")
        print("Next (Day 5): introduce controlled stress/degradation and persistence logic.")
