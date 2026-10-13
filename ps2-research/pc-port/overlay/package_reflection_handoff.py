#!/usr/bin/env python3
"""Package the bounded PS2-REFLECTION-PORT1 handoff after a verified build.

This script never stages, builds, patches, deploys or changes game data. It
checks the immutable renderer tree, reviewed patches and current PS2 sources
against the final build report, then packages an explicit source allowlist and
the two independently built proxy DLLs. Original game assets are excluded.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path, PurePosixPath
import struct
import subprocess
import sys
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "ps2-research" / "pc-port"
OVERLAY = PORT / "overlay"
DOCS = PORT / "docs" / "reflection-port1"
REPORT = DOCS / "build-report.json"
OUTPUT = PORT / "dist" / "PS2-REFLECTION-PORT1-handoff.zip"
FIXED_TIMESTAMP = (2026, 1, 1, 0, 0, 0)

# Paths in the archive match the repository, so imports and research links keep
# their normal relative layout. The complete frozen renderer is not copied.
PORT_FILES = (
    ".gitignore",
    "README.md",
    "HANDOFF.md",
    "implementation.md",
    "runtime-ab.md",
    "validation.md",
    "PS2Port.ini.example",
    "PILOT1.4-HANDOFF.md",
    "docs/architecture.md",
    "docs/pilot1.2-design.md",
    "docs/pilot1.4-pixel-provenance.md",
    "tools/prepare_reflection_pilot.py",
    "overlay/baseline-lock.json",
    "overlay/build_overlay.py",
    "overlay/package_reflection_handoff.py",
    "overlay/README.md",
    "overlay/patches/0001-renderer-integration.patch",
    "overlay/patches/0002-interface-generator.patch",
)
REQUIRED_FINAL_DOCS = (
    "final-report.md",
    "validation.md",
    "command-log.md",
    "design-and-implementation.md",
    "runtime-ab.md",
    "build-report.json",
    "material-source-contract.json",
    "material-negative-controls.json",
    "pc-executable-cross-check.json",
    "next.md",
)
REFL1_FILES = (
    "final-report.md", "findings.md", "material-contract.md",
    "vehicle-mesh-binding.md", "vehicle-case-studies.md",
    "reflection-resource-inventory.md", "environment-target-lifecycle.md",
    "environment-coordinate-math.md", "body-reflection.md",
    "glass-and-windscreen.md", "chrome-and-trim.md",
    "gs-state-and-blending.md", "draw-pipeline.md", "pc-comparison.md",
    "portability-notes.md", "validation.md", "render-contract.json",
    "resource-evidence.json", "vehicle-evidence.json", "elf-functions.json",
    "provenance.json", "synthetic-coordinate-input.json",
)
# Import closure used by prepare_reflection_pilot.py. Course SDK itself remains
# an external read-only dependency; no second parser or archive decoder exists.
RESEARCH_TOOLS = (
    "reflection_runtime.py", "water_runtime.py", "detail_runtime.py",
    "psbtool.py", "tngtool.py", "course_delta.py", "build_report.py",
)
SOURCE_SUFFIXES = {".cpp", ".hpp", ".py"}
DOCUMENT_SUFFIXES = {".md", ".json"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_required(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise RuntimeError(f"Required regular handoff file is missing: {path}")
    resolved = path.resolve()
    if not resolved.is_relative_to(ROOT.resolve()):
        raise RuntimeError(f"Handoff input escapes the repository: {path}")
    return path.read_bytes()


def relative_name(path: Path) -> str:
    name = path.relative_to(ROOT).as_posix()
    pure = PurePosixPath(name)
    if pure.is_absolute() or ".." in pure.parts or "\\" in name:
        raise RuntimeError(f"Unsafe archive source path: {name}")
    return name


def current_ps2_sources() -> dict[str, Path]:
    return {
        path.relative_to(PORT).as_posix(): path
        for folder in (PORT / "renderer", PORT / "tests")
        for path in sorted(folder.rglob("*"))
        if path.is_file() and path.suffix in SOURCE_SUFFIXES
    }


def verify_build_inputs(report: dict, lock: dict) -> dict[str, Path]:
    """Verify source/DLL provenance without modifying staging or baseline."""
    spec = importlib.util.spec_from_file_location(
        "reflection_handoff_build_overlay", OVERLAY / "build_overlay.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load the existing build-overlay verifier")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    identity = builder.verify_renderer_identity(ROOT, lock)
    for field in ("baseline_head", "renderer_tree", "branch"):
        if report[field] != identity[field]:
            raise RuntimeError(f"Build report has a different {field}")
    # Unrelated commits are permitted by the renderer-tree lock. The report's
    # original current_head need not equal current HEAD after research commits.
    for relative, expected in lock["files"].items():
        data = subprocess.check_output(
            ["git", "show", f"{lock['baseline_head']}:{relative}"], cwd=ROOT)
        if sha256(data) != expected["sha256"]:
            raise RuntimeError(f"Frozen Git-object hash mismatch: {relative}")
    patch_names = set(builder.PATCH_PATHS)
    if set(report["patch_sha256"]) != patch_names or set(lock["patches"]) != patch_names:
        raise RuntimeError("Unexpected or missing exact integration patch")
    for name in sorted(patch_names):
        actual = sha256(read_required(OVERLAY / "patches" / name))
        if actual != report["patch_sha256"][name] or actual != lock["patches"][name]["sha256"]:
            raise RuntimeError(f"Integration patch differs from the verified build: {name}")
    sources = current_ps2_sources()
    if not sources or set(sources) != set(report["ps2_source_sha256"]):
        raise RuntimeError("Current PS2 source/test file set differs from the verified build")
    staged_relative = PurePosixPath(report["staging"]["ps2_port_root"])
    if staged_relative.is_absolute() or ".." in staged_relative.parts:
        raise RuntimeError("Unsafe PS2 source staging path in the build report")
    staged_port = ROOT.joinpath(*staged_relative.parts)
    if not staged_port.resolve().is_relative_to(PORT.resolve()):
        raise RuntimeError("PS2 source staging path escapes the port build root")
    for name, path in sorted(sources.items()):
        if sha256(read_required(path)) != report["ps2_source_sha256"][name]:
            raise RuntimeError(f"PS2 source/test differs from the verified build: {name}")
        staged = staged_port.joinpath(*PurePosixPath(name).parts)
        if sha256(read_required(staged)) != report["ps2_source_sha256"][name]:
            raise RuntimeError(f"PS2 staged source/test differs from the verified build: {name}")
    if report.get("ps2_port_tests") != "PASS" or not report.get("dll_distinct"):
        raise RuntimeError("Focused PS2 tests or independent DLL build identity is not PASS")
    for variant in ("baseline", "ps2-enabled"):
        entry = report["builds"][variant]
        if any(entry.get(key) != "PASS" for key in ("build", "ctest", "proxy_verification")):
            raise RuntimeError(f"{variant} build, CTest or proxy verification is not PASS")
        if not report["generator"][variant].get("deterministic"):
            raise RuntimeError(f"{variant} interface generator is not verified deterministic")
        if report["generator"][variant]["outputs"] != lock["generated_outputs"][variant]:
            raise RuntimeError(f"{variant} generated-interface contract differs from its lock")
    return sources


def verified_dll(report: dict, variant: str) -> bytes:
    entry = report["builds"][variant]
    relative = PurePosixPath(entry["dll"])
    if relative.is_absolute() or ".." in relative.parts or "\\" in entry["dll"]:
        raise RuntimeError(f"Unsafe build-report DLL path for {variant}")
    dll = ROOT.joinpath(*relative.parts)
    if not dll.resolve().is_relative_to(PORT.resolve()) or dll.name != "d3d8.dll":
        raise RuntimeError(f"Unexpected build-report proxy path: {dll}")
    data = read_required(dll)
    if sha256(data) != entry["dll_sha256"]:
        raise RuntimeError(f"{variant} DLL differs from the verified build report")
    if len(data) < 64 or data[:2] != b"MZ":
        raise RuntimeError(f"{variant} output is not a PE DLL")
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if pe + 24 > len(data) or data[pe:pe + 4] != b"PE\0\0":
        raise RuntimeError(f"{variant} output has an invalid PE header")
    machine = struct.unpack_from("<H", data, pe + 4)[0]
    characteristics = struct.unpack_from("<H", data, pe + 22)[0]
    if machine != 0x14C or not characteristics & 0x2000:
        raise RuntimeError(f"{variant} output is not a Win32/x86 DLL")
    return data


def handoff_text(report: dict) -> str:
    prefix = "ps2-research/pc-port/docs/reflection-port1"
    return f"""# PS2-REFLECTION-PORT1 compact handoff

