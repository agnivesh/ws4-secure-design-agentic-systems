#!/usr/bin/env python3
"""Render CoSAI agent skills for a target harness.

See scripts/agent/DESIGN.md §8 for behaviour.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = REPO_ROOT / "scripts" / "agent"
CONFIGS_DIR = AGENT_DIR / "configs"


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

    # Stub for now; real dispatch comes in later tasks.
    print(f"render.py: skill={args.skill} target={args.target} (stub)", file=sys.stderr)
    return 0


def _cmd_validate_all() -> int:
    """Stub; real implementation in a later task."""
    print("render.py --validate-all (stub)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
