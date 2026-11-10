"""Wait for the game to cook a course DX, then replace its collision tree (R5T-INV E2.4).

usage: course_bsp_watch.py <source.gxm> <dx path> [--timeout seconds]

The retail game cooks ``<name>.dx`` from the GXM on the first load of the
course and keeps the file in use while it runs. This waits for a fresh DX
(size stable for 15 s), patches it with course_bsp_patch and retries until the
file can be replaced (at the latest when the game exits).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import course_bsp_patch  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("gxm", type=Path)
    parser.add_argument("dx", type=Path)
    parser.add_argument("--timeout", type=float, default=6 * 3600)
    args = parser.parse_args()
    marker = args.dx.with_suffix(".bsp.json")
    deadline = time.time() + args.timeout
    last = None
    while time.time() < deadline:
        if args.dx.exists():
            size = args.dx.stat().st_size
            done = marker.exists() and json.loads(marker.read_text(encoding="utf-8")).get("dx_size") == size
            if done:
                print("already patched", flush=True)
                return 0
            if last is not None and last[0] == size and time.time() - last[1] >= 15:
                try:
                    print(json.dumps(course_bsp_patch.patch(args.gxm, args.dx, args.dx)), flush=True)
                    return 0
                except PermissionError as error:
                    print(f"waiting for the game to release the DX: {error}", flush=True)
                    time.sleep(20)
                    continue
            if last is None or last[0] != size:
                last = (size, time.time())
        time.sleep(5)
    print("timeout", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
