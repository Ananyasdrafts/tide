"""The honest evaluation.

Two questions:
1. Does personalising the guidance actually reduce hesitation and overload, versus a static
   one-size policy, and how close does the learned model get to an oracle that knows the
   person's true traits?
2. Does federated learning (weights only, data stays local) cost anything in accuracy
   against centralised training on pooled data?

    python scripts/run_eval.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from tide.campus import sample_campus
from tide.federated import centralized, fed_avg
from tide.guidance import PersonalizedPolicy, StaticPolicy
from tide.journey import run_journey
from tide.personalize import build_dataset, calibration_features, label
from tide.travelers import MODALITIES, Traveler, sample_profiles

START, GOAL = "entrance", "hall_B"


def run_population(campus, profiles, policies, seed0=100):
    peak = over = hes = tt = 0.0
    n = len(profiles)
    for i, (p, pol) in enumerate(zip(profiles, policies)):
        t = Traveler(p, np.random.default_rng(seed0 + i))
        r = run_journey(campus, START, GOAL, t, pol)
        peak += r.peak_stress
        over += r.overload_events
        hes += r.hesitations
        tt += r.total_time
    return {"peak": peak / n, "over": over / n, "hes": hes / n, "time": tt / n}


def model_scores(model, profiles, feats):
    mod_ok = sens_err = 0.0
    for p, f in zip(profiles, feats):
        pm, ps = model.predict(f)
        tm, ts = label(p)
        mod_ok += int(MODALITIES.index(pm) == tm)
        sens_err += abs(ps - ts)
    return mod_ok / len(profiles), sens_err / len(profiles)


def main():
    campus = sample_campus()
    rng = np.random.default_rng(7)
    train = sample_profiles(60, rng)
    test = sample_profiles(25, rng)

    clients = build_dataset(train, examples_per=4)
    fed = fed_avg(clients)
    cen = centralized(clients)

    feats = [calibration_features(p, seed=500000 + i) for i, p in enumerate(test)]
    fa, fe = model_scores(fed, test, feats)
    ca, ce = model_scores(cen, test, feats)
    print("=== model accuracy (does federated cost anything?) ===")
    print(f"  modality accuracy   federated {fa:.2f}   centralized {ca:.2f}")
    print(f"  sensitivity MAE     federated {fe:.2f}   centralized {ce:.2f}")

    static = [StaticPolicy() for _ in test]
    oracle = [PersonalizedPolicy(p.modality, p.stress_gain) for p in test]
    learned = [PersonalizedPolicy(*fed.predict(f)) for f in feats]

    rows = {
        "static": run_population(campus, test, static),
        "personalised (federated)": run_population(campus, test, learned),
        "personalised (oracle)": run_population(campus, test, oracle),
    }
    print("\n=== journeys (lower is better) ===")
    for name, m in rows.items():
        print(f"  {name:26} peak stress {m['peak']:.2f}   overload {m['over']:.2f}"
              f"   hesitations {m['hes']:.1f}   time {m['time']:.0f}s")

    _figure(rows)


def _figure(rows):
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    names = list(rows)
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.8))
    for k, (key, title) in enumerate([("over", "overload moments per journey"),
                                      ("peak", "peak stress (0-1)")]):
        vals = [rows[n][key] for n in names]
        ax[k].bar(range(len(names)), vals, color=["#94a3b8", "#3b82f6", "#22c55e"])
        ax[k].set_xticks(range(len(names)))
        ax[k].set_xticklabels(["static", "federated", "oracle"])
        ax[k].set_title(title)
    fig.suptitle("Personalised guidance vs a static one-size policy")
    fig.tight_layout()
    out = Path("docs/images")
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "personalization.png", dpi=130)
    print("\nwrote", out / "personalization.png")


if __name__ == "__main__":
    main()
