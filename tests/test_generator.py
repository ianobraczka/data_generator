"""Tests for schema validation, generation, and export."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from data_generator.cli import load_schema_from_yaml
from data_generator.exporters import to_csv, to_json
from data_generator.generator import generate_dataset


def _minimal_schema():
    return {
        "name": {"type": "name"},
        "age": {"type": "int", "min": 18, "max": 80},
        "city": {"type": "choice", "values": ["Rio", "São Paulo", "Curitiba"]},
        "plan": {
            "type": "weighted_choice",
            "values": ["free", "pro", "enterprise"],
            "weights": [0.7, 0.25, 0.05],
        },
        "active": {"type": "boolean"},
        "score": {"type": "float", "min": 0.0, "max": 1.0},
        "joined": {"type": "date", "min": "2020-01-01", "max": "2020-12-31"},
        "email": {"type": "email"},
    }


def test_row_count_and_columns():
    schema = _minimal_schema()
    df = generate_dataset(100, schema, seed=1)
    assert len(df) == 100
    assert list(df.columns) == list(schema.keys())


def test_reproducible_seed():
    s = {"x": {"type": "int", "min": 0, "max": 100}}
    a = generate_dataset(50, s, seed=42)
    b = generate_dataset(50, s, seed=42)
    pd.testing.assert_frame_equal(a, b)


def test_invalid_unknown_type():
    with pytest.raises(ValueError, match="unknown type"):
        generate_dataset(1, {"bad": {"type": "not_a_real_type"}}, seed=0)


def test_int_min_not_less_than_max():
    with pytest.raises(ValueError, match="min"):
        generate_dataset(1, {"x": {"type": "int", "min": 5, "max": 5}}, seed=0)


def test_weighted_choice_length_mismatch():
    with pytest.raises(ValueError, match="same length"):
        generate_dataset(
            1,
            {"x": {"type": "weighted_choice", "values": ["a", "b"], "weights": [1]}},
            seed=0,
        )


def test_weighted_choice_negative_weights():
    with pytest.raises(ValueError, match="non-negative"):
        generate_dataset(
            1,
            {"x": {"type": "weighted_choice", "values": ["a", "b"], "weights": [1, -1]}},
            seed=0,
        )


def test_csv_export(tmp_path: Path):
    df = generate_dataset(10, {"n": {"type": "int", "min": 1, "max": 3}}, seed=3)
    out = tmp_path / "t.csv"
    to_csv(df, out)
    loaded = pd.read_csv(out)
    assert len(loaded) == 10


def test_json_export(tmp_path: Path):
    df = generate_dataset(5, {"n": {"type": "int", "min": 1, "max": 3}}, seed=3)
    out = tmp_path / "t.json"
    to_json(df, out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) == 5


def test_load_yaml_schema():
    yaml_path = Path(__file__).resolve().parents[1] / "examples" / "users_schema.yaml"
    schema = load_schema_from_yaml(yaml_path)
    assert "email" in schema and schema["email"]["type"] == "email"
