"""Schema validation tests for scripts/agent/."""
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


def load_yaml(path: Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def manifest_schema(agent_dir: Path) -> dict:
    return load_json(agent_dir / "manifest.schema.json")


def test_manifest_schema_loads(manifest_schema: dict):
    Draft202012Validator.check_schema(manifest_schema)


def test_valid_manifest_passes(manifest_schema: dict, fixtures_dir: Path):
    manifest = load_yaml(fixtures_dir / "valid_manifest.yaml")
    Draft202012Validator(manifest_schema).validate(manifest)


def test_invalid_manifest_missing_field_fails(manifest_schema: dict, fixtures_dir: Path):
    manifest = load_yaml(fixtures_dir / "invalid_manifest_missing_field.yaml")
    with pytest.raises(ValidationError):
        Draft202012Validator(manifest_schema).validate(manifest)


def test_invalid_manifest_unknown_nested_field_fails(manifest_schema: dict, fixtures_dir: Path):
    """Nested objects use additionalProperties: false; unknown keys (not x-*) must fail."""
    manifest = load_yaml(fixtures_dir / "invalid_manifest_unknown_field.yaml")
    with pytest.raises(ValidationError):
        Draft202012Validator(manifest_schema).validate(manifest)


@pytest.fixture
def config_schema(agent_dir: Path) -> dict:
    return load_json(agent_dir / "configs" / "_config.schema.json")


def test_config_schema_loads(config_schema: dict):
    Draft202012Validator.check_schema(config_schema)


def test_valid_config_passes(config_schema: dict, fixtures_dir: Path):
    config = load_yaml(fixtures_dir / "valid_config.yaml")
    Draft202012Validator(config_schema).validate(config)


def test_config_with_unresolved_extends_passes_schema(config_schema: dict, fixtures_dir: Path):
    """Schema does NOT enforce that extends resolves; that's render.py's job."""
    config = load_yaml(fixtures_dir / "config_with_unresolved_extends.yaml")
    # Schema-level validation passes — extends references are resolved
    # by the renderer, which catches unresolved parents separately (see test_render.py).
    Draft202012Validator(config_schema).validate(config)
