"""Schema-driven dataset generation and legacy examples."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from faker import Faker

from data_generator.distributions import (
    random_floats,
    random_ints,
    random_values,
    random_values_with_probs,
)
from data_generator.fields import column_values, validate_schema


def legacy_sample_frame(rows: int = 500, *, seed: int | None = None) -> pd.DataFrame:
    """
    Build the same toy DataFrame as the original Colab snippet (columns A–D).

    This preserves the teaching example: floats, ints, categorical, weighted categorical.
    """
    df = pd.DataFrame()
    base = seed
    df["A"] = random_floats(rows, 1.4, 5.4, seed=base)
    df["B"] = random_ints(rows, 10, 90, seed=None if base is None else base + 1)
    df["C"] = random_values(rows, ["bom", "otimo", "excelente"], seed=None if base is None else base + 2)
    df["D"] = random_values_with_probs(
        rows,
        ["bom", "otimo", "excelente"],
        [0.7, 0.2, 0.1],
        seed=None if base is None else base + 3,
    )
    return df


def generate_dataset(rows: int, schema: dict[str, Any], *, seed: int | None = None) -> pd.DataFrame:
    """
    Build a DataFrame with ``rows`` rows from a column schema.

    ``schema`` maps column names to field specs. Results are reproducible when ``seed``
    is set (numpy RNG + Faker seed).
    """
    if rows < 1:
        raise ValueError("rows must be >= 1")
    validate_schema(schema)
    rng = np.random.default_rng(seed)
    fake = Faker()
    if seed is not None:
        fake.seed_instance(seed)
    data = {col: column_values(rng, fake, rows, spec) for col, spec in schema.items()}
    return pd.DataFrame(data)
