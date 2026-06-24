#!/usr/bin/env python3
"""Rollback the module-reference migration to the previous schema state.

This restores the legacy foreign-key columns by moving back to migration 0004.
The schema is reverted, but the data behind the legacy references is not
reconstructed automatically.
"""

from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from purchase_entrys.scripts._runtime import run_manage


def main() -> None:
    run_manage("migrate", "purchase_entrys", "0004")


if __name__ == "__main__":
    main()
