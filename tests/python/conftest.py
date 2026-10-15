# FROZEN — DO NOT MODIFY (plan/PLAN.md, tests/FROZEN_MANIFEST.sha256). Requirement, decision and claim IDs are cited per test.
import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))


def need_env(name: str, step: str) -> str:
    """Environment input for a test, asserted with the variable and the plan step that sets it (PK-26)."""
    value = os.environ.get(name, "")
    assert value, f"{name} is not set (set by plan step {step}; see HANDOFF.md)"
    return value


@pytest.fixture
def root() -> pathlib.Path:
    return ROOT