Start with [{prefix}/final-report.md]({prefix}/final-report.md), then follow
[{prefix}/runtime-ab.md]({prefix}/runtime-ab.md) for the manual one-car A/B.
This archive contains source, exact staged integration patches, tests, compact
research evidence and two separately built Win32 Release proxy DLLs. It does
not include original game executables, geometry, textures or a renderer copy.

## Verified source and artifacts

- Immutable baseline Git commit: `{report['baseline_head']}`.
- Frozen `modernization/renderer` tree: `{report['renderer_tree']}`.
- Baseline proxy: `artifacts/baseline/d3d8.dll`, SHA-256
  `{report['builds']['baseline']['dll_sha256']}`.
- PS2-enabled proxy: `artifacts/ps2-enabled/d3d8.dll`, SHA-256
  `{report['builds']['ps2-enabled']['dll_sha256']}`.
- `SHA256SUMS.txt` hashes every archive member except itself. The archive
  `.sha256` sidecar hashes the complete ZIP. Sources keep repository paths.

## Dependencies and commands

Native rebuilding requires an external Git checkout containing the locked
baseline commit and renderer tree, Python, CMake and the Windows Visual Studio
18 2026 Win32/MSVC toolchain used by the build script. Apply the included
`ps2-research` source files to that checkout while preserving unrelated work;
do not modify `modernization/renderer`. From the repository root, run:

