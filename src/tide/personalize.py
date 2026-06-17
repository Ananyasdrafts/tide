"""An on-device model that infers how to guide a person from a short calibration.

It watches a few calibration steps, how the person responds to each modality and how much
they hesitate, and predicts their preferred modality and how sensitive they are. A
personalised policy then uses that. The model is deliberately small (a softmax for modality,
a logistic for sensitivity, in numpy), because it has to be trainable locally on a phone and
shared only as weights, never raw behaviour. Federated training lives in ``federated.py``.
"""

from __future__ import annotations

import numpy as np

from .travelers import MODALITIES, Traveler, TravelerProfile

N_FEAT = 5
N_MOD = len(MODALITIES)


def calibration_features(profile: TravelerProfile, seed: int) -> np.ndarray:
    """Observable features from a short calibration: stress under each modality, plus
    hesitation and pace under a default probe. Lower stress under a modality hints it is
    preferred; overall responses hint at sensitivity."""
    feats = []
    # probe each modality under calm conditions, where the modality fit is the main thing
    # that moves stress; average a few short passes to cut the noise from random hesitation.
    for mi, m in enumerate(MODALITIES):
        stresses = []
        for trial in range(3):
            t = Traveler(profile, np.random.default_rng(seed + 7 * trial + 13 * mi))
            for _ in range(3):
                t.take_step(0.1, 0.2, m, 0.4)
            stresses.append(t.stress)
        feats.append(float(np.mean(stresses)))
    # a default-modality probe for pace and hesitation (sensitivity signal)
    t = Traveler(profile, np.random.default_rng(seed + 1))
    durs, hes = [], 0
    for _ in range(4):
        o = t.take_step(0.5, 0.4, "text", 0.5)
        durs.append(o.duration)
        hes += int(o.hesitated)
    feats.append(float(np.mean(durs)) / 10.0)
    feats.append(hes / 4.0)
    return np.array(feats, dtype=float)


def label(profile: TravelerProfile) -> tuple[int, float]:
    """The ground-truth (modality index, sensitivity) for a profile, used in the simulation."""
    return MODALITIES.index(profile.modality), float(profile.stress_gain)


class Model:
    """Softmax for modality + logistic for sensitivity, sharing the feature input."""

    def __init__(self, weights: np.ndarray | None = None):
        if weights is None:
            self.W = np.zeros((N_FEAT + 1, N_MOD))   # modality
            self.v = np.zeros(N_FEAT + 1)            # sensitivity
        else:
            self.set_weights(weights)

    @staticmethod
    def _x(X: np.ndarray) -> np.ndarray:
        X = np.atleast_2d(np.asarray(X, float))
        return np.hstack([X, np.ones((X.shape[0], 1))])

    def predict(self, feats: np.ndarray) -> tuple[str, float]:
        x = self._x(feats)
        modality = MODALITIES[int(np.argmax(x @ self.W, axis=1)[0])]
        sensitivity = float(1.0 / (1.0 + np.exp(-(x @ self.v)))[0])
        return modality, sensitivity

    def get_weights(self) -> np.ndarray:
        return np.concatenate([self.W.ravel(), self.v.ravel()])

    def set_weights(self, w: np.ndarray) -> None:
        cut = (N_FEAT + 1) * N_MOD
        self.W = w[:cut].reshape(N_FEAT + 1, N_MOD)
        self.v = w[cut:].reshape(N_FEAT + 1)

    def train(self, X, y_mod, y_sen, epochs: int = 200, lr: float = 0.3) -> "Model":
        x = self._x(X)
        n = x.shape[0]
        Y = np.eye(N_MOD)[np.asarray(y_mod, int)]
        y_sen = np.asarray(y_sen, float)
        for _ in range(epochs):
            logits = x @ self.W
            logits -= logits.max(axis=1, keepdims=True)
            p = np.exp(logits)
            p /= p.sum(axis=1, keepdims=True)
            self.W -= lr * (x.T @ (p - Y) / n)
            s = 1.0 / (1.0 + np.exp(-(x @ self.v)))
            self.v -= lr * (x.T @ (s - y_sen) / n)
        return self


def build_dataset(profiles, examples_per: int = 4, seed0: int = 0):
    """One client per profile, each with a few calibration examples (varying seed)."""
    clients = []
    for i, p in enumerate(profiles):
        X, ym, ys = [], [], []
        m, s = label(p)
        for k in range(examples_per):
            X.append(calibration_features(p, seed=seed0 + 1000 * i + k))
            ym.append(m)
            ys.append(s)
        clients.append((np.array(X), np.array(ym), np.array(ys)))
    return clients
