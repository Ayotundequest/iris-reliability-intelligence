import random
from statistics import mean, stdev

# -----------------------------------------
# IRIS Day 9: Multi-pattern classification
# -----------------------------------------

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
        "p95": percentile(s, 95),
    }

# --------- Scenario generators ----------

def gen_slow_drift(samples, drift_ms):
    # Pattern #1: mean and p95 rise gradually; variance stays roughly stable
    lat = []
    for _ in range(samples):
        base = random.uniform(20, 50)
        jitter = random.uniform(-2, 2)
        lat.append(base + drift_ms + jitter)
    return lat

def gen_variance_explosion(samples, jitter_amp):
    # Pattern #2: mean mostly stable; jitter increases strongly; tail gets worse
    lat = []
    for _ in range(samples):
        base = random.uniform(20, 50)
        jitter = random.uniform(-jitter_amp, jitter_amp)
        lat.append(base + jitter)
    return lat

def gen_tail_only(samples, tail_fraction, tail_latency):
    # Pattern #3: most values normal; small fraction extreme; mean/std should stay relatively stable if tail is rare
    lat = []
    for _ in range(samples):
        if random.random() < tail_fraction:
            lat.append(tail_latency + random.uniform(-5, 5))
        else:
            lat.append(random.uniform(20, 50))
    return lat

# --------- Feature extraction ----------

def is_monotonic_increasing(values, slack=0.0):
    # allow small slack so random noise doesn't break trend
    return all(values[i] <= values[i+1] + slack for i in range(len(values) - 1))

def summarize_features(window_stats):
    means = [ws["mean"] for ws in window_stats]
    stds  = [ws["std"]  for ws in window_stats]
    p95s  = [ws["p95"]  for ws in window_stats]

    mean_delta = max(means) - min(means)
    std_delta  = max(stds)  - min(stds)
    p95_delta  = max(p95s)  - min(p95s)

    mean_trend_up = is_monotonic_increasing(means, slack=0.3)
    p95_trend_up  = is_monotonic_increasing(p95s, slack=0.5)

    std_growth = (stds[-1] / (stds[0] if stds[0] != 0 else 1e-9))

    return {
        "means": means,
        "stds": stds,
        "p95s": p95s,
        "mean_delta": mean_delta,
        "std_delta": std_delta,
        "p95_delta": p95_delta,
        "mean_trend_up": mean_trend_up,
        "p95_trend_up": p95_trend_up,
        "std_growth": std_growth,
    }

# --------- Scoring (rule-based, multi-pattern) ----------

def score_patterns(feat):
    # The idea: each pattern gets points for the “shape” it expects.
    # Higher score = better explanation.

    scores = {
        "SLOW_DRIFT": 0,
        "VARIANCE_EXPLOSION": 0,
        "TAIL_ONLY_DEGRADATION": 0,
    }

    # --- Pattern #1: Slow Drift ---
    if feat["mean_trend_up"]:
        scores["SLOW_DRIFT"] += 3
    if feat["p95_trend_up"]:
        scores["SLOW_DRIFT"] += 2
    if feat["mean_delta"] >= 3:
        scores["SLOW_DRIFT"] += 2
    if feat["std_growth"] < 1.35:
        scores["SLOW_DRIFT"] += 2  # stability matters
    elif feat["std_growth"] < 1.5:
        scores["SLOW_DRIFT"] += 1

    # --- Pattern #2: Variance Explosion ---
    if feat["std_growth"] >= 1.5:
        scores["VARIANCE_EXPLOSION"] += 4
    elif feat["std_growth"] >= 1.3:
        scores["VARIANCE_EXPLOSION"] += 2

    if feat["p95_delta"] >= 3:
        scores["VARIANCE_EXPLOSION"] += 2
    if not feat["mean_trend_up"]:
        scores["VARIANCE_EXPLOSION"] += 2  # mean shouldn't look like drift
    if feat["mean_delta"] < 3.5:
        scores["VARIANCE_EXPLOSION"] += 1

    # --- Pattern #3: Tail-only degradation ---
    # Tail-only means: mean + std fairly stable, but p95 worsens
    if feat["p95_delta"] >= 5:
        scores["TAIL_ONLY_DEGRADATION"] += 4
    elif feat["p95_delta"] >= 3:
        scores["TAIL_ONLY_DEGRADATION"] += 2

    if feat["mean_delta"] < 3:
        scores["TAIL_ONLY_DEGRADATION"] += 2
    if feat["std_delta"] < 3:
        scores["TAIL_ONLY_DEGRADATION"] += 2
    if feat["p95_trend_up"]:
        scores["TAIL_ONLY_DEGRADATION"] += 1

    return scores

