"""The on-device personalization model."""

import numpy as np

from cairn.personalize import N_FEAT, Model, build_dataset, calibration_features
from cairn.travelers import MODALITIES, TravelerProfile, sample_profiles


def test_calibration_features_length():
    p = TravelerProfile(3.0, 0.2, 0.6, 0.2, "text")
    assert calibration_features(p, seed=0).shape == (N_FEAT,)


def test_weight_roundtrip():
    w = np.arange(len(Model().get_weights()), dtype=float)
    m = Model()
    m.set_weights(w)
    assert np.allclose(m.get_weights(), w)


def test_predict_returns_valid_ranges():
    p = TravelerProfile(3.0, 0.2, 0.6, 0.2, "haptic")
    mod, sens = Model().predict(calibration_features(p, seed=1))
    assert mod in MODALITIES and 0.0 <= sens <= 1.0


def test_training_learns_modality_above_chance():
    profs = sample_profiles(40, np.random.default_rng(3))
    clients = build_dataset(profs, examples_per=3)
    X = np.vstack([c[0] for c in clients])
    ym = np.concatenate([c[1] for c in clients])
    ys = np.concatenate([c[2] for c in clients])
    m = Model().train(X, ym, ys, epochs=300)
    ok = sum(int(m.predict(calibration_features(p, seed=123))[0] == p.modality) for p in profs)
    assert ok / len(profs) > 0.45  # clearly above 3-class chance (0.33)
