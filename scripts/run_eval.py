"""The honest evaluation of Cairn.

Over several seeds (mean and spread), on held-out simulated travelers:

1. Does personalising guidance reduce overload versus a static one-size policy, and how
   close does the federated model get to an oracle that knows the true traits?
2. Where does the gain come from? An ablation splits it into matching modality, easing the
   pace, and taking a calmer route.
3. Does the benefit reach the people who need it most? A slice by sensitivity.
4. Does easing ahead of a busy segment (anticipation) beat reacting after stress rises?
5. Does acting cautiously when the model is unsure (confidence-aware) help over trusting an
   uncertain guess?
6. Does federated learning (weights only, data local) cost accuracy versus centralised?

    python scripts/run_eval.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from cairn.campus import sample_campus
from cairn.federated import centralized, fed_avg
from cairn.guidance import PersonalizedPolicy, StaticPolicy
from cairn.journey import run_journey
from cairn.personalize import build_dataset, calibration_features, label
from cairn.travelers import MODALITIES, Traveler, sample_profiles

START, GOAL = "entrance", "hall_B"
SEEDS = [1, 2, 3, 4, 5]


def policy_for(kind, profile, pred):
    pm, ps, conf = pred
    if kind == "static":
        return StaticPolicy()
    if kind == "oracle":
        return PersonalizedPolicy(profile.modality, profile.stress_gain)
    if kind == "personalised":
        return PersonalizedPolicy(pm, ps)
    if kind == "modality-only":
        return PersonalizedPolicy(pm, ps, ease_pace=False, calm_route=False)
    if kind == "pace-only":
        return PersonalizedPolicy(pm, ps, match_modality=False, calm_route=False)
    if kind == "route-only":
        return PersonalizedPolicy(pm, ps, match_modality=False, ease_pace=False)
    if kind == "reactive":
        # eases only on current stress (ignores the sensitivity estimate and the route)
        return PersonalizedPolicy(pm, ps, use_sensitivity=False, calm_route=False)
    if kind == "anticipatory":
        return PersonalizedPolicy(pm, ps, use_sensitivity=False, calm_route=False, anticipate=True)
    raise ValueError(kind)


def journey_overload(campus, profile, policy, seed):
    t = Traveler(profile, np.random.default_rng(seed))
    r = run_journey(campus, START, GOAL, t, policy)
    return r.overload_events, r.peak_stress


def main():
    campus = sample_campus()
    conditions = ["static", "personalised", "oracle", "modality-only", "pace-only",
                  "route-only", "reactive", "anticipatory"]
    over = {c: [] for c in conditions}     # per-seed mean overload
    peak = {c: [] for c in conditions}
    mod_fed, mod_cen, sens_fed, sens_cen = [], [], [], []
    slice_rows = []  # (sensitivity, overload_static, overload_personalised)
    conf_rows = []   # (model confidence, overload naive, overload confidence-aware)

    for s in SEEDS:
        rng = np.random.default_rng(s)
        train = sample_profiles(50, rng)
        test = sample_profiles(40, rng)
        clients = build_dataset(train, examples_per=4, seed0=s * 99)
        fed = fed_avg(clients)
        cen = centralized(clients)

        feats = [calibration_features(p, seed=700000 + s * 1000 + i) for i, p in enumerate(test)]
        preds = [fed.predict_conf(f) for f in feats]

        # model accuracy, federated vs centralized
        for model, ma, sa in [(fed, mod_fed, sens_fed), (cen, mod_cen, sens_cen)]:
            ok = se = 0.0
            for p, f in zip(test, feats):
                pm, ps, _ = model.predict_conf(f)
                tm, ts = label(p)
                ok += int(MODALITIES.index(pm) == tm)
                se += abs(ps - ts)
            ma.append(ok / len(test))
            sa.append(se / len(test))

        for c in conditions:
            o = p_ = 0.0
            for i, (prof, pr) in enumerate(zip(test, preds)):
                ov, pk = journey_overload(campus, prof, policy_for(c, prof, pr), seed=10_000 + i)
                o += ov
                p_ += pk
            over[c].append(o / len(test))
            peak[c].append(p_ / len(test))

        for i, prof in enumerate(test):
            pm, ps, conf = preds[i]
            so, _ = journey_overload(campus, prof, policy_for("static", prof, preds[i]), 10_000 + i)
            po, _ = journey_overload(campus, prof, policy_for("personalised", prof, preds[i]), 10_000 + i)
            slice_rows.append((prof.stress_gain, so, po))
            ca, _ = journey_overload(campus, prof, PersonalizedPolicy(pm, ps, confidence=conf), 10_000 + i)
            conf_rows.append((conf, po, ca))

    def ms(d, c):
        a = np.array(d[c])
        return a.mean(), a.std()

    print("=== overload moments per journey (mean +/- std over seeds, lower is better) ===")
    for c in ["static", "modality-only", "pace-only", "route-only", "personalised", "oracle"]:
        m, sd = ms(over, c)
        pm, _ = ms(peak, c)
        print(f"  {c:18} overload {m:.2f} +/- {sd:.2f}   peak stress {pm:.2f}")

    print("\n=== anticipation: ease ahead of a busy segment (no sensitivity estimate used) ===")
    print(f"  reactive (stress only) {ms(over, 'reactive')[0]:.2f}   "
          f"anticipatory {ms(over, 'anticipatory')[0]:.2f}")

    cr = np.array(conf_rows)
    low = cr[:, 0] < 0.5
    print("\n=== confidence-aware: act cautiously when the model is unsure ===")
    print(f"  all travelers        naive {cr[:, 1].mean():.2f}   confidence-aware {cr[:, 2].mean():.2f}")
    if low.sum():
        print(f"  low-confidence ones  naive {cr[low, 1].mean():.2f}   "
              f"confidence-aware {cr[low, 2].mean():.2f}   (n={int(low.sum())})")

    print("\n=== federated vs centralized (privacy cost?) ===")
    print(f"  modality accuracy   fed {np.mean(mod_fed):.2f}   cen {np.mean(mod_cen):.2f}")
    print(f"  sensitivity MAE     fed {np.mean(sens_fed):.2f}   cen {np.mean(sens_cen):.2f}")

    print("\n=== does it help the most sensitive most? (overload, static -> personalised) ===")
    rows = np.array(slice_rows)
    edges = [(0.2, 0.45, "low"), (0.45, 0.65, "medium"), (0.65, 0.91, "high")]
    slice_summary = []
    for lo, hi, name in edges:
        m = (rows[:, 0] >= lo) & (rows[:, 0] < hi)
        st, pe = rows[m, 1].mean(), rows[m, 2].mean()
        slice_summary.append((name, st, pe))
        print(f"  {name:7} sensitivity: {st:.2f} -> {pe:.2f}   (n={int(m.sum())})")

    _figures(over, slice_summary,
             ["static", "route-only", "modality-only", "pace-only", "personalised", "oracle"])


def _figures(over, slice_summary, conditions):
    import matplotlib

    matplotlib.use("Agg")
    from matplotlib import pyplot as plt

    out = Path("docs/images")
    out.mkdir(parents=True, exist_ok=True)

    # ablation: overload by condition
    fig, ax = plt.subplots(figsize=(8, 3.8))
    vals = [np.mean(over[c]) for c in conditions]
    ax.bar(range(len(conditions)), vals, color="#3b82f6")
    ax.set_xticks(range(len(conditions)))
    ax.set_xticklabels(conditions, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("overload moments per journey")
    ax.set_title("Where the gain comes from")
    fig.tight_layout()
    fig.savefig(out / "ablation.png", dpi=130)

    # slice by sensitivity
    fig, ax = plt.subplots(figsize=(6, 3.8))
    names = [r[0] for r in slice_summary]
    x = np.arange(len(names))
    ax.bar(x - 0.2, [r[1] for r in slice_summary], 0.4, label="static", color="#94a3b8")
    ax.bar(x + 0.2, [r[2] for r in slice_summary], 0.4, label="personalised", color="#22c55e")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{n}\nsensitivity" for n in names])
    ax.set_ylabel("overload moments per journey")
    ax.set_title("The benefit is largest for the most sensitive")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "by_sensitivity.png", dpi=130)
    print("\nwrote docs/images/ablation.png and by_sensitivity.png")


if __name__ == "__main__":
    main()
