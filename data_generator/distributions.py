"""Low-level random column builders (numpy-backed for reproducible seeds)."""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from numpy.random import Generator
from faker import Faker


def _rng(seed: int | None) -> Generator:
    return np.random.default_rng(seed)


def random_floats(n: int, a: float, b: float, *, seed: int | None = None) -> list[float]:
    """Return ``n`` floats in ``[a, b]``, each rounded to 3 decimal places (original behaviour)."""
    rng = _rng(seed)
    return [round(float(x), 3) for x in rng.uniform(a, b, size=n)]


def random_ints(n: int, a: int, b: int, *, seed: int | None = None) -> list[int]:
    """Return ``n`` integers uniformly from ``a`` through ``b`` inclusive."""
    if a > b:
        raise ValueError(f"min ({a}) must be <= max ({b})")
    rng = _rng(seed)
    return rng.integers(low=a, high=b + 1, size=n).tolist()


def random_values(n: int, values: Sequence[Any], *, seed: int | None = None) -> list[Any]:
    """Return ``n`` independent picks from ``values`` with uniform probability."""
    if not values:
        raise ValueError("values must be non-empty")
    rng = _rng(seed)
    idx = rng.integers(0, len(values), size=n)
    return [values[i] for i in idx]


def random_values_with_probs(
    n: int,
    values: Sequence[Any],
    p: Sequence[float] | None = None,
    *,
    seed: int | None = None,
) -> list[Any]:
    """
    Return ``n`` picks from ``values`` using probability vector ``p``.

    If ``p`` is omitted, every value is equally likely.
    """
    if not values:
        raise ValueError("values must be non-empty")
    if p is not None and len(p) != len(values):
        raise ValueError("p must have the same length as values")
    rng = _rng(seed)
    if p is None:
        p_use = np.ones(len(values)) / len(values)
    else:
        p_use = np.asarray(p, dtype=float)
        s = p_use.sum()
        if s <= 0:
            raise ValueError("probabilities must sum to a positive number")
        p_use = p_use / s
    choices = rng.choice(len(values), size=n, p=p_use)
    return [values[i] for i in choices]


def random_names(n: int, *, seed: int | None = None) -> list[str]:
    """Return ``n`` synthetic person names using Faker."""
    fake = Faker()
    if seed is not None:
        fake.seed_instance(seed)
    return [fake.name() for _ in range(n)]


def constant_column(n: int, value: Any) -> list[Any]:
    """Return ``n`` copies of ``value`` (handy for fixed labels per group)."""
    return [value] * n
