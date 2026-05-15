"""Command-line interface for schema-based synthetic data generation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from data_generator.exporters import to_csv, to_json, to_parquet
from data_generator.generator import generate_dataset


def load_schema_from_yaml(path: str | Path) -> dict[str, Any]:
    """Load a ``fields:`` mapping from a YAML file into a flat column schema dict."""
    p = Path(path)
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("YAML root must be a mapping")
    fields = raw.get("fields")
    if not isinstance(fields, dict) or not fields:
        raise ValueError("YAML must contain a non-empty 'fields' mapping")
    return dict(fields)


def export_dataframe(df, output: Path) -> None:
    """Save ``df`` using the file extension to pick format."""
    suffix = output.suffix.lower()
    if suffix == ".csv":
        to_csv(df, output)
    elif suffix == ".json":
        to_json(df, output)
    elif suffix in (".parquet", ".pq"):
        try:
            to_parquet(df, output)
        except ImportError as exc:
            raise SystemExit(
                "Parquet export requires pyarrow (pip install pyarrow)."
            ) from exc
    else:
        raise SystemExit(
            f"Unsupported output format {suffix!r}. Use .csv, .json, or .parquet."
        )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="data_generator", description="Synthetic tabular data from schemas.")
    sub = p.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate", help="Generate a dataset from a YAML schema")
    gen.add_argument("--rows", type=int, required=True, help="Number of rows")
    gen.add_argument("--schema", type=Path, required=True, help="Path to YAML schema file")
    gen.add_argument("--output", type=Path, required=True, help="Output file (.csv, .json, .parquet)")
    gen.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "generate":
        try:
            schema = load_schema_from_yaml(args.schema)
            df = generate_dataset(args.rows, schema, seed=args.seed)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            export_dataframe(df, args.output)
        except (yaml.YAMLError, ValueError, TypeError, OSError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(f"Wrote {len(df)} rows, {len(df.columns)} columns -> {args.output}")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
