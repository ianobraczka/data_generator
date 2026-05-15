"""Higher-level helpers that compose distributions into DataFrames."""

from __future__ import annotations

import pandas as pd

from data_generator.distributions import (
    random_floats,
    random_ints,
    random_values,
    random_values_with_probs,
)


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
