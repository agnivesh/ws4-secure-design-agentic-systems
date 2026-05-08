#!/usr/bin/env python3
"""Render CoSAI agent skills for a target harness.

See scripts/agent/DESIGN.md §8 for behaviour.
"""
from __future__ import annotations

import argparse
import functools
import json
import shutil
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
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@functools.lru_cache(maxsize=8)
def _load_json_cached(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_manifest(skill_dir: Path) -> dict[str, Any]:
    return _load_yaml(skill_dir / "manifest.yaml")


def _format_validation_errors(instance: dict[str, Any], schema_path: Path) -> list[str]:
    """Validate `instance` against the schema at `schema_path`.

    Returns a list of human-readable error messages; empty list means valid.
    """
    schema = _load_json_cached(schema_path)
    errors = []
    for err in Draft202012Validator(schema).iter_errors(instance):
        path = "/".join(str(p) for p in err.path) or "<root>"
        errors.append(f"{path}: {err.message}")
    return errors


def _validate_manifest(manifest: dict[str, Any]) -> list[str]:
    return _format_validation_errors(manifest, MANIFEST_SCHEMA_PATH)


def _validate_config(config: dict[str, Any]) -> list[str]:
    return _format_validation_errors(config, CONFIG_SCHEMA_PATH)


def _deep_merge(parent: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge child onto parent. Object fields merge; arrays fully replace; scalars override; null clears."""
    if not isinstance(parent, dict) or not isinstance(child, dict):
        return child
    result = dict(parent)
    for key, child_val in child.items():
        if child_val is None and key in result:
            del result[key]
            continue
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(child_val, dict)
        ):
            result[key] = _deep_merge(result[key], child_val)
        else:
            # Scalars and arrays replace.
            result[key] = child_val
    return result


def resolve_config(config_path: Path, configs_dir: Path | None = None) -> dict[str, Any]:
    """Load a config, resolving a single-level `extends:` chain.

    Raises FileNotFoundError if extends points at a missing parent.
    Raises ValueError if a chain longer than one level is encountered.
    """
    configs_dir = configs_dir or CONFIGS_DIR
    config = _load_yaml(config_path)

    parent_id = config.get("extends")
    if not parent_id:
        return config

    parent_path = configs_dir / f"{parent_id}.yaml"
    if not parent_path.exists():
        raise FileNotFoundError(
            f"{config_path.name}: extends '{parent_id}' but {parent_path} does not exist"
        )

    parent = _load_yaml(parent_path)
    if parent.get("extends"):
        raise ValueError(
            f"{config_path.name} extends {parent_id}, which itself extends "
            f"{parent['extends']}. Inheritance is single-level only."
        )

    if parent.get("schema_version") != config.get("schema_version"):
        raise ValueError(
            f"{config_path.name} schema_version {config.get('schema_version')} "
            f"does not match parent {parent_path.name} "
            f"schema_version {parent.get('schema_version')}"
        )

    merged = _deep_merge(parent, config)
    merged.pop("extends", None)
    return merged


def _claude_code_frontmatter(manifest: dict[str, Any]) -> str:
    """Build the YAML frontmatter Claude Code requires."""
    description = " ".join(manifest["description"].split())  # collapse whitespace to single line
    return (
        "---\n"
        f"name: {manifest['name']}\n"
        f"description: {description}\n"
        "---\n"
    )


def _manifest_context_block(manifest: dict[str, Any]) -> str:
    """Build the auto-generated 'Skill Contract' block injected into rendered SKILL.md."""
    summary = {
        k: manifest[k]
        for k in ("arguments", "dependencies", "composition", "output", "boundaries")
        if k in manifest
    }
    yaml_text = yaml.safe_dump(summary, sort_keys=False)
    return (
        "## Skill Contract (auto-generated from manifest.yaml; do not edit)\n\n"
        "```yaml\n"
        f"{yaml_text}"
        "```\n\n"
        "See `scripts/agent/<skill>/manifest.yaml` for canonical.\n\n"
    )


def render_claude_code(
    skill_dir: Path,
    output_dir: Path,
    *,
    manifest: dict[str, Any] | None = None,
    symlink: bool = True,
    repo_root: Path | None = None,
) -> Path:
    """Render a skill for Claude Code. Returns the path of the written SKILL.md."""
    if manifest is None:
        manifest = _load_manifest(skill_dir)
    errors = _validate_manifest(manifest)
    if errors:
        raise ValueError(f"manifest validation failed for {skill_dir.name}: {errors}")

    skill_body_path = skill_dir / manifest.get("narrative", "SKILL.md")
    skill_body = skill_body_path.read_text()
    # Render-time path substitution: replace <repo_root> with the absolute repo path.
    if repo_root is None:
        repo_root = REPO_ROOT
    skill_body = skill_body.replace("<repo_root>", str(repo_root))

    rendered = (
        _claude_code_frontmatter(manifest)
        + "\n"
        + _manifest_context_block(manifest)
        + skill_body
    )

    target_dir = output_dir / manifest["name"]
    target_dir.mkdir(parents=True, exist_ok=True)
    target_skill = target_dir / "SKILL.md"

    if symlink:
        # Write the rendered SKILL.md to a staging file in the source tree
        # and symlink it from the destination so source-tree edits to the
        # manifest get picked up on next render and live SKILL.md edits
        # are visible immediately.
        staging = skill_dir / ".rendered.SKILL.md"
        tmp = staging.with_suffix(".tmp")
        tmp.write_text(rendered)
        tmp.replace(staging)
        target_skill.unlink(missing_ok=True)
        target_skill.symlink_to(staging.resolve())
    else:
        # Copy mode: atomic write to the destination.
        tmp = target_skill.with_suffix(".tmp")
        tmp.write_text(rendered)
        tmp.replace(target_skill)

    # Sibling files: any data dep with runtime_role: input and a relative path
    # that resolves to an in-repo file gets installed alongside SKILL.md.
    deps = manifest.get("dependencies", {})
    for data_dep in deps.get("data", []) or []:
        if data_dep.get("runtime_role") != "input":
            continue
        prov = data_dep.get("provisioning", {})
        if not prov.get("tracked_in_repo"):
            continue
        rel_path = data_dep.get("path", "")
        if "/" in rel_path or rel_path.startswith("{"):
            # Path templates or repo-rooted paths aren't sibling files.
            continue
        src = skill_dir / rel_path
        if not src.exists():
            continue
        dest = target_dir / rel_path
        dest.unlink(missing_ok=True)
        if symlink:
            dest.symlink_to(src.resolve())
        else:
            shutil.copy2(src, dest)

    return target_skill


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

    if args.target == "generic":
        print("Generic-prompt rendering deferred to v2; CLI accepts the flag for forward-compat.", file=sys.stderr)
        manifest = _load_manifest(AGENT_DIR / args.skill)
        print(yaml.safe_dump({k: manifest.get(k) for k in ("name", "version", "arguments")}, sort_keys=False), file=sys.stderr)
        return 2

    skill_dir = AGENT_DIR / args.skill
    if not skill_dir.exists():
        print(f"render.py: skill {args.skill!r} not found at {skill_dir}", file=sys.stderr)
        return 1

    output_dir = Path(args.output) if args.output else Path.home() / ".claude" / "skills"

    if args.dry_run:
        print(f"DRY RUN: would render {args.skill} -> {output_dir / args.skill}", file=sys.stderr)
        manifest = _load_manifest(skill_dir)
        errors = _validate_manifest(manifest)
        if errors:
            print(f"Manifest validation failures: {errors}", file=sys.stderr)
            return 1
        return 0

    manifest = _load_manifest(skill_dir)
    target_path = render_claude_code(skill_dir, output_dir, manifest=manifest, symlink=args.symlink)
    print(f"Rendered {args.skill} -> {target_path}", file=sys.stderr)

    # Out-of-band data deps reminder
    for data_dep in manifest.get("dependencies", {}).get("data", []) or []:
        if data_dep.get("provisioning", {}).get("kind") == "out-of-band":
            populated_by = data_dep.get("provisioning", {}).get("populated_by", {})
            tool = populated_by.get("tool", "(unknown)")
            print(f"Reminder: data path {data_dep['path']} is populated out-of-band by {tool}", file=sys.stderr)

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
