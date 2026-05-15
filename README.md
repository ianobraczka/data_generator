# data_generator

Generate synthetic pandas datasets from simple Python or YAML schemas, with support for weighted choices, reproducible seeds, and CSV/JSON export.

This is an educational project: plain functions, minimal dependencies, and no heavy framework beyond pandas, NumPy, Faker, PyYAML, and **optional** AI SDKs for schema assistance (install separately; see `requirements-ai.txt`).

## Clone and local setup

1. **Clone** the repository and enter its root (the directory that contains `requirements.txt` and the `data_generator/` package folder).

2. **Create your personal `.env`** (this file is **gitignored**; it never ships with the clone):

   ```bash
   ./scripts/init-local-env.sh
   ```

   Then open **`.env`** and set **`GEMINI_API_KEY`** (default provider) and/or **`OPENAI_API_KEY`**. On Windows without `sh`, copy manually: `cp .env.example .env` (Git Bash / WSL) or duplicate `.env.example` as `.env` in Explorer and edit.

3. **Install dependencies** (virtual environment recommended):

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-ai.txt   # for `ai-schema` (Gemini + OpenAI SDKs)
   pip install -r requirements-dev.txt   # optional: for pytest
   ```

4. **Run the CLI from the repo root** (or from any subdirectory of the repo). **python-dotenv** searches upward from the current working directory for a `.env` file, so keeping the file at the repo root matches a normal `git clone` workflow.

## AI-assisted schema generation

AI is used to assist with **schema creation**, while **dataset generation remains deterministic, validated, and reproducible** (`generate_dataset` fills rows; models never emit the final dataset).

**Providers:** **`gemini`** (default, recommended for hobby use with Google’s free tier) and **`openai`** (optional if you already have OpenAI API access). Install SDKs once:

```bash
pip install -r requirements-ai.txt
```

**Configuration:** use **Clone and local setup** so `.env` exists, then set **`GEMINI_API_KEY`** and/or **`OPENAI_API_KEY`**. Optional env vars: **`GEMINI_MODEL`**, **`OPENAI_MODEL`**. Shell exports override `.env` values.

**Gemini example — draft a schema, then generate rows:**

```bash
export GEMINI_API_KEY="your-gemini-api-key"

python -m data_generator ai-schema \
  --provider gemini \
  --prompt "Create a dataset for SaaS customers with name, email, plan, signup date, monthly revenue and churn risk" \
  --output examples/saas_customers.yaml

python -m data_generator generate \
  --rows 1000 \
  --schema examples/saas_customers.yaml \
  --output customers.csv \
  --seed 42
```

**OpenAI example:**

```bash
export OPENAI_API_KEY="your-openai-api-key"

python -m data_generator ai-schema \
  --provider openai \
  --model gpt-4o-mini \
  --prompt "Create an ecommerce orders dataset" \
  --output examples/orders.yaml
```

The CLI defaults to **`--provider gemini`**. Use **`--model`** to override the model for the active provider (otherwise `GEMINI_MODEL` / `OPENAI_MODEL` or built-in defaults apply).

**Supported field types** for AI output match the rest of the tool: `int`, `float`, `choice`, `weighted_choice`, `name`, `email`, `boolean`, `date`. Parsed output is validated with `validate_schema`; bad types or constraints produce clear errors (no automatic repair or retry loops).

In Python:

```python
from data_generator import generate_schema_from_prompt, save_schema_yaml

schema = generate_schema_from_prompt(
    "E-commerce orders with id, buyer email, status, total amount",
    provider="gemini",
)
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

Use `python -m data_generator ai-schema --help` for LLM-backed schema drafting (`--provider gemini|openai`, optional `--model`).

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

From the repo root (no live LLM calls; provider SDKs are not required for pytest):

```bash
pytest
```

## Project layout

- `data_generator/` — package: `ai_providers.py` (Gemini/OpenAI), `ai_schema.py`, distributions, validation, `generate_dataset`, exporters, CLI.
- `scripts/` — `init-local-env.sh` copies `.env.example` → `.env` for new clones.
- `examples/` — YAML schema and demo notebook.
- `tests/` — pytest coverage for generation, validation, exports, and AI schema (mocked).
