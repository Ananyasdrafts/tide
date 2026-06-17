"""Federated training of the personalisation model (FedAvg).

Each person is a client that trains the model on their own calibration data and shares only
the resulting weights. The server averages the weights across clients, weighted by how much
data each has, and sends the average back. Raw behaviour never leaves the device. The
``centralized`` baseline trains one model on all the data pooled together, so we can check,
honestly, what (if anything) the privacy of federated learning costs in accuracy.
"""

from __future__ import annotations

import numpy as np

from .personalize import Model


def fed_avg(clients, rounds: int = 40, local_epochs: int = 5, lr: float = 0.3) -> Model:
    """clients: list of (X, y_mod, y_sen). Returns the global model after `rounds` of FedAvg."""
    global_w = Model().get_weights()
    total = sum(len(c[0]) for c in clients)
    for _ in range(rounds):
        agg = np.zeros_like(global_w)
        for X, ym, ys in clients:
            local = Model(global_w.copy()).train(X, ym, ys, epochs=local_epochs, lr=lr)
            agg += (len(X) / total) * local.get_weights()
        global_w = agg
    return Model(global_w)


def centralized(clients, rounds: int = 40, local_epochs: int = 5, lr: float = 0.3) -> Model:
    """Train one model on all clients' data pooled, matched roughly on total passes."""
    X = np.vstack([c[0] for c in clients])
    ym = np.concatenate([c[1] for c in clients])
    ys = np.concatenate([c[2] for c in clients])
    return Model().train(X, ym, ys, epochs=rounds * local_epochs, lr=lr)
