#!/usr/bin/env python3
"""Public Vehicle Composer entrypoint; implementation lives in physics_bind."""
from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.physics_bind import build_parser as _build_parser  # noqa: E402
from tools.physics_bind import main as _main  # noqa: E402


def build_parser():
    """Build the canonical parser with the public command name."""
    return _build_parser(program_name="python tools/vehicle_composer.py")


def main(argv: list[str] | None = None) -> int:
    """Dispatch through the existing Vehicle Composer implementation."""
    return _main(argv, program_name="python tools/vehicle_composer.py")


if __name__ == "__main__":
    raise SystemExit(main())