def classify(scores):
    # Decide label + confidence + mixed detection
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_label, top_score = ranked[0]
    second_label, second_score = ranked[1]

    # Confidence rules (simple, explainable)
    if top_score >= 8 and (top_score - second_score) >= 3:
        confidence = "HIGH"
        label = top_label
    elif top_score >= 6 and (top_score - second_score) >= 2:
        confidence = "MEDIUM"
        label = top_label
    elif top_score >= 5 and (top_score - second_score) <= 1:
        confidence = "LOW"
        label = "MIXED/TRANSITION"
    else:
        confidence = "LOW"
        label = "UNCERTAIN"

    return label, confidence, ranked

# --------- Run a chosen scenario ----------

if __name__ == "__main__":
    windows = 4
    samples_per_window = 120

    # Choose ONE scenario to test today:
    #   "drift", "variance", "tail", "mixed"
    scenario = "mixed"

    window_stats = []

    print(f"\n=== IRIS DAY 9: MULTI-PATTERN CLASSIFIER (scenario={scenario}) ===\n")

    for w in range(windows):
        if scenario == "drift":
            # drift increases each window
            lat = gen_slow_drift(samples_per_window, drift_ms=w * 3.0)

        elif scenario == "variance":
            # jitter increases each window
            jitter_schedule = [2, 4, 8, 12]
            lat = gen_variance_explosion(samples_per_window, jitter_amp=jitter_schedule[w])

        elif scenario == "tail":
            # tail gets worse each window but kept relatively rare
            tail_schedule = [(0.02, 90), (0.02, 100), (0.02, 110), (0.02, 120)]
            frac, tail_lat = tail_schedule[w]
            lat = gen_tail_only(samples_per_window, frac, tail_lat)

        elif scenario == "mixed":
            # intentionally create a transitional case (tail + some variance)
            tail_schedule = [(0.03, 80), (0.04, 90), (0.05, 100), (0.06, 110)]
            jitter_schedule = [2, 4, 6, 8]
            frac, tail_lat = tail_schedule[w]

            # mix: mostly normal, some tail, some jitter
            lat = []
            for _ in range(samples_per_window):
                base = random.uniform(20, 50)
                jitter = random.uniform(-jitter_schedule[w], jitter_schedule[w])
                if random.random() < frac:
                    lat.append(tail_lat + random.uniform(-5, 5) + jitter)
                else:
                    lat.append(base + jitter)

        else:
            raise ValueError("Unknown scenario value")

        stats = compute_stats(lat)
        window_stats.append(stats)

        print(
            f"Window {w+1}: Mean={stats['mean']:.2f}ms "
            f"Std={stats['std']:.2f}ms "
            f"P95={stats['p95']:.2f}ms"
        )

    feat = summarize_features(window_stats)
    scores = score_patterns(feat)
    label, confidence, ranked = classify(scores)

    print("\n=== FEATURES (shape of behaviour) ===")
    print(f"mean_delta={feat['mean_delta']:.2f} | std_growth={feat['std_growth']:.2f}x | p95_delta={feat['p95_delta']:.2f}")
    print(f"mean_trend_up={feat['mean_trend_up']} | p95_trend_up={feat['p95_trend_up']}")

    print("\n=== SCORES ===")
    for k, v in scores.items():
        print(f"{k}: {v}")

    print("\n=== CLASSIFICATION ===")
    print(f"Label: {label}")
    print(f"Confidence: {confidence}")
    print("Ranking:", ranked)
