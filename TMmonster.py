#!/usr/bin/env python3
"""Run tmmonster from a local source checkout without installing."""

from pathlib import Path
import sys


def main() -> int:
    repo_root = Path(__file__).resolve().parent
    src_dir = repo_root / "src"
    sys.path.insert(0, str(src_dir))

    from tmmonster.cli import cli_main

    cli_main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
