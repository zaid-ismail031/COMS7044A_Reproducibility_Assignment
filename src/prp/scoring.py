from __future__ import annotations

import math


def posterior(deltas, beta=1.0, prior=None):
    k = len(deltas)
    if prior is None:
        prior = [1.0 / k] * k
    scaled = [-beta * d for d in deltas]
    max_scaled = max(scaled)
    exps = [math.exp(s - max_scaled) for s in scaled]
    weighted = [e * p for e, p in zip(exps, prior)]
    total = sum(weighted)
    if total == 0:
        return [1.0 / k] * k
    return [w / total for w in weighted]


def predict(probabilities):
    top = max(probabilities)
    indices = [i for i, p in enumerate(probabilities) if p == top]
    return indices[0], len(indices)
