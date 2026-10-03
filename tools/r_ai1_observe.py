"""Use an audited external Observatory with one exact R-AI1 research profile.

The external distribution remains unchanged. Its capture/UI implementations
are reused; every native memory location and command ID retains retail layout.
All generated settings/captures stay in this checkout's ignored output.
"""
from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

from r_ai1_mixed_class import (CANDIDATE_SHA256, REPOSITORY, ignored_output,
                              sha256, verify_candidate)

OBSERVATORY_FILES = {
    "broker_observatory.py": "d1a07eab330ef3d8b825ef3320b458d20ced11df99d75250a72e9c7701c4ba7d",
    "dev_command_trigger.py": "6da763eb605e7bb397f39ef78d909bfc5952e869f59eca6650bb710847c37cbe",
    "mr_observe.py": "ad3c1ec4b6209cb4a3a1d9ed19b3e1f2ed19ccb4b6c3ecb8a2beeebfbf91cbb8",
    "observatory_version.py": "43d54f1ac1922c40cc68ac301a9dade645a66db3d0b3f9f72e68a2844cfe4526",
}


def verify_distribution(directory: Path) -> None:
    for name, expected in OBSERVATORY_FILES.items():
        if sha256((directory / name).read_bytes()) != expected:
            raise ValueError(f"Observatory implementation changed: {name}; audit required")


def load_profile(directory: Path, candidate: Path):
    verify_candidate(candidate.read_bytes())
    directory = directory.resolve()
    verify_distribution(directory)
    for name in ("broker_observatory", "dev_command_trigger", "mr_observe", "observatory_version"):
        if name in sys.modules:
            raise ValueError("Observatory already loaded; use a fresh process for this exact profile")
    sys.dont_write_bytecode = True  # Do not create external __pycache__ research artifacts.
    sys.path.insert(0, str(directory))
    observe = importlib.import_module("mr_observe")
    core, commands = observe.core, observe.commands
    # Exact audited implementation, exact candidate, retail image size/base/RVAs.
    core.RETAIL_SHA256 = commands.RETAIL_SHA256 = CANDIDATE_SHA256
    original_verify = observe.verify_executable
    def verify_executable(path):
        try:
            original_verify(path)  # Retains basename, size, exact hash and file gates.
        except observe.UserError as exc:
            raise observe.UserError("R-AI1 requires the exact generated MRallye.exe profile.",
                                    f"Expected SHA256: {CANDIDATE_SHA256}") from exc
        verify_candidate(path.read_bytes())  # Inverse manifest must restore pristine exactly.
    observe.verify_executable = verify_executable
    observe.PORTABLE = True
    observe.REPO = REPOSITORY / ".research-output/r-ai1/observatory"
    observe.DATA_ROOT = observe.REPO / "observatory-data"
    observe.DEFAULT_CAPTURE_ROOT = observe.DATA_ROOT / "captures"
    observe.DEFAULT_CONFIG = observe.DATA_ROOT / "config.json"
    original_root = observe.capture_root_for
    observe.capture_root_for = lambda args, config: ignored_output(original_root(args, config))
    original_save = observe.save_config
    observe.save_config = lambda path, config: original_save(ignored_output(path), config)
    original_launcher = observe.setup_launcher
    observe.setup_launcher = lambda output, exe: original_launcher(ignored_output(output), exe)
    return observe


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observatory", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    arguments = args.arguments
    if arguments[:1] == ["--"]:
        arguments = arguments[1:]
    observe = load_profile(args.observatory, args.candidate)
    print("R-AI1 exact profile:", CANDIDATE_SHA256)
    return observe.main(["--exe", str(args.candidate.resolve()), *arguments])


if __name__ == "__main__":
    raise SystemExit(main())
