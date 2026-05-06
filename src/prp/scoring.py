from __future__ import annotations

import math


def posterior(deltas, beta=1.0, prior=None):
    k = len(deltas)
    if prior is None:
        prior = [1.0 / k] * k
    finite_scaled = [-beta * d for d in deltas if math.isfinite(d)]
    if not finite_scaled:
        return [1.0 / k] * k
    max_scaled = max(finite_scaled)
    weighted = []
    for d, p in zip(deltas, prior):
        if math.isfinite(d):
            weighted.append(math.exp(-beta * d - max_scaled) * p)
        else:
            weighted.append(0.0)
    total = sum(weighted)
    if total == 0:
        return [1.0 / k] * k
    return [w / total for w in weighted]


def predict(probabilities):
    if not probabilities:
        return 0, 0
    top = max(probabilities)
    indices = [i for i, p in enumerate(probabilities) if p == top]
    return indices[0], len(indices)
