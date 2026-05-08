#!/usr/bin/env python3
"""Render CoSAI agent skills for a target harness.

See scripts/agent/DESIGN.md §8 for behaviour.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = REPO_ROOT / "scripts" / "agent"
CONFIGS_DIR = AGENT_DIR / "configs"
MANIFEST_SCHEMA_PATH = AGENT_DIR / "manifest.schema.json"
CONFIG_SCHEMA_PATH = CONFIGS_DIR / "_config.schema.json"


def _load_yaml(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


def _load_json(path: Path) -> dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def _load_manifest(skill_dir: Path) -> dict[str, Any]:
    return _load_yaml(skill_dir / "manifest.yaml")


def _validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Return list of validation error messages; empty if valid."""
    schema = _load_json(MANIFEST_SCHEMA_PATH)
    errors = []
    for err in Draft202012Validator(schema).iter_errors(manifest):
        path = "/".join(str(p) for p in err.path) or "<root>"
        errors.append(f"{path}: {err.message}")
    return errors


def _validate_config(config: dict[str, Any]) -> list[str]:
    schema = _load_json(CONFIG_SCHEMA_PATH)
    errors = []
    for err in Draft202012Validator(schema).iter_errors(config):
        path = "/".join(str(p) for p in err.path) or "<root>"
        errors.append(f"{path}: {err.message}")
    return errors


def _list_skill_dirs() -> list[Path]:
    """Return all directories under scripts/agent/ that contain a manifest.yaml."""
    skills = []
    for entry in sorted(AGENT_DIR.iterdir()):
        if entry.is_dir() and (entry / "manifest.yaml").exists():
            skills.append(entry)
    return skills


def _list_config_files() -> list[Path]:
    """Return all top-level workstream configs (configs/<id>.yaml)."""
    return sorted(p for p in CONFIGS_DIR.glob("*.yaml") if not p.name.startswith("_"))


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="render.py",
        description="Render CoSAI agent skills for a target harness.",
    )
    p.add_argument("skill", nargs="?", help="Skill directory name (e.g. cosai-meeting-agenda).")
    p.add_argument("--target", choices=["claude-code", "generic"], default="claude-code")
    p.add_argument("--config", help="Workstream config slug (e.g. ws4) for path substitution.")
    p.add_argument("--output", help="Override destination directory.")
    p.add_argument("--symlink", action="store_true", default=True, help="Symlink files (default).")
    p.add_argument("--copy", dest="symlink", action="store_false", help="Copy files instead of symlinking.")
    p.add_argument("--dry-run", action="store_true", help="Validate and print intent; do not write.")
    p.add_argument("--validate-all", action="store_true", help="Validate every manifest and config; exit non-zero on failure.")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.validate_all:
        return _cmd_validate_all()

    if not args.skill:
        parser.error("the following arguments are required: skill (or use --validate-all)")

    print(f"render.py: skill={args.skill} target={args.target} (target rendering not yet implemented)", file=sys.stderr)
    return 0


def _cmd_validate_all() -> int:
    """Walk scripts/agent/, validate every manifest.yaml and config; exit non-zero on failure."""
    failures: list[str] = []

    for skill_dir in _list_skill_dirs():
        try:
            manifest = _load_manifest(skill_dir)
        except Exception as e:
            failures.append(f"{skill_dir.name}/manifest.yaml: parse error: {e}")
            continue
        errors = _validate_manifest(manifest)
        if errors:
            for e in errors:
                failures.append(f"{skill_dir.name}/manifest.yaml: {e}")
        else:
            print(f"OK   {skill_dir.name}/manifest.yaml", file=sys.stderr)

    for config_path in _list_config_files():
        try:
            config = _load_yaml(config_path)
        except Exception as e:
            failures.append(f"configs/{config_path.name}: parse error: {e}")
            continue
        errors = _validate_config(config)
        if errors:
            for e in errors:
                failures.append(f"configs/{config_path.name}: {e}")
        else:
            print(f"OK   configs/{config_path.name}", file=sys.stderr)

    if failures:
        print("\nValidation failures:", file=sys.stderr)
        for f in failures:
            print(f"  FAIL {f}", file=sys.stderr)
        return 1
    print("\nAll manifests and configs valid.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
