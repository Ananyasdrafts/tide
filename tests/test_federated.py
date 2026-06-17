"""Federated learning (FedAvg) of the personalization model."""

import numpy as np

from cairn.federated import centralized, fed_avg
from cairn.personalize import build_dataset, calibration_features
from cairn.travelers import sample_profiles


def _modality_accuracy(model, profiles):
    ok = sum(int(model.predict(calibration_features(p, seed=222))[0] == p.modality) for p in profiles)
    return ok / len(profiles)


def test_fedavg_learns_and_stays_close_to_centralized():
    profs = sample_profiles(50, np.random.default_rng(5))
    clients = build_dataset(profs, examples_per=3)
    fed = fed_avg(clients, rounds=30)
    cen = centralized(clients, rounds=30)
    fa = _modality_accuracy(fed, profs)
    ca = _modality_accuracy(cen, profs)
    assert fa > 0.45                # federated learning recovers the signal
    assert abs(fa - ca) < 0.25      # and stays close to centralized: privacy costs little
