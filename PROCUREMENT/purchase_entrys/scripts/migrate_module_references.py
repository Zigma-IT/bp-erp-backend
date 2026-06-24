#!/usr/bin/env python3
"""Apply the purchase_entrys module-reference migration."""

from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from purchase_entrys.scripts._runtime import run_manage


def main() -> None:
    run_manage("migrate", "purchase_entrys", "0005")


if __name__ == "__main__":
    main()
