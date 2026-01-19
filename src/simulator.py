import random
from statistics import mean, stdev

# -----------------------------
# IRIS Day 6: Pattern 1 - Slow Drift
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

def generate_window(samples, drift):
    latencies = []
    for i in range(samples):
        base = random.uniform(20, 50)
        jitter = random.uniform(-2, 2)
        latencies.append(base + drift + jitter)
    return latencies

# ---- Simulation config ----
windows = 4
samples_per_window = 120
drift_step = 3.0  # ms added per window

window_stats = []

print("\n=== IRIS PATTERN ANALYSIS: SLOW DRIFT ===")

for w in range(windows):
    drift = w * drift_step
    lat = generate_window(samples_per_window, drift)
    stats = compute_stats(lat)
    window_stats.append(stats)

    print(
        f"Window {w+1}: "
        f"Mean={stats['mean']:.2f}ms "
        f"P95={stats['p95']:.2f}ms "
        f"Std={stats['std']:.2f}ms"
    )

# ---- Detect slow drift pattern ----
mean_trend = all(
    window_stats[i]["mean"] < window_stats[i+1]["mean"]
    for i in range(len(window_stats)-1)
)

p95_trend = all(
    window_stats[i]["p95"] < window_stats[i+1]["p95"]
    for i in range(len(window_stats)-1)
)

std_stable = max(ws["std"] for ws in window_stats) < 1.5 * min(ws["std"] for ws in window_stats)

print("\n=== IRIS PATTERN CLASSIFICATION ===")

if mean_trend and p95_trend and std_stable:
    print("Pattern detected: SLOW DRIFT")
    print("Interpretation: Gradual, persistent performance degradation.")
else:
    print("No clear slow-drift pattern detected.")
