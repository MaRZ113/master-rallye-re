#!/usr/bin/env python3
"""Build baseline and PS2-enabled renderer variants from a locked Git snapshot.

This script stages only modernization/renderer from the exact baseline commit.
The PS2 variant is assembled by applying the reviewed patch files and then
copying the PS2-only implementation/tests into the ignored staging directory.
No source renderer file is edited by this script.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile
import io
import tempfile
from contextlib import contextmanager


ROOT = Path(__file__).resolve().parents[3]
PORT = ROOT / "ps2-research" / "pc-port"
OVERLAY = PORT / "overlay"
LOCK_PATH = OVERLAY / "baseline-lock.json"
PATCH_DIR = OVERLAY / "patches"
BUILD_ROOT = PORT / ".build"
STAGING_ROOT = PORT / ".staging"
DIST_ROOT = PORT / "dist" / "current"
GENERATOR_OUTPUTS = (
    "data/interface-map.json",
    "include/wrappers.hpp",
    "include/method_names.hpp",
    "src/forwarders.cpp",
    "tests/mock_interfaces.hpp",
)
PATCH_PATHS = {
    "0001-renderer-integration.patch": {
        "modernization/renderer/CMakeLists.txt",
        "modernization/renderer/include/ui_margins.hpp",
        "modernization/renderer/include/wrappers.hpp",
        "modernization/renderer/src/buffer_provenance.cpp",
        "modernization/renderer/src/forwarders.cpp",
        "modernization/renderer/src/provenance.cpp",
        "modernization/renderer/src/quality_wrappers.cpp",
        "modernization/renderer/src/race_epoch.cpp",
        "modernization/renderer/src/race_observer.cpp",
        "modernization/renderer/src/visual_wrappers.cpp",
        "modernization/renderer/src/wrappers.cpp",
    },
    "0002-interface-generator.patch": {
        "modernization/renderer/tools/generate_interfaces.py",
    },
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha256(path.read_bytes())


def repo_relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def git_text(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def verify_renderer_identity(root: Path, lock: dict) -> dict[str, str]:
    """Lock the complete renderer Git tree, not unrelated repository history.

    The pinned commit remains the immutable staging source. Both that commit and
    current HEAD must contain exactly the locked renderer tree. Working-tree and
    untracked source edits are rejected; ignored build outputs are not inputs.
    """
    def git(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    branch, head = git("branch", "--show-current"), git("rev-parse", "HEAD")
    if branch != lock["baseline_branch"]:
        raise RuntimeError(f"Expected branch {lock['baseline_branch']!r}, found {branch!r}")
    source_commit = lock["baseline_head"]
    if git("cat-file", "-t", source_commit) != "commit":
        raise RuntimeError("Pinned baseline source is not a Git commit")
    expected_tree = lock.get("renderer_tree")
    if not expected_tree or git("cat-file", "-t", expected_tree) != "tree":
        raise RuntimeError("Missing or invalid frozen renderer tree identity")
    for commit in (source_commit, head):
        actual_tree = git("rev-parse", f"{commit}:modernization/renderer")
        if actual_tree != expected_tree:
            raise RuntimeError(f"Frozen renderer tree mismatch at {commit}: expected {expected_tree}, found {actual_tree}")
    dirty = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "modernization/renderer"], cwd=root)
    if dirty.returncode:
        raise RuntimeError("modernization/renderer has tracked working-tree changes; staging refused")
    untracked = git("ls-files", "--others", "--exclude-standard", "--", "modernization/renderer")
    if untracked:
        raise RuntimeError("modernization/renderer has untracked source files; staging refused")
    return {"current_head": head, "branch": branch, "baseline_head": source_commit,
            "renderer_tree": expected_tree}


def verify_baseline(lock: dict) -> None:
    override=os.environ.get("MRR_PS2PORT_BUILD_ROOT")
    if override and Path(override).resolve()!=BUILD_ROOT.resolve():
        raise RuntimeError("Single-build-root policy: unset MRR_PS2PORT_BUILD_ROOT; only pc-port/.build is allowed")
    for path in (BUILD_ROOT,STAGING_ROOT,DIST_ROOT):
        if path.is_symlink() or path.resolve()!=path.absolute():
            raise RuntimeError(f"Canonical workflow root must not be redirected: {path}")
    git_root = Path(git_text("rev-parse", "--show-toplevel")).resolve()
    if git_root != ROOT.resolve():
        raise RuntimeError(f"Unexpected repository root: {git_root}")
    verify_renderer_identity(ROOT, lock)
    head = lock["baseline_head"]
    for relative, expected in lock["files"].items():
        data = subprocess.check_output(["git", "show", f"{head}:{relative}"], cwd=ROOT)
        actual = sha256(data)
        if actual != expected["sha256"]:
            raise RuntimeError(f"Baseline file hash mismatch for {relative}: {actual}")
    if set(lock.get("patches", {})) != set(PATCH_PATHS):
        raise RuntimeError("Locked patch set differs from the approved integration patch set")
    for name, expected_paths in PATCH_PATHS.items():
        patch_path = PATCH_DIR / name
        if not patch_path.is_file():
            raise RuntimeError(f"Required exact patch is missing: {patch_path}")
        expected_hash = lock.get("patches", {}).get(name, {}).get("sha256")
        actual_hash = file_sha(patch_path)
        if not expected_hash or actual_hash != expected_hash:
            raise RuntimeError(f"Patch hash mismatch for {name}: expected {expected_hash}, found {actual_hash}")
        output = subprocess.check_output(["git", "apply", "--numstat", str(patch_path)], cwd=ROOT, text=True)
        actual_paths = {line.split("\t", 2)[2] for line in output.splitlines() if len(line.split("\t", 2)) == 3}
        if actual_paths != expected_paths:
            raise RuntimeError(f"Unexpected paths in {name}: {sorted(actual_paths ^ expected_paths)}")


def safe_extract_renderer(archive: bytes, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
        for member in bundle.getmembers():
            name = PurePosixPath(member.name)
            if not member.isfile() or name.is_absolute() or ".." in name.parts:
                if member.isdir():
                    continue
                raise RuntimeError(f"Unexpected Git archive member: {member.name}")
            if name.parts[:2] != ("modernization", "renderer"):
                raise RuntimeError(f"Git archive escaped renderer scope: {member.name}")
            target = destination.joinpath(*name.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            stream = bundle.extractfile(member)
            if stream is None:
                raise RuntimeError(f"Could not read archive member: {member.name}")
            target.write_bytes(stream.read())


def apply_patch(stage_root: Path, name: str) -> None:
    patch = PATCH_DIR / name
    relative_stage = stage_root.relative_to(ROOT).as_posix()
    directory = f"--directory={relative_stage}"
    subprocess.run(["git", "apply", "--check", directory, str(patch)], cwd=ROOT, check=True)
    subprocess.run(["git", "apply", directory, str(patch)], cwd=ROOT, check=True)


def copy_ps2_sources(stage_root: Path) -> Path:
    staged_port = stage_root / "ps2-research" / "pc-port"
    staged_port.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(PORT / "renderer", staged_port / "renderer", ignore=ignore)
    shutil.copytree(PORT / "tests", staged_port / "tests", ignore=ignore)
    return staged_port


def generated_hashes(renderer: Path) -> dict[str, str]:
    return {name: file_sha(renderer / name) for name in GENERATOR_OUTPUTS}


def check_generator(renderer: Path, variant: str, report: dict, env: dict) -> None:
    before = generated_hashes(renderer)
    timestamps={name:(renderer/name).stat().st_mtime_ns for name in GENERATOR_OUTPUTS}
    command = [sys.executable, "tools/generate_interfaces.py"]
    run_command(command, renderer, env, BUILD_ROOT / "logs" / f"{variant}-generator-1.log")
    after_first = generated_hashes(renderer)
    run_command(command, renderer, env, BUILD_ROOT / "logs" / f"{variant}-generator-2.log")
    after_second = generated_hashes(renderer)
    if after_first != after_second:
        raise RuntimeError(f"{variant} interface generator is nondeterministic")
    # The original generator rewrites files unconditionally. Preserve source
    # mtimes only when the verified content is identical, avoiding full native
    # recompiles on otherwise unchanged incremental builds.
    for name in GENERATOR_OUTPUTS:
        if before[name]==after_second[name]:
            p=renderer/name;os.utime(p,ns=(p.stat().st_atime_ns,timestamps[name]))
    expected = json.loads(LOCK_PATH.read_text(encoding="utf-8")).get("generated_outputs", {}).get(variant)
    if expected and after_second != expected:
        raise RuntimeError(f"{variant} generated outputs differ from the locked deterministic contract")
    if variant == "baseline" and before != after_first:
        raise RuntimeError("Baseline interface generator changed its checked-in generated outputs")
    if variant == "baseline":
        if "buffer_mirroring_enabled" in (renderer / "include/wrappers.hpp").read_text(encoding="utf-8"):
            raise RuntimeError("Baseline generator unexpectedly emitted a PS2 extension seam")
        if "buffer_mirroring_enabled()" in (renderer / "src/forwarders.cpp").read_text(encoding="utf-8"):
            raise RuntimeError("Baseline generator unexpectedly enabled PS2 buffer mirroring")
    else:
        header = (renderer / "include/wrappers.hpp").read_text(encoding="utf-8")
        forwarders = (renderer / "src/forwarders.cpp").read_text(encoding="utf-8")
        if "PS2PortExtension" not in header or forwarders.count("buffer_mirroring_enabled()") != 4:
            raise RuntimeError("PS2 generator lost the extension seam or buffer-mirroring gates")
    report["generator"][variant] = {
        "deterministic": True,
        "outputs": after_second,
        "initial_files_rewritten": [name for name in before if before[name] != after_first[name]],
    }


def run_command(command: list[str], cwd: Path, env: dict, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    printable = subprocess.list2cmdline(command)
    print(f"\n> {printable}\n  cwd: {cwd}", flush=True)
    with log_path.open("w", encoding="utf-8", newline="\n") as log:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="", flush=True)
            log.write(line)
        code = process.wait()
    if code:
        raise subprocess.CalledProcessError(code, command)


def copy_source_archive(stage_root: Path, head: str) -> None:
    archive = subprocess.check_output(["git", "archive", head, "modernization/renderer"], cwd=ROOT)
    safe_extract_renderer(archive, stage_root)


def sync_verified_stage(desired: Path, destination: Path, previous: dict[str,str]) -> dict[str,str]:
    """Only replace owned verified files; retain mtimes of identical content.

    Reject edits/unknown files in persistent staging instead of discarding
    them. Build directories are never staging inputs and never cleaned.
    """
    current={p.relative_to(destination).as_posix():p for p in destination.rglob('*') if p.is_file()}
    for name,p in current.items():
        if name not in previous or file_sha(p)!=previous[name]:
            raise RuntimeError(f"Unowned or modified staged source, refusing overwrite: {p}")
    wanted={p.relative_to(desired).as_posix():p for p in desired.rglob('*') if p.is_file()}
    for name,p in current.items():
        if name not in wanted:p.unlink() # Verified generated staging file only.
    hashes={}
    for name,p in sorted(wanted.items()):
        data=p.read_bytes();hashes[name]=sha256(data);target=destination/name
        if not target.is_file() or file_sha(target)!=hashes[name]:
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return hashes


def create_stages(lock: dict, report: dict) -> tuple[Path, Path]:
    STAGING_ROOT.mkdir(parents=True,exist_ok=True)
    manifest_path=STAGING_ROOT/'source-manifest.json'
    old=json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
    # Temporary source validation only, no third CMake tree. Patches are checked
    # against fresh immutable Git bytes on EVERY build, then content-synced.
    with tempfile.TemporaryDirectory(prefix='.verify-',dir=STAGING_ROOT) as directory:
        candidate=Path(directory);baseline,ps2=assemble_stages(candidate,lock,report)
        manifests={}
        for variant,source in (('baseline',baseline),('ps2-enabled',ps2)):
            manifests[variant]=sync_verified_stage(source,STAGING_ROOT/variant,old.get(variant,{}))
        manifest_path.write_text(json.dumps(manifests,indent=2)+'\n')
    baseline,ps2=STAGING_ROOT/'baseline',STAGING_ROOT/'ps2-enabled'
    report['staging']['baseline_source']=repo_relative(baseline/'modernization/renderer')
    report['staging']['ps2_source']=repo_relative(ps2/'modernization/renderer')
    report['staging']['ps2_port_root']=repo_relative(ps2/'ps2-research/pc-port')
    return baseline,ps2


def assemble_stages(parent: Path,lock: dict,report: dict) -> tuple[Path,Path]:
    baseline = parent / "baseline"
    ps2 = parent / "ps2-enabled"
    for stage in (baseline, ps2):
        copy_source_archive(stage, lock["baseline_head"])
    apply_patch(ps2, "0001-renderer-integration.patch")
    apply_patch(ps2, "0002-interface-generator.patch")
    staged_port = copy_ps2_sources(ps2)
    staged_renderer = ps2 / "modernization" / "renderer"
    cmake = (staged_renderer / "CMakeLists.txt").read_text(encoding="utf-8")
    wrappers = (staged_renderer / "include" / "wrappers.hpp").read_text(encoding="utf-8")
    draw = (staged_renderer / "src" / "visual_wrappers.cpp").read_text(encoding="utf-8")
    wrappers_source = (staged_renderer / "src" / "wrappers.cpp").read_text(encoding="utf-8")
    extension_header = (staged_port / "renderer" / "ps2_port_extension.hpp").read_text(encoding="utf-8")
    if "option(MRR_ENABLE_PS2_PORT" not in cmake or "MRR_PS2_PORT_ROOT" not in cmake:
        raise RuntimeError("PS2 staging did not receive the CMake integration patch")
    if "PS2PortExtension" not in wrappers or "extension->classify(snapshot)" not in draw:
        raise RuntimeError("PS2 staging did not receive the draw-extension integration")
    if "override_mask" not in extension_header or "apply_state_transaction" not in draw or "restore_state_transaction" not in draw:
        raise RuntimeError("PS2 staging did not receive masked state transaction support")
    if "claim_draw_diagnostic()" not in draw or "requested_mask" not in draw or "applied_mask" not in draw:
        raise RuntimeError("PS2 staging is missing the bounded mode/mask diagnostic")
    if "ps2_port_mode_selected" not in wrappers_source:
        raise RuntimeError("PS2 staging is missing the one-shot selected-mode diagnostic")
    report["staging"] = {
        "baseline_source": repo_relative(baseline / "modernization" / "renderer"),
        "ps2_source": repo_relative(ps2 / "modernization" / "renderer"),
        "ps2_port_root": repo_relative(staged_port),
        "patches_applied_in_order": list(PATCH_PATHS),
    }
    return baseline, ps2


def build_variant(renderer: Path, build: Path, variant: str, port_root: Path | None,
                  env: dict, report: dict) -> Path:
    configure = ["cmake", "-S", str(renderer), "-B", str(build), "-G", "Visual Studio 18 2026", "-A", "Win32", "-DBUILD_TESTING=ON"]
    if port_root is not None:
        configure += ["-DMRR_ENABLE_PS2_PORT=ON", f"-DMRR_PS2_PORT_ROOT={port_root}"]
    run_command(configure, ROOT, env, BUILD_ROOT / "logs" / f"{variant}-configure.log")
    run_command(["cmake", "--build", str(build), "--config", "Release", "--parallel", "1"], ROOT, env,
                BUILD_ROOT / "logs" / f"{variant}-build.log")
    run_command(["ctest", "--test-dir", str(build), "-C", "Release", "--output-on-failure"], ROOT, env,
                BUILD_ROOT / "logs" / f"{variant}-ctest.log")
    dll = build / "Release" / "d3d8.dll"
    if not dll.is_file():
        raise RuntimeError(f"Expected renderer DLL was not produced: {dll}")
    verify = renderer / "tools" / "verify_proxy.py"
    run_command([sys.executable, str(verify), str(dll)], ROOT, env,
                BUILD_ROOT / "logs" / f"{variant}-proxy-verify.log")
    report["builds"][variant] = {"dll": repo_relative(dll), "dll_sha256": file_sha(dll), "ctest": "PASS", "proxy_verification": "PASS"}
    return dll


@contextmanager
def workflow_lock():
    BUILD_ROOT.mkdir(parents=True,exist_ok=True)
    path=BUILD_ROOT/'workflow.lock'
    with path.open('a+b') as handle:
        handle.seek(0);handle.write(b'0');handle.flush();handle.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as exc:raise RuntimeError('PS2 build workflow already in use; no staging/build changes made') from exc
        try:yield
        finally:
            handle.seek(0)
            if os.name=='nt':msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(handle.fileno(),fcntl.LOCK_UN)


def main() -> int:
    # Verify roots before acquiring the lock or touching reusable stages.
    verify_baseline(json.loads(LOCK_PATH.read_text(encoding='utf-8')))
    with workflow_lock():return build_locked()


def build_locked() -> int:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    verify_baseline(lock)
    print(f"Baseline identity verified: {lock['baseline_head']}", flush=True)
    report = {
        "schema_version": 3,
        "baseline_head": lock["baseline_head"],
        "current_head": git_text("rev-parse", "HEAD"),
        "renderer_tree": lock["renderer_tree"],
        "branch": lock["baseline_branch"],
        "patch_sha256": {name: file_sha(PATCH_DIR / name) for name in PATCH_PATHS},
        "ps2_source_sha256": {
            path.relative_to(PORT).as_posix(): file_sha(path)
            for folder in (PORT / "renderer", PORT / "tests")
            for path in sorted(folder.rglob("*"))
            if path.is_file() and path.suffix in {".cpp", ".hpp", ".py"}
        },
        "generator": {},
        "builds": {},
    }
    baseline, ps2 = create_stages(lock, report)
    temp_root = BUILD_ROOT / "tmp"
    temp_root.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({"TEMP": str(temp_root), "TMP": str(temp_root), "TMPDIR": str(temp_root)})
    check_generator(baseline / "modernization" / "renderer", "baseline", report, env)
    check_generator(ps2 / "modernization" / "renderer", "ps2-enabled", report, env)
    baseline_build = BUILD_ROOT / "baseline"
    ps2_build = BUILD_ROOT / "ps2-enabled"
    baseline_dll = build_variant(baseline / "modernization" / "renderer", baseline_build, "baseline", None, env, report)
    ps2_port_root = ps2 / "ps2-research" / "pc-port"
    ps2_dll = build_variant(ps2 / "modernization" / "renderer", ps2_build, "ps2-enabled", ps2_port_root, env, report)
    # The integration tests inspect the generated PS2 staging tree, never the baseline worktree.
    env["MRR_PC_PORT_RENDERER_ROOT"] = str(ps2 / "modernization" / "renderer")
    run_command([sys.executable, "-m", "unittest", "discover", "-s", str(PORT / "tests"), "-v"], ROOT, env,
                BUILD_ROOT / "logs" / "ps2-port-python-tests.log")
    run_command([sys.executable, "-m", "compileall", "-q", str(PORT / "renderer"), str(PORT / "tests")], ROOT, env,
                BUILD_ROOT / "logs" / "ps2-port-compileall.log")
    report["builds"]["baseline"]["build"] = "PASS"
    report["builds"]["ps2-enabled"]["build"] = "PASS"
    report["ps2_port_tests"] = "PASS"
    report["dll_distinct"] = baseline_dll.resolve() != ps2_dll.resolve()
    if not report["dll_distinct"] or file_sha(baseline_dll) == file_sha(ps2_dll):
        raise RuntimeError("The baseline and PS2-enabled DLL outputs are not distinct")
    verify_baseline(lock)
    # Build outputs are intermediate; publish validated DLLs only after all
    # suites, exports and source integrity checks pass. Never deploy to game.
    DIST_ROOT.mkdir(parents=True,exist_ok=True)
    for variant,dll in (('baseline',baseline_dll),('ps2-enabled',ps2_dll)):
        target=DIST_ROOT/variant/'d3d8.dll';target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(dll,target)
        report['builds'][variant]['build_dll']=report['builds'][variant]['dll']
        report['builds'][variant]['dll']=repo_relative(target)
        if file_sha(target)!=report['builds'][variant]['dll_sha256']:raise RuntimeError('Published DLL hash mismatch')
    report_path = DIST_ROOT/'build-report.json'
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (DIST_ROOT/'SHA256SUMS.txt').write_text(''.join(f'{file_sha(p)}  {p.relative_to(DIST_ROOT).as_posix()}\n'
        for p in sorted(DIST_ROOT.rglob('*')) if p.is_file() and p.name!='SHA256SUMS.txt'))
    print(f"\nBuild report: {report_path}", flush=True)
    print(f"Baseline DLL: {baseline_dll}  SHA256 {report['builds']['baseline']['dll_sha256']}", flush=True)
    print(f"PS2-enabled DLL: {ps2_dll}  SHA256 {report['builds']['ps2-enabled']['dll_sha256']}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError, KeyError, ValueError) as exc:
        print(f"BUILD OVERLAY ERROR: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(2)
