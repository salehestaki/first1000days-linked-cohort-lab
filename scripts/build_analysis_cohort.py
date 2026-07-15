#!/usr/bin/env python3
"""Build deterministic exposure, analysis, sibling, trajectory, and flow artefacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from first1000days_lab.bootstrap import bootstrap_repository  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--force", action="store_true", help="Regenerate source data before rebuilding")
    args = parser.parse_args()
    result = bootstrap_repository(args.root, force=args.force)
    print(result)


if __name__ == "__main__":
    main()
