# data_generator

Generate synthetic pandas datasets from simple Python or YAML schemas, with support for weighted choices, reproducible seeds, and CSV/JSON export.

This is a small, educational project: plain functions, minimal dependencies, and no heavy framework beyond pandas, NumPy, Faker, and PyYAML.

## Installation

From the project root (prefer a virtual environment):

```bash
pip install -r requirements.txt
```

For tests:

```bash
pip install -r requirements-dev.txt
```

## Python usage

```python
from data_generator import generate_dataset

schema = {
    "name": {"type": "name"},
    "age": {"type": "int", "min": 18, "max": 80},
    "city": {"type": "choice", "values": ["Rio", "São Paulo", "Curitiba"]},
    "plan": {
        "type": "weighted_choice",
        "values": ["free", "pro", "enterprise"],
        "weights": [0.7, 0.25, 0.05],
    },
}

df = generate_dataset(1000, schema, seed=42)
print(df.head())
```

The original teaching DataFrame (columns A–D) is still available as `legacy_sample_frame`.

## YAML schema example

See `examples/users_schema.yaml`:

```yaml
fields:
  name:
    type: name
  age:
    type: int
    min: 18
    max: 80
  email:
    type: email
  city:
    type: choice
    values:
      - Rio de Janeiro
      - São Paulo
      - Curitiba
  subscription:
    type: weighted_choice
    values: [free, pro, enterprise]
    weights: [0.7, 0.25, 0.05]
  active:
    type: boolean
```

## CLI usage

```bash
python -m data_generator generate --rows 1000 --schema examples/users_schema.yaml --output users.csv --seed 42
```

The output format is chosen from the file extension: `.csv`, `.json`, or `.parquet`. Parquet needs an extra engine such as `pyarrow` (`pip install pyarrow`).

## Supported field types

| Type | Required keys | Notes |
|------|----------------|-------|
| `int` | `min`, `max` | Inclusive range; `min` must be less than `max`. |
| `float` | `min`, `max` | Uniform floats in `[min, max)`. |
| `choice` | `values` | Uniform random pick from the list. |
| `weighted_choice` | `values`, `weights` | Same length; weights must be non-negative and sum to a positive value. |
| `name` | — | Faker person name. |
| `email` | — | Faker email. |
| `boolean` | — | Optional `probability_true` in `[0, 1]`. |
| `date` | — | Optional ISO `min` / `max` (default span roughly 2000–2025). |

## Running tests

```bash
pytest
```

## Project layout

- `data_generator/` — package: distributions, field validation, `generate_dataset`, exporters, CLI.
- `examples/` — YAML schema and demo notebook.
- `tests/` — pytest coverage for generation, validation, and exports.
