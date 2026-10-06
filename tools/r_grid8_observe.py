"""Capture an R-GRID8 active-race snapshot into this phase's ignored output."""
from __future__ import annotations

import argparse
from pathlib import Path

from r_ai1_mixed_class import REPOSITORY, ignored_output
from r_grid8_candidate import EXPECTED_CANDIDATE_SHA256, verify as verify_candidate
from research_build_profiles import resolve_build
from r_ai1_observe import load_profile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observatory", required=True, type=Path,
                        help="directory containing the exact audited Observatory files")
    parser.add_argument("--candidate", required=True, type=Path,
                        help="staged MRallye.exe currently running the game")
    parser.add_argument("label", help="active-race label, e.g. grid8-france1")
    args = parser.parse_args()

    data = args.candidate.read_bytes()
    if len(data) != 3_121_214 or verify_candidate(data)["output_sha256"] != EXPECTED_CANDIDATE_SHA256:
        raise ValueError("Need the exact R-GRID8 candidate")
    profile = resolve_build(data)
    if (profile.get("profile_origin") != "locally_audited" or
            profile.get("compatibility_family") != "retail-broker-v1"):
        raise ValueError("Candidate did not resolve through the fail-closed retail Broker family")
    observe = load_profile(args.observatory, args.candidate)

    # Keep this phase's captures, raw sidecars, local config and launcher beneath
    # the general-re ignored output tree, not the historical R-OBS2 output root.
    root = ignored_output(REPOSITORY / ".research-output" / "general-re" / "grid8" / "observatory")
    observe.REPO = root
    observe.DATA_ROOT = root / "observatory-data"
    observe.DEFAULT_CAPTURE_ROOT = observe.DATA_ROOT / "captures"
    observe.DEFAULT_CONFIG = observe.DATA_ROOT / "config.json"
    return_code = observe.main(["--exe", str(args.candidate.resolve()), "capture", args.label])
    if return_code:
        raise SystemExit(return_code)


if __name__ == "__main__":
    main()
