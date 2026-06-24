"""Shared runtime helpers for the purchase_entrys phase-6 scripts."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def find_repo_root() -> Path:
    """Walk upward until we find the Django project root."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "manage.py").exists():
            return parent
    raise RuntimeError("Could not locate manage.py from purchase_entrys/scripts")


def manage_py_path() -> Path:
    return find_repo_root() / "manage.py"


def run_manage(*args: str) -> None:
    """Run a Django management command in the project context."""
    env = os.environ.copy()
    env.setdefault("DJANGO_SETTINGS_MODULE", "PROCUREMENT.settings")
    subprocess.run(
        [sys.executable, str(manage_py_path()), *args],
        check=True,
        cwd=str(find_repo_root()),
        env=env,
    )

