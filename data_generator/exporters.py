"""Write pandas DataFrames to files (extended in phase 3 for CLI)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def to_csv(df: pd.DataFrame, path: str | Path) -> None:
    """Write ``df`` to CSV without the index column."""
    df.to_csv(path, index=False)


def to_json(df: pd.DataFrame, path: str | Path, *, orient: str = "records") -> None:
    """Write ``df`` to JSON (default: list of row records)."""
    df.to_json(path, orient=orient, indent=2, force_ascii=False)


def to_parquet(df: pd.DataFrame, path: str | Path) -> None:
    """Write ``df`` to Parquet (requires ``pyarrow`` or ``fastparquet``)."""
    df.to_parquet(path, index=False)


def to_parquet(df: pd.DataFrame, path: str | Path) -> None:
    """Write ``df`` to Parquet (requires ``pyarrow`` or ``fastparquet``)."""
    df.to_parquet(path, index=False)
