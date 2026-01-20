import random
import os
import matplotlib.pyplot as plt
from statistics import mean, stdev

# -----------------------------
# IRIS Day 7: Pattern 2 - Variance Explosion 
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

def generate_window(samples, jitter_amplitude):
    """
    Keep base distribution the same but increase jitter amplitude
    to simulate instability (variance explosion).
    """
    latencies = []
    for _ in range(samples):
        base = random.uniform(20, 50)
        jitter = random.uniform(-jitter_amplitude, jitter_amplitude)
        latencies.append(base + jitter)
    return latencies

def save_latency_plot(latencies, title, path):
    plt.figure(figsize=(10, 4))
    plt.plot(latencies)
    plt.title(title)
    plt.xlabel("Sample Index (time)")
    plt.ylabel("Latency (ms)")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

def save_summary_plot(means, stds, p95s, path):
    windows = list(range(1, len(means) + 1))
    plt.figure(figsize=(10, 4))
    plt.plot(windows, means, marker="o", label="Mean")
    plt.plot(windows, stds, marker="o", label="Std (jitter)")
    plt.plot(windows, p95s, marker="o", label="P95")
    plt.title("Variance Explosion Summary Across Windows")
    plt.xlabel("Window")
    plt.ylabel("Latency / Variability (ms)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

# ---- Simulation config ----
windows = 4
samples_per_window = 120
jitter_schedule = [2, 4, 8, 12]  # ms jitter range grows per window


os.makedirs("data", exist_ok=True)

window_stats = []
window_latencies = []

print("\n=== IRIS PATTERN ANALYSIS: VARIANCE EXPLOSION ===")

for w in range(windows):
    jitter_amp = jitter_schedule[w]
    lat = generate_window(samples_per_window, jitter_amp)
    stats = compute_stats(lat)

    window_latencies.append(lat)
    window_stats.append(stats)

    print(
        f"Window {w+1}: "
        f"Mean={stats['mean']:.2f}ms "
        f"P95={stats['p95']:.2f}ms "
        f"Std={stats['std']:.2f}ms "
        f"(jitter_amp=±{jitter_amp}ms)"
    )

    # Save a per-window latency vs time plot
    plot_path = f"data/pattern2_window{w+1}_latency.png"
    save_latency_plot(
        lat,
        title=f"Pattern #2 (Variance Explosion) — Window {w+1} (±{jitter_amp}ms jitter)",
        path=plot_path
    )

# ---- Detect variance explosion pattern ----
means = [ws["mean"] for ws in window_stats]
stds = [ws["std"] for ws in window_stats]
p95s = [ws["p95"] for ws in window_stats]

mean_not_monotonic = not all(means[i] < means[i+1] for i in range(len(means)-1))
std_growth = stds[-1] / (stds[0] if stds[0] != 0 else 1e-9)
p95_growth = p95s[-1] - p95s[0]

# Save a summary plot (mean/std/p95 across windows)
summary_path = "data/pattern2_summary.png"
save_summary_plot(means, stds, p95s, summary_path)

print("\n=== IRIS PATTERN CLASSIFICATION ===")
if std_growth >= 1.5 and p95_growth >= 3 and mean_not_monotonic:
    print("Pattern detected: VARIANCE EXPLOSION")
    print("Interpretation: Unstable behaviour (jitter spikes) despite average staying roughly stable.")
else:
    print("No clear variance-explosion pattern detected.")
    print(f"(Diagnostics: std_growth={std_growth:.2f}x, p95_growth={p95_growth:.2f}ms)")

print("\n=== PLOTS SAVED ===")
print("Per-window plots: data/pattern2_window*_latency.png")
print(f"Summary plot: {summary_path}")
