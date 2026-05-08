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
