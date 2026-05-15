"""Tests for AI-assisted schema generation (mocked providers; no real API calls)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from data_generator import cli
from data_generator.ai_providers import (
    GeminiProvider,
    OpenAIProvider,
    ProviderError,
    get_provider,
)
from data_generator.ai_schema import AISchemaError, generate_schema_from_prompt, save_schema_yaml


class FakeProvider:
    def __init__(self, text: str) -> None:
        self._text = text
        self.calls: list[tuple[str, str]] = []

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        return self._text


def test_generate_schema_success_validates():
    payload = {
        "fields": {
            "user_name": {"type": "name"},
            "score": {"type": "float", "min": 0.0, "max": 1.0},
        }
    }
    prov = FakeProvider(json.dumps(payload))
    schema = generate_schema_from_prompt("make two columns", provider="gemini", _provider=prov)
    assert schema == payload["fields"]
    assert "synthetic tabular" in prov.calls[0][0].lower()
    assert prov.calls[0][1] == "make two columns"


def test_generate_schema_passes_custom_model_openai():
    payload = {"name": {"type": "name"}}
    prov = FakeProvider(json.dumps(payload))
    generate_schema_from_prompt("x", provider="openai", model="gpt-custom", _provider=prov)
    assert prov.calls[0][1] == "x"


def test_generate_schema_from_yaml_style_body():
    body = "fields:\n  flag:\n    type: boolean\n"
    prov = FakeProvider(body)
    schema = generate_schema_from_prompt("need a flag", _provider=prov)
    assert schema == {"flag": {"type": "boolean"}}


def test_unsupported_field_type_rejected():
    payload = {"bad": {"type": "unicorn"}}
    prov = FakeProvider(json.dumps({"fields": payload}))
    with pytest.raises(AISchemaError, match="Generated schema failed validation"):
        generate_schema_from_prompt("test", _provider=prov)


def test_invalid_ai_response_raises():
    prov = FakeProvider("{ invalid json")
    with pytest.raises(AISchemaError, match="Could not parse"):
        generate_schema_from_prompt("test", _provider=prov)


def test_empty_prompt_raises():
    with pytest.raises(AISchemaError, match="non-empty"):
        generate_schema_from_prompt("   ", _provider=FakeProvider("{}"))


def test_unsupported_provider_raises():
    with pytest.raises(ValueError, match="Unsupported"):
        get_provider("anthropic")


def test_gemini_missing_api_key(monkeypatch):
    monkeypatch.setattr(
        "data_generator.ai_providers._import_genai",
        lambda: MagicMock(),
    )
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="GEMINI_API_KEY"):
        GeminiProvider()


def test_gemini_configures_api_key(monkeypatch):
    fake_genai = MagicMock()
    monkeypatch.setattr("data_generator.ai_providers._import_genai", lambda: fake_genai)
    monkeypatch.setenv("GEMINI_API_KEY", "k-test")
    g = GeminiProvider(model="my-gemini-model")
    assert g._model_name == "my-gemini-model"
    fake_genai.configure.assert_called_once_with(api_key="k-test")


def test_openai_missing_api_key(monkeypatch):
    class DummyClient:
        def __init__(self, **kwargs):
            pass

    monkeypatch.setattr(
        "data_generator.ai_providers._import_openai_client",
        lambda: DummyClient,
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ProviderError, match="OPENAI_API_KEY"):
        OpenAIProvider()


def test_cli_writes_yaml(tmp_path: Path, monkeypatch):
    schema = {"n": {"type": "int", "min": 0, "max": 10}}

    def fake_gen(prompt, provider="gemini", model=None, _provider=None):
        assert "widgets" in prompt
        assert provider == "openai"
        assert model == "cli-model"
        return schema

    monkeypatch.setattr(cli, "generate_schema_from_prompt", fake_gen)
    out = tmp_path / "out.yaml"
    rc = cli.main(
        [
            "ai-schema",
            "--provider",
            "openai",
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


def test_cli_defaults_to_gemini(tmp_path: Path, monkeypatch):
    captured: dict = {}

    def capture(prompt, provider="gemini", model=None, _provider=None):
        captured["provider"] = provider
        captured["model"] = model
        return {"a": {"type": "boolean"}}

    monkeypatch.setattr(cli, "generate_schema_from_prompt", capture)
    rc = cli.main(
        ["ai-schema", "--prompt", "y", "--output", str(tmp_path / "z.yaml")]
    )
    assert rc == 0
    assert captured["provider"] == "gemini"
    assert captured["model"] is None


def test_cli_handles_ai_error(tmp_path: Path, monkeypatch):
    def boom(prompt, provider="gemini", model=None, _provider=None):
        raise AISchemaError("bad response")

    monkeypatch.setattr(cli, "generate_schema_from_prompt", boom)
    rc = cli.main(
        ["ai-schema", "--prompt", "x", "--output", str(tmp_path / "o.yaml")]
    )
    assert rc == 1


def test_cli_handles_valueerror(tmp_path: Path, monkeypatch):
    def boom(prompt, provider="gemini", model=None, _provider=None):
        raise ValueError("nope")

    monkeypatch.setattr(cli, "generate_schema_from_prompt", boom)
    rc = cli.main(
        ["ai-schema", "--prompt", "x", "--output", str(tmp_path / "o.yaml")]
    )
    assert rc == 1


def test_save_schema_yaml_roundtrip(tmp_path: Path):
    schema = {"x": {"type": "int", "min": 1, "max": 2}}
    path = tmp_path / "s.yaml"
    save_schema_yaml(schema, path)
    from data_generator.cli import load_schema_from_yaml

    assert load_schema_from_yaml(path) == schema


def test_provider_error_surfaces_as_aischema_error():
    class P:
        def generate_text(self, system_prompt: str, user_prompt: str) -> str:
            raise ProviderError("quota exceeded")

    with pytest.raises(AISchemaError, match="quota exceeded"):
        generate_schema_from_prompt("hi", _provider=P())