```powershell
python ps2-research/pc-port/overlay/build_overlay.py
python ps2-research/pc-port/overlay/package_reflection_handoff.py
```

These are reproducible command recipes. The actually executed commands and
test results are recorded in `{prefix}/command-log.md` and `validation.md`.
Staging uses verified immutable Git objects and exact patches. Unrelated
research commits are accepted when the frozen renderer tree is identical.
Historical architecture and PILOT1.4 documents describe earlier checkpoints;
the final reflection report and current lock/build script govern this bundle.

Synthetic native tests require the staged baseline headers and Windows
toolchain but no private game data. The renderer-tree Python tests use local
temporary Git repositories; full Python integration tests inspect the staged
renderer and compact included evidence. Set `MRR_PC_PORT_RENDERER_ROOT` to its
PS2-enabled staging path when running those integration tests separately.

Original asset preparation additionally requires the canonical private PS2
PackFS corpus, protected retail PC corpus and separate read-only Course SDK
checkout. The included `tools/prepare_reflection_pilot.py` reuses included
research parsers plus that SDK. It writes the verified original environment
GXI only into ignored local `.assets`; the GXI is deliberately absent here.
The opt-in reflection mode fails closed without the verified local image.
See `runtime-ab.md` for exact private input roots and asset-preparation options.
The enabled-image Reset subcase requires `MRR_REFLECTION_TEST_GXI` pointing to
the verified local GXI; it explicitly reports NOT_PERFORMED without that input.
It was run and passed in this handoff's original validation. Synthetic tests do
not require original images. The included port `.gitignore` keeps local assets,
builds and diagnostics out of Git.

## Runtime boundary

