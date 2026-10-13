from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


PORT = Path(__file__).resolve().parents[1]
BUILD_REPORT = PORT / "dist" / "current" / "build-report.json"
DLL_RELATIVE = Path("dist/current/ps2-enabled/d3d8.dll")
OUTPUT = PORT / "dist" / "PC-VISUAL-PILOT1.3-handoff.zip"

FILES = (
    "README.md",
    "HANDOFF.md",
    "implementation.md",
    "runtime-ab.md",
    "validation.md",
    "PS2Port.ini.example",
    "renderer/ps2_port_extension.hpp",
    "renderer/ps2_port_extension.cpp",
    "tests/ps2_port_extension_tests.cpp",
    "tests/test_integration_contract.py",
    "overlay/README.md",
    "overlay/command-log.md",
    "overlay/baseline-lock.json",
    "overlay/build_overlay.py",
    "overlay/package_handoff.py",
    "overlay/patches/0001-renderer-integration.patch",
    "overlay/patches/0002-interface-generator.patch",
    "docs/architecture.md",
    "docs/pilot1.2-design.md",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    report = json.loads(BUILD_REPORT.read_text(encoding="utf-8"))
    if report["builds"]["ps2-enabled"]["build"] != "PASS":
        raise SystemExit("PS2-enabled build is not marked PASS in build-report.json")
    dll = PORT / DLL_RELATIVE
    if sha256(dll.read_bytes()) != report["builds"]["ps2-enabled"]["dll_sha256"]:
        raise SystemExit("PS2-enabled DLL hash does not match build-report.json")

    members: dict[str, bytes] = {}
    for relative in FILES:
        path = PORT / relative
        if not path.is_file():
            raise SystemExit(f"Required handoff file is missing: {path}")
        members[f"pc-port/{relative}"] = path.read_bytes()
    members["artifacts/ps2-enabled/d3d8.dll"] = dll.read_bytes()
    members["build-report.json"] = BUILD_REPORT.read_bytes()
    manifest = "".join(f"{sha256(data)}  {name}\n" for name, data in sorted(members.items()))
    members["SHA256SUMS.txt"] = manifest.encode("utf-8")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members.items()):
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=ZIP_DEFLATED, compresslevel=9)

    with ZipFile(OUTPUT, "r") as archive:
        stored = {name: archive.read(name) for name in archive.namelist()}
    expected = set(members)
    if set(stored) != expected:
        raise SystemExit("Handoff ZIP member set did not round-trip")
    lines = stored.pop("SHA256SUMS.txt").decode("utf-8").splitlines()
    parsed = {line.split("  ", 1)[1]: line.split("  ", 1)[0] for line in lines}
    if set(parsed) != set(stored) or any(sha256(data) != parsed[name] for name, data in stored.items()):
        raise SystemExit("Handoff ZIP SHA-256 manifest verification failed")
    if sha256(stored["artifacts/ps2-enabled/d3d8.dll"]) != report["builds"]["ps2-enabled"]["dll_sha256"]:
        raise SystemExit("Handoff DLL does not match the verified build")

    archive_hash = sha256(OUTPUT.read_bytes())
    OUTPUT.with_suffix(OUTPUT.suffix + ".sha256").write_text(
        f"{archive_hash}  {OUTPUT.name}\n", encoding="ascii"
    )
    print(f"Handoff: {OUTPUT}")
    print(f"Handoff SHA-256: {archive_hash}")
    print(f"PS2 DLL SHA-256: {report['builds']['ps2-enabled']['dll_sha256']}")
    print(f"Verified members: {len(stored) + 1}")


if __name__ == "__main__":
    main()
