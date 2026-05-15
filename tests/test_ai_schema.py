"""Tests for AI-assisted schema generation (mocked OpenAI; no real API calls)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from data_generator import cli
from data_generator.ai_schema import AISchemaError, generate_schema_from_prompt, save_schema_yaml


def _mock_openai_client(content: str) -> MagicMock:
    client = MagicMock()
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    client.chat.completions.create.return_value = resp
    return client


def test_generate_schema_success_validates(monkeypatch):
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    payload = {
        "fields": {
            "user_name": {"type": "name"},
            "score": {"type": "float", "min": 0.0, "max": 1.0},
        }
    }
    client = _mock_openai_client(json.dumps(payload))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    schema = generate_schema_from_prompt("make two columns", client=client)

    assert schema == payload["fields"]
    client.chat.completions.create.assert_called_once()
    kwargs = client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "gpt-4o-mini"
    assert "messages" in kwargs


def test_generate_schema_passes_custom_model(monkeypatch):
    payload = {"name": {"type": "name"}}
    client = _mock_openai_client(json.dumps(payload))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    generate_schema_from_prompt("x", model="gpt-test-model", client=client)
    assert client.chat.completions.create.call_args.kwargs["model"] == "gpt-test-model"


def test_generate_schema_from_yaml_style_body():
    body = "fields:\n  flag:\n    type: boolean\n"
    client = _mock_openai_client(body)
    schema = generate_schema_from_prompt("need a flag", client=client)
    assert schema == {"flag": {"type": "boolean"}}


def test_unsupported_field_type_rejected():
    payload = {"bad": {"type": "unicorn"}}
    client = _mock_openai_client(json.dumps({"fields": payload}))
    with pytest.raises(AISchemaError, match="Generated schema failed validation"):
        generate_schema_from_prompt("test", client=client)


def test_invalid_ai_response_raises():
    client = _mock_openai_client("{ invalid json")
    with pytest.raises(AISchemaError, match="Could not parse"):
        generate_schema_from_prompt("test", client=client)


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(AISchemaError, match="OPENAI_API_KEY"):
        generate_schema_from_prompt("hello there")


def test_empty_prompt_raises():
    with pytest.raises(AISchemaError, match="non-empty"):
        generate_schema_from_prompt("   ")


def test_cli_writes_yaml(tmp_path: Path, monkeypatch):
    schema = {"n": {"type": "int", "min": 0, "max": 10}}

    def fake_gen(prompt: str, model=None, client=None):
        assert "widgets" in prompt
        assert model == "cli-model"
        return schema

    monkeypatch.setattr(cli, "generate_schema_from_prompt", fake_gen)
    out = tmp_path / "out.yaml"
    rc = cli.main(
        [
            "ai-schema",
            "--prompt",
            "I need widgets",
            "--output",
            str(out),
            "--model",
            "cli-model",
        ]
    )
    assert rc == 0
    loaded = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert loaded["fields"] == schema


def test_cli_handles_invalid_response(tmp_path: Path, monkeypatch):
    def boom(prompt: str, model=None, client=None):
        raise AISchemaError("Model returned nonsense")

    monkeypatch.setattr(cli, "generate_schema_from_prompt", boom)
    rc = cli.main(
        ["ai-schema", "--prompt", "x", "--output", str(tmp_path / "o.yaml")]
    )
    assert rc == 1


def test_cli_optional_model_uses_default_in_function(monkeypatch, tmp_path):
    captured: dict = {}

    def capture(prompt: str, model=None, client=None):
        captured["model"] = model
        return {"a": {"type": "boolean"}}

    monkeypatch.setattr(cli, "generate_schema_from_prompt", capture)
    rc = cli.main(
        ["ai-schema", "--prompt", "y", "--output", str(tmp_path / "z.yaml")]
    )
    assert rc == 0
    assert captured["model"] is None


def test_save_schema_yaml_roundtrip(tmp_path: Path):
    schema = {"x": {"type": "int", "min": 1, "max": 2}}
    path = tmp_path / "s.yaml"
    save_schema_yaml(schema, path)
    from data_generator.cli import load_schema_from_yaml

    assert load_schema_from_yaml(path) == schema
