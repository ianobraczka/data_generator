# data_generator

Generate synthetic pandas datasets from simple Python or YAML schemas, with support for weighted choices, reproducible seeds, and CSV/JSON export.

This is an educational project: plain functions, minimal dependencies, and no heavy framework beyond pandas, NumPy, Faker, PyYAML, and the OpenAI Python client (for the optional AI schema helper).

## Clone and local setup

1. **Clone** the repository and enter its root (the directory that contains `requirements.txt` and the `data_generator/` package folder).

2. **Create your personal `.env`** (this file is **gitignored**; it never ships with the clone):

   ```bash
   ./scripts/init-local-env.sh
   ```

   Then open **`.env`** and set **`OPENAI_API_KEY`** (and optionally **`OPENAI_MODEL`**). On Windows without `sh`, copy manually: `cp .env.example .env` (Git Bash / WSL) or duplicate `.env.example` as `.env` in Explorer and edit.

3. **Install dependencies** (virtual environment recommended):

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt   # optional: for pytest
   ```

4. **Run the CLI from the repo root** (or from any subdirectory of the repo). **python-dotenv** searches upward from the current working directory for a `.env` file, so keeping the file at the repo root matches a normal `git clone` workflow.

## AI-assisted schema generation

This is a **developer productivity** feature: the model drafts a **schema only**. Dataset generation stays **deterministic**, **validated**, and **reproducible** via `generate_dataset` and the existing field types — AI assists with schema creation; rows are still produced only by the generator.

**Why schemas, not rows?** Letting the model emit raw data would be harder to test, less predictable, and riskier. Here the model proposes structure; your generator fills values under the same rules as hand-written YAML.

**Setup:** follow **Clone and local setup** to create `.env` with `OPENAI_API_KEY`. You can also `export OPENAI_API_KEY=...` in your shell (environment variables override values from `.env`).

**Step 1 — ask the model for a schema:**

```bash
python -m data_generator ai-schema \
  --prompt "Create a dataset for SaaS customers with name, email, plan, signup date, monthly revenue and churn risk" \
  --output examples/saas_customers.yaml
```

Optional: `--model gpt-4o-mini` (overrides `OPENAI_MODEL` / built-in default).

**Step 2 — generate rows with the normal pipeline:**

```bash
python -m data_generator generate \
  --rows 1000 \
  --schema examples/saas_customers.yaml \
  --output customers.csv \
  --seed 42
```

**Supported field types** for AI output are the same as the rest of the tool: `int`, `float`, `choice`, `weighted_choice`, `name`, `email`, `boolean`, `date`. After parsing, the schema is run through `validate_schema`; unsupported types or bad constraints surface as clear errors.

In Python:

```python
from data_generator import generate_schema_from_prompt, save_schema_yaml

schema = generate_schema_from_prompt("E-commerce orders with id, buyer email, status, total amount")
save_schema_yaml(schema, "examples/orders.yaml")
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

Use `python -m data_generator ai-schema --help` for the OpenAI-powered schema helper (see **AI-assisted schema generation** above).

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

- `data_generator/` — package: distributions, field validation, `generate_dataset`, AI schema helper (`ai_schema.py`), exporters, CLI.
- `scripts/` — `init-local-env.sh` copies `.env.example` → `.env` for new clones.
- `examples/` — YAML schema and demo notebook.
- `tests/` — pytest coverage for generation, validation, exports, and AI schema (mocked).