Manual installation into an isolated PC test setup is the user's choice; the
packager installs nothing. Both DLLs are individual D3D8 proxies, never a
chain. Stock defaults include `FoliageMode=0`, `PixelProbe=0` and
`ReflectionMode=0`. Keep camera, car, paint, lighting and quality settings fixed
for the reflection A/B. Live visual acceptance and PS2 parity are not implied
by successful builds, synthetic tests or archive integrity. PILOT1.4 pixel
readback remains a separate pending runtime diagnostic.
"""


def collect_members(report: dict, sources: dict[str, Path]) -> dict[str, bytes]:
    for name in REQUIRED_FINAL_DOCS:
        read_required(DOCS / name)
    members: dict[str, bytes] = {}
    paths = [PORT / name for name in PORT_FILES]
    paths += list(sources.values())
    paths += [ROOT / "ps2-research" / "refl1" / name for name in REFL1_FILES]
    paths += [ROOT / "ps2-research" / "tools" / name for name in RESEARCH_TOOLS]
    for path in sorted(DOCS.rglob("*")):
        if path.is_file():
            if path.suffix not in DOCUMENT_SUFFIXES:
                raise RuntimeError(f"Unexpected non-document in final research directory: {path}")
            paths.append(path)
    for path in sorted(set(paths)):
        members[relative_name(path)] = read_required(path)
    for variant in ("baseline", "ps2-enabled"):
        members[f"artifacts/{variant}/d3d8.dll"] = verified_dll(report, variant)
    if members["artifacts/baseline/d3d8.dll"] == members["artifacts/ps2-enabled/d3d8.dll"]:
        raise RuntimeError("Baseline and PS2-enabled DLL contents are unexpectedly identical")
    members["HANDOFF.md"] = handoff_text(report).encode("utf-8")
    manifest = "".join(f"{sha256(data)}  {name}\n" for name, data in sorted(members.items()))
    members["SHA256SUMS.txt"] = manifest.encode("utf-8")
    return members


def archive_bytes(members: dict[str, bytes]) -> bytes:
    stream = io.BytesIO()
    with ZipFile(stream, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members.items()):
            info = ZipInfo(name, date_time=FIXED_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=ZIP_DEFLATED, compresslevel=9)
    return stream.getvalue()


def verify_archive(data: bytes, members: dict[str, bytes]) -> None:
    with ZipFile(io.BytesIO(data), "r") as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Archive CRC verification failed")
        if archive.namelist() != sorted(members):
            raise RuntimeError("Archive members are missing, duplicated or not sorted")
        for info in archive.infolist():
            if info.date_time != FIXED_TIMESTAMP:
                raise RuntimeError("Archive member timestamp is not deterministic")
        stored = {name: archive.read(name) for name in archive.namelist()}
    manifest = stored.pop("SHA256SUMS.txt").decode("utf-8")
    parsed = {}
    for line in manifest.splitlines():
        digest, name = line.split("  ", 1)
        if name in parsed:
            raise RuntimeError("Duplicate archive checksum entry")
        parsed[name] = digest
    if set(parsed) != set(stored):
        raise RuntimeError("Archive manifest coverage differs from its contents")
    for name, content in stored.items():
        if content != members[name] or sha256(content) != parsed[name]:
            raise RuntimeError(f"Archive byte/hash round-trip failed: {name}")


def main() -> int:
    report = json.loads(read_required(REPORT).decode("utf-8"))
    lock = json.loads(read_required(OVERLAY / "baseline-lock.json").decode("utf-8"))
    sources = verify_build_inputs(report, lock)
    members = collect_members(report, sources)
    data = archive_bytes(members)
    if data != archive_bytes(members):
        raise RuntimeError("Repeated archive serialization is not byte-identical")
    verify_archive(data, members)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(data)
    # Verify bytes from disk as well as the in-memory serialization.
    verify_archive(OUTPUT.read_bytes(), members)
    digest = sha256(data)
    sidecar = OUTPUT.with_suffix(OUTPUT.suffix + ".sha256")
    sidecar.write_text(f"{digest}  {OUTPUT.name}\n", encoding="ascii")
    print(json.dumps({
        "archive": str(OUTPUT), "archive_sha256": digest,
        "member_count": len(members), "size_bytes": len(data),
        "baseline_dll_sha256": report["builds"]["baseline"]["dll_sha256"],
        "ps2_enabled_dll_sha256": report["builds"]["ps2-enabled"]["dll_sha256"],
        "fixed_timestamp": list(FIXED_TIMESTAMP),
        "repeat_serialization": "PASS", "testzip": "PASS",
        "manifest_round_trip": "PASS", "automatic_deployment": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print(f"REFLECTION HANDOFF ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
