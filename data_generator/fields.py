"""
Field-type registry, validation, and column generation for schema-driven datasets.

Each field spec is a dict with at least ``{"type": "<type_name>"}`` and type-specific keys.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

import numpy as np
from faker import Faker
from numpy.random import Generator

SUPPORTED_FIELD_TYPES: frozenset[str] = frozenset(
    {
        "int",
        "float",
        "choice",
        "weighted_choice",
        "name",
        "email",
        "boolean",
        "date",
    }
)


def validate_field_spec(column: str, spec: Any) -> None:
    """Raise ``ValueError`` or ``TypeError`` if ``spec`` is not a valid field definition."""
    if not isinstance(spec, dict):
        raise TypeError(f"Column {column!r}: spec must be a dict, got {type(spec).__name__}")
    t = spec.get("type")
    if t is None:
        raise ValueError(f"Column {column!r}: missing 'type'")
    if t not in SUPPORTED_FIELD_TYPES:
        raise ValueError(
            f"Column {column!r}: unknown type {t!r}. "
            f"Supported: {', '.join(sorted(SUPPORTED_FIELD_TYPES))}"
        )

    if t in ("int", "float"):
        if "min" not in spec or "max" not in spec:
            raise ValueError(f"Column {column!r}: type {t!r} requires 'min' and 'max'")
        lo, hi = spec["min"], spec["max"]
        if lo >= hi:
            raise ValueError(f"Column {column!r}: min ({lo}) must be less than max ({hi})")

    if t == "choice":
        vals = spec.get("values")
        if not vals or not isinstance(vals, (list, tuple)):
            raise ValueError(f"Column {column!r}: choice requires non-empty 'values' list")

    if t == "weighted_choice":
        vals = spec.get("values")
        weights = spec.get("weights")
        if not vals or not isinstance(vals, (list, tuple)):
            raise ValueError(f"Column {column!r}: weighted_choice requires 'values' list")
        if weights is None or not isinstance(weights, (list, tuple)):
            raise ValueError(f"Column {column!r}: weighted_choice requires 'weights' list")
        if len(vals) != len(weights):
            raise ValueError(
                f"Column {column!r}: weighted_choice 'values' and 'weights' "
                f"must have the same length (got {len(vals)} vs {len(weights)})"
            )
        w = np.asarray(weights, dtype=float)
        if (w < 0).any():
            raise ValueError(f"Column {column!r}: weights must be non-negative")
        if w.sum() <= 0:
            raise ValueError(f"Column {column!r}: weights must sum to a positive number")

    if t == "boolean":
        if "probability_true" in spec:
            p = float(spec["probability_true"])
            if not 0.0 <= p <= 1.0:
                raise ValueError(f"Column {column!r}: probability_true must be between 0 and 1")

    if t == "date":
        dmin = spec.get("min", "2000-01-01")
        dmax = spec.get("max", "2025-12-31")
        try:
            d0 = dt.date.fromisoformat(str(dmin))
            d1 = dt.date.fromisoformat(str(dmax))
        except ValueError as exc:
            raise ValueError(f"Column {column!r}: invalid date min/max (use ISO YYYY-MM-DD)") from exc
        if d0 >= d1:
            raise ValueError(f"Column {column!r}: date min must be before max")


def validate_schema(schema: dict[str, Any]) -> None:
    """Validate all columns in a schema dict."""
    if not schema:
        raise ValueError("schema must contain at least one column")
    for col, spec in schema.items():
        validate_field_spec(str(col), spec)


def column_values(rng: Generator, fake: Faker, n: int, spec: dict[str, Any]) -> list[Any]:
    """Generate ``n`` values for one column according to ``spec``."""
    t = spec["type"]

    if t == "int":
        lo, hi = int(spec["min"]), int(spec["max"])
        return rng.integers(lo, hi + 1, size=n).tolist()

    if t == "float":
        lo, hi = float(spec["min"]), float(spec["max"])
        return [round(float(x), 6) for x in rng.uniform(lo, hi, size=n)]

    if t == "choice":
        vals = list(spec["values"])
        idx = rng.integers(0, len(vals), size=n)
        return [vals[i] for i in idx]

    if t == "weighted_choice":
        vals = list(spec["values"])
        w = np.asarray(spec["weights"], dtype=float)
        w = w / w.sum()
        idx = rng.choice(len(vals), size=n, p=w)
        return [vals[i] for i in idx]

    if t == "name":
        return [fake.name() for _ in range(n)]

    if t == "email":
        return [fake.email() for _ in range(n)]

    if t == "boolean":
        p = float(spec.get("probability_true", 0.5))
        return (rng.random(size=n) < p).tolist()

    if t == "date":
        d0 = dt.date.fromisoformat(str(spec.get("min", "2000-01-01")))
        d1 = dt.date.fromisoformat(str(spec.get("max", "2025-12-31")))
        span = (d1 - d0).days
        offsets = rng.integers(0, span + 1, size=n)
        return [d0 + dt.timedelta(days=int(o)) for o in offsets]

    raise ValueError(f"Unhandled type {t!r}")
