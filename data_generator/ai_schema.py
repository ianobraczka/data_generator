"""
AI-assisted generation of dataset schemas (YAML-shaped dicts) via the OpenAI API.

The model only proposes a schema; ``generate_dataset`` still produces rows deterministically.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from openai import OpenAI

from data_generator.fields import SUPPORTED_FIELD_TYPES, validate_schema

# Load `.env` from the process working directory (walks up parent dirs). After clone, run
# `./scripts/init-local-env.sh` once from the repo root, then edit `.env`.
load_dotenv(override=False)

DEFAULT_MODEL = "gpt-4o-mini"


class AISchemaError(Exception):
    """Raised when AI schema generation, parsing, or validation fails."""


def _system_prompt() -> str:
    types = ", ".join(sorted(SUPPORTED_FIELD_TYPES))
    return (
        "You are a schema designer for a small synthetic tabular data tool.\n\n"
        "Your task: given a user description, output ONLY a schema — not data rows, not CSV, "
        "not explanations.\n\n"
        "Rules:\n"
        "- Do NOT generate the dataset or sample values. Only the schema.\n"
        "- Do NOT invent field types. Allowed types exactly: "
        f"{types}.\n"
        "- Use realistic snake_case or clear column names. Keep schemas small and practical.\n"
        "- Use type \"choice\" with a \"values\" list for uniform categories.\n"
        "- Use type \"weighted_choice\" with \"values\" and \"weights\" lists of equal length "
        "only when probabilities matter (e.g. plan tiers). Otherwise prefer \"choice\".\n"
        "- For \"int\" and \"float\", always include \"min\" and \"max\" with min < max.\n"
        "- For \"date\", use ISO \"min\" and \"max\" strings (YYYY-MM-DD) with min before max, "
        "or omit min/max for defaults.\n"
        "- For \"boolean\", you may omit \"probability_true\" (defaults to 0.5).\n"
        "- Output MUST be raw YAML or raw JSON only: no markdown, no code fences, no commentary.\n"
        "Preferred YAML shape:\n"
        "fields:\n"
        "  column_name:\n"
        "    type: <one of the allowed types>\n"
        "    ...\n"
        "You may instead output a single JSON object with a top-level \"fields\" key mapping "
        "column names to field spec objects.\n"
    )


def _strip_markdown_fences(text: str) -> str:
    """Remove optional ``` / ```yaml fences if the model adds them despite instructions."""
    t = text.strip()
    if not t.startswith("```"):
        return t
    t = re.sub(r"^```[a-zA-Z0-9]*\s*", "", t, count=1)
    if t.rstrip().endswith("```"):
        t = t.rstrip()[:-3].rstrip()
    return t


def _parse_schema_payload(text: str) -> Any:
    """Parse model output as JSON first, then YAML."""
    stripped = _strip_markdown_fences(text.strip())
    if not stripped:
        raise AISchemaError("Model returned empty content after stripping whitespace.")
    try:
        data = json.loads(stripped)
    except json.JSONDecodeError:
        try:
            data = yaml.safe_load(stripped)
        except yaml.YAMLError as exc:
            raise AISchemaError(
                "Could not parse model output as YAML or JSON. "
                "Ensure the model returns only a schema object."
            ) from exc
    if isinstance(data, str):
        raise AISchemaError("Parsed content was a plain string; expected a schema object.")
    if data is None:
        raise AISchemaError("Parsed content was empty or null.")
    return data


def _normalize_to_column_schema(raw: Any) -> dict[str, Any]:
    """Turn parsed YAML/JSON into the flat column -> spec dict used by ``generate_dataset``."""
    if not isinstance(raw, dict):
        raise AISchemaError("Parsed schema must be a JSON/YAML object (mapping).")
    if "fields" in raw and isinstance(raw["fields"], dict) and raw["fields"]:
        return {str(k): v for k, v in raw["fields"].items()}
    if raw and all(isinstance(v, dict) and "type" in v for v in raw.values()):
        return {str(k): v for k, v in raw.items()}
    raise AISchemaError(
        "Schema must be a non-empty 'fields' mapping or a flat mapping of column names to "
        "objects with a 'type' key."
    )


def _default_client() -> OpenAI:
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key:
        raise AISchemaError(
            "OPENAI_API_KEY is not set. Export it in your environment or use a .env file "
            "(see .env.example)."
        )
    return OpenAI(api_key=key)


def generate_schema_from_prompt(
    prompt: str,
    model: str | None = None,
    *,
    client: Any | None = None,
) -> dict[str, Any]:
    """
    Call OpenAI to produce a column schema from natural language, then validate it.

    Returns a flat ``dict`` mapping column names to field specs (same shape as
    ``generate_dataset`` expects). Does not generate dataset rows.

    ``client`` may be injected for tests; otherwise ``OPENAI_API_KEY`` must be set.
    """
    if not (prompt or "").strip():
        raise AISchemaError("prompt must be a non-empty string.")

    resolved_model = (model or os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL).strip()
    api_client = client if client is not None else _default_client()

    try:
        response = api_client.chat.completions.create(
            model=resolved_model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": _system_prompt()},
                {"role": "user", "content": prompt.strip()},
            ],
        )
    except Exception as exc:
        raise AISchemaError(f"OpenAI API request failed: {exc}") from exc

    choice = response.choices[0] if response.choices else None
    content = getattr(getattr(choice, "message", None), "content", None)
    if content is None or not str(content).strip():
        raise AISchemaError("Model returned no usable text content.")

    raw = _parse_schema_payload(str(content))
    schema = _normalize_to_column_schema(raw)
    try:
        validate_schema(schema)
    except (ValueError, TypeError) as exc:
        raise AISchemaError(f"Generated schema failed validation: {exc}") from exc
    return schema


def save_schema_yaml(schema: dict[str, Any], path: str | Path) -> None:
    """Write ``schema`` to ``path`` as YAML with a top-level ``fields:`` block."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = yaml.dump(
        {"fields": schema},
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )
    p.write_text(payload, encoding="utf-8")
