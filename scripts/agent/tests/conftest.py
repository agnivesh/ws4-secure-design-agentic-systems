"""Shared pytest fixtures for scripts/agent/ tests."""
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
AGENT_DIR = REPO_ROOT / "scripts" / "agent"


@pytest.fixture
def agent_dir() -> Path:
    """Absolute path to scripts/agent/ in the repo."""
    return AGENT_DIR


@pytest.fixture
def fixtures_dir() -> Path:
    """Absolute path to scripts/agent/tests/fixtures/."""
    return Path(__file__).parent / "fixtures"
