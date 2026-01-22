import random
from statistics import mean, stdev

# -----------------------------
# IRIS Day 8: Pattern 3 - Tail-only Degradation
# -----------------------------

def percentile(sorted_values, p):
    k = (len(sorted_values) - 1) * (p / 100)
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)

def compute_stats(latencies):
    s = sorted(latencies)
    return {
        "mean": mean(latencies),
        "std": stdev(latencies) if len(latencies) >= 2 else 0.0,
        "p95": percentile(s, 95)
    }

def generate_window(samples, tail_fraction, tail_latency):
    """
    Most samples are healthy.
    A small fraction are high-latency tail samples.
    """
    latencies = []
    for _ in range(samples):
        if random.random() < tail_fraction:
            latencies.append(tail_latency + random.uniform(-5, 5))
        else:
            latencies.append(random.uniform(20, 50))
    return latencies

# ---- Simulation config ----
windows = 4
samples_per_window = 120

# Tail gets worse each window
tail_schedule = [
    (0.03, 70),   # 3% of samples at ~70ms
    (0.04, 80),
    (0.05, 90),
    (0.06, 100),
]

window_stats = []

print("\n=== IRIS PATTERN ANALYSIS: TAIL-ONLY DEGRADATION ===")

for w in range(windows):
    tail_frac, tail_lat = tail_schedule[w]
    lat = generate_window(samples_per_window, tail_frac, tail_lat)
    stats = compute_stats(lat)
    window_stats.append(stats)

    print(
        f"Window {w+1}: "
        f"Mean={stats['mean']:.2f}ms "
        f"P95={stats['p95']:.2f}ms "
        f"Std={stats['std']:.2f}ms "
        f"(tail={int(tail_frac*100)}% @ ~{tail_lat}ms)"
    )

# ---- Detect tail-only degradation ----
means = [ws["mean"] for ws in window_stats]
stds = [ws["std"] for ws in window_stats]
p95s = [ws["p95"] for ws in window_stats]

mean_stable = max(means) - min(means) < 3
std_stable = max(stds) - min(stds) < 3
p95_rising = p95s[-1] - p95s[0] >= 5

print("\n=== IRIS PATTERN CLASSIFICATION ===")
if mean_stable and std_stable and p95_rising:
    print("Pattern detected: TAIL-ONLY DEGRADATION")
    print("Interpretation: Worst-case latency degrading while averages remain healthy.")
else:
    print("No clear tail-only degradation pattern detected.")
    print(f"(Diagnostics: meanΔ={max(means)-min(means):.2f}, stdΔ={max(stds)-min(stds):.2f}, p95Δ={p95s[-1]-p95s[0]:.2f})")
