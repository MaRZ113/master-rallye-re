"""Convenient retail Observatory frontend; original Dump, passive read, offline diff.

No gameplay automation or persistence commands. Low-level parsing and memory
capture are imported from broker_observatory; verified window commands are
imported from dev_command_trigger.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Sequence

import broker_observatory as core
import dev_command_trigger as commands

REPO = Path(__file__).resolve().parents[2]
DEFAULT_CAPTURE_ROOT = REPO / "research-output/general-re/broker-observatory/captures"
DEFAULT_CONFIG = REPO / "research-output/general-re/runtime-config.json"
FRESH_DUMP_WAIT_SECONDS = 120.0
PRESETS = {
    "race": re.compile(r"^(?:Race/|Car\d+$|Vehicles/Car\d+(?:/|$)|Drivers/|Controller/Car\d+(?:/|$)|Physics/Car\d+(?:/|$))"),
    "frontend": re.compile(r"^(?:Frontend/|UI/)"),
    "vehicle": re.compile(r"^(?:Vehicles/|Race/Car\d+(?:/|$))"),
    "route": re.compile(r"^Race/"),
}


@dataclass(frozen=True)
class ProcessCandidate:
    pid: int
    image_path: Path
    sha256: str


def verify_executable(path: Path) -> None:
    if path.name.casefold() != "mrallye.exe" or not path.is_file():
        raise core.ObservatoryError(f"Expected an existing retail MRallye.exe: {path}")
    if path.stat().st_size != core.RETAIL_SIZE or core.sha256_file(path) != core.RETAIL_SHA256:
        raise core.ObservatoryError(f"Unsupported/patched EXE: {path}; only the pristine retail hash is supported.")


def discover_processes() -> tuple[list[ProcessCandidate], list[str]]:
    if os.name != "nt":
        raise core.ObservatoryError("Live discovery is Windows-only; offline show/diff/report still work.")
    import ctypes
    from ctypes import wintypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    commands._configure_kernel32(kernel32, ctypes)

    class ProcessEntry(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG),
                    ("dwFlags", wintypes.DWORD), ("szExeFile", wintypes.WCHAR * 260)]

    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    for name in ("Process32FirstW", "Process32NextW"):
        function = getattr(kernel32, name)
        function.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
        function.restype = wintypes.BOOL
    handle = kernel32.CreateToolhelp32Snapshot(2, 0)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    candidates, rejected = [], []
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(entry)
        ok = kernel32.Process32FirstW(handle, ctypes.byref(entry))
        while ok:
            if entry.szExeFile.casefold() == "mrallye.exe":
                pid = int(entry.th32ProcessID)
                path = commands._image_for_pid(kernel32, pid)
                try:
                    if path is None:
                        raise core.ObservatoryError("image path unavailable")
                    verify_executable(path)
                    candidates.append(ProcessCandidate(pid, path, core.RETAIL_SHA256))
                except (OSError, core.ObservatoryError) as exc:
                    rejected.append(f"PID {pid}: {exc}")
            ok = kernel32.Process32NextW(handle, ctypes.byref(entry))
    finally:
        kernel32.CloseHandle(handle)
    return sorted(candidates, key=lambda p: p.pid), rejected


def select_process(candidates: Sequence[ProcessCandidate], pid: int | None = None,
                   input_fn: Callable[[str], str] | None = None) -> ProcessCandidate | None:
    if pid is not None:
        matches = [p for p in candidates if p.pid == pid]
        if len(matches) != 1:
            raise core.ObservatoryError(f"PID {pid} is not one verified retail candidate.")
        return matches[0]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    if input_fn is None:
        raise core.ObservatoryError("Multiple supported instances; use --pid or the interactive menu.")
    for i, process in enumerate(candidates, 1):
        print(f"[{i}] PID {process.pid}: {process.image_path}")
    choice = input_fn("Select instance (0 cancels): ").strip()
    if choice == "0":
        return None
    if not choice.isdigit() or not 1 <= int(choice) <= len(candidates):
        raise core.ObservatoryError("Invalid process selection.")
    return candidates[int(choice) - 1]


def load_config(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise core.ObservatoryError(f"Cannot read local config: {exc}") from exc
    if not isinstance(value, dict) or any(k not in {"retail_exe", "install_root", "capture_root"} for k in value):
        raise core.ObservatoryError("Invalid config keys; expected retail_exe/install_root/capture_root.")
    if any(not isinstance(v, str) or not v.strip() for v in value.values()):
        raise core.ObservatoryError("Config paths must be nonempty strings.")
    return value


def capture_root_for(args: argparse.Namespace, config: dict[str, str]) -> Path:
    root = Path(args.capture_root or config.get("capture_root") or DEFAULT_CAPTURE_ROOT).resolve()
    if not root.is_relative_to((REPO / "research-output").resolve()):
        raise core.ObservatoryError("Capture root must stay inside this worktree's ignored research-output.")
    return root


def capture_name(label: str, now: datetime | None = None) -> tuple[str, str]:
    now = now or datetime.now()
    slug = re.sub(r"[^\w.-]+", "-", label.strip(), flags=re.UNICODE).strip(" .-_")[:64] or "snapshot"
    return now.strftime("%Y-%m-%d"), now.strftime("%Y%m%d-%H%M%S") + "_" + slug


def _publish_new(temp: Path, final: Path) -> None:
    # Windows rename is new-file-only; POSIX rename could overwrite, so link.
    if os.name == "nt":
        os.rename(temp, final)
    else:
        os.link(temp, final)
        temp.unlink()


def store_capture(root: Path, raw: bytes, source: dict[str, Any], label: str,
                  now: datetime | None = None) -> Path:
    """Validate first, reserve a pair, publish raw then JSON, clean interrupted output."""
    snapshot = core.parse_dump_bytes(raw, {**source, "label": label})
    date, stem = capture_name(label, now)
    folder = root / date
    folder.mkdir(parents=True, exist_ok=True)
    for suffix in range(10000):
        name = stem + (f"_{suffix:03}" if suffix else "")
        path = folder / (name + ".json")
        raw_path = path.with_suffix(".dump.bin")
        reservation = path.with_suffix(".pending")
        try:
            with reservation.open("xb"):
                pass
        except FileExistsError:
            continue
        if path.exists() or raw_path.exists():
            reservation.unlink()
            continue
        break
    else:
        raise core.ObservatoryError("Capture naming collision limit reached.")
    token = uuid.uuid4().hex
    raw_temp = folder / (name + "." + token + ".raw.tmp")
    json_temp = folder / (name + "." + token + ".json.tmp")
    published: list[Path] = []
    try:
        snapshot["source"]["raw_sidecar"] = raw_path.name
        for temp, payload in ((raw_temp, raw), (json_temp, (json.dumps(snapshot, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode("utf-8"))):
            with temp.open("xb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
        if core.sha256_file(raw_temp) != snapshot["source"]["raw_sha256"]:
            raise core.ObservatoryError("Raw sidecar validation failed.")
        core.load_snapshot(json_temp)
        _publish_new(raw_temp, raw_path)
        published.append(raw_path)
        _publish_new(json_temp, path)
        published.append(path)
    except BaseException:
        for member in published:
            member.unlink(missing_ok=True)
        raise
    finally:
        raw_temp.unlink(missing_ok=True)
        json_temp.unlink(missing_ok=True)
        reservation.unlink(missing_ok=True)
    return path


def capture_history(root: Path) -> list[Path]:
    """Deterministic metadata discovery; incomplete/corrupt pairs are never latest."""
    found = []
    # Include original low-level captures placed directly in the established
    # root as well as new date folders. Never rewrite/import their evidence.
    for path in root.rglob("*.json"):
        if path.with_suffix(".pending").exists():
            continue
        try:
            snapshot = core.load_snapshot(path)
            raw = path.with_suffix(".dump.bin")
            if snapshot["source"].get("raw_sidecar") != raw.name:
                continue
            if raw.stat().st_size != snapshot["source"]["raw_byte_length"]:
                continue
            if core.sha256_file(raw) != snapshot["source"]["raw_sha256"]:
                continue
            found.append((snapshot["created_at_utc"], path.name, path))
        except (OSError, KeyError, TypeError, core.ObservatoryError):
            continue
    return [item[2] for item in sorted(found)]


def last_two(root: Path) -> tuple[Path, Path]:
    history = capture_history(root)
    if len(history) < 2:
        raise core.ObservatoryError("Need two complete capture pairs for diff --last.")
    return history[-2], history[-1]


def fresh_dump_snapshot(baseline: bytes, current: bytes, source: dict[str, Any]) -> dict[str, Any]:
    # Base address can move under realloc. Prefix and complete-block offset prove
    # append provenance even if the new Dump hash equals the old one.
    if not current.startswith(baseline):
        raise core.ObservatoryError("Debug buffer reset/compacted after baseline; fresh Dump provenance cannot be proved.")
    snapshot = core.parse_dump_bytes(current, source)
    if snapshot["source"]["selected_block_offset"] < len(baseline):
        raise core.ObservatoryError("No NEW complete Dump appended after the request.")
    return snapshot


def ensure_tool(process: ProcessCandidate, tool: str, timeout: float = 5.0) -> commands.TargetWindow:
    existing = commands.find_tool_windows(process.pid, tool)
    if len(existing) == 1:
        return existing[0]
    if existing:
        raise core.ObservatoryError(f"Ambiguous {tool} windows; no command sent.")
    mains = [w for w in commands.find_retail_main_windows() if w.pid == process.pid]
    if len(mains) != 1:
        raise core.ObservatoryError("No unique verified Game/Reset/Exit main window. Enable Menues/Enabled in your disposable install.")
    print(f"Opening {tool} (open only; Broker may register two SaveFile metadata names).")
    commands.send_tool_command(mains[0], tool)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        existing = commands.find_tool_windows(process.pid, tool)
        if len(existing) == 1:
            return existing[0]
        if len(existing) > 1:
            raise core.ObservatoryError(f"Ambiguous {tool} windows after open.")
        time.sleep(0.1)
    raise core.ObservatoryError(f"{tool} did not appear. No repeated open command sent.")


def capture_fresh(process: ProcessCandidate, *, manual: bool = False,
                  input_fn: Callable[[str], str] = input, timeout: float = FRESH_DUMP_WAIT_SECONDS,
                  read_fn: Callable = core.capture_debug_buffer,
                  ensure_fn: Callable = ensure_tool,
                  dump_fn: Callable = commands.send_broker_dump) -> tuple[bytes, dict[str, Any]]:
    broker = ensure_fn(process, "broker-editor")
    baseline, _ = read_fn(process.pid)
    dispatch = None
    if manual:
        input_fn("Press Broker Editor -> Debug -> Dump, then press Enter here: ")
    else:
        dispatch = dump_fn(broker)
        if dispatch == commands.DumpDispatchOutcome.TIMEOUT_COMPLETION_UNCERTAIN:
            print("Dump command is still processing; waiting for a fresh complete block. No retry will be sent.")
        elif dispatch != commands.DumpDispatchOutcome.COMPLETED_SYNCHRONOUSLY:
            raise core.ObservatoryError("Unrecognized Dump dispatch outcome; no retry was sent.")
    deadline = time.monotonic() + timeout
    problem = "no new complete block"
    while time.monotonic() < deadline:
        try:
            raw, source = read_fn(process.pid)
            fresh_dump_snapshot(baseline, raw, source)
            source.update({"dump_request": "manual-original-menu" if manual else "broker-window-WM_COMMAND-2",
                           "baseline_byte_length": len(baseline), "baseline_sha256": core.sha256_bytes(baseline),
                           "freshness": "post_baseline_complete_dump_proven",
                           "dump_dispatch": "manual_original_menu" if manual else (
                               "send_timeout_then_fresh_dump_observed"
                               if dispatch == commands.DumpDispatchOutcome.TIMEOUT_COMPLETION_UNCERTAIN
                               else "completed_synchronously"),
                           "dump_dispatch_win32_error": commands.ERROR_TIMEOUT if (
                               dispatch == commands.DumpDispatchOutcome.TIMEOUT_COMPLETION_UNCERTAIN) else None if manual else 0})
            return raw, source
        except core.ObservatoryError as exc:
            problem = str(exc)
        time.sleep(0.1)
    raise core.ObservatoryError(f"Fresh Dump capture timed out: {problem}; no automatic retry command was sent.")


def capture_recovery(process: ProcessCandidate, *,
                     read_fn: Callable = core.capture_debug_buffer) -> tuple[bytes, dict[str, Any]]:
    """Read only: latest complete block plus full buffer; no opener or Dump."""
    raw, source = read_fn(process.pid)
    core.parse_dump_bytes(raw, source)  # Reject buffers without a complete Dump.
    source.update({"dump_request": "none-passive-recovery", "dump_dispatch": "not_sent",
                   "freshness": "not_command_proven"})
    return raw, source


def show_capture(path: Path) -> None:
    snapshot = core.load_snapshot(path)
    print(f"Captured: {snapshot['source'].get('label', 'snapshot')} ({snapshot['created_at_utc']})")
    print(f"Entries: {snapshot['dump']['reported_scope_counts']}")
    print(f"Raw: {snapshot['source']['raw_byte_length'] / 1048576:.2f} MiB")
    if snapshot["source"].get("freshness") == "not_command_proven":
        print("Freshness: NOT command-proven (passive recovery; may be an older Dump).")
    elif "dump_dispatch" in snapshot["source"]:
        print(f"Dump dispatch: {snapshot['source']['dump_dispatch']}")
    print(f"JSON: {path}\nRaw:  {path.with_suffix('.dump.bin')}")


def filtered_diff(before: dict, after: dict, *, preset: str | None = None,
                  ignore_revision_only: bool = False, prefixes: Sequence[str] = ()) -> dict:
    if preset in PRESETS:
        pattern = PRESETS[preset]
        before = {**before, "entries": [e for e in before["entries"] if pattern.search(e["path"])]}
        after = {**after, "entries": [e for e in after["entries"] if pattern.search(e["path"])]}
    result = core.diff_snapshots(before, after, prefixes=prefixes, ignore_revision_only=ignore_revision_only)
    if preset == "persistence":
        names = {"REVISION_CHANGED", "BROKER_ID_CHANGED", "SCOPE_CHANGED", "SAVE_MASK_CHANGED", "SAVE_FILE_CHANGED"}
        events = []
        for event in result["events"]:
            if event["kind"] != "CHANGED":
                events.append(event)
            else:
                changes = {k: v for k, v in event["changes"].items() if k in names}
                if changes:
                    events.append({**event, "changes": changes})
        result["events"] = events
        counts = Counter()
        for event in events:
            counts[event["kind"]] += 1
            if event["kind"] == "CHANGED":
                counts.update(event["changes"].keys())
        result["summary"] = dict(sorted(counts.items()))
    result["filters"]["preset"] = preset
    return result


def status(root: Path, process: ProcessCandidate | None, rejected: Sequence[str] = ()) -> None:
    print("Master Rallye Observatory")
    for reason in rejected:
        print("Rejected: " + reason)
    if process is None:
        print("Game: no supported retail process selected.")
    else:
        print(f"Game: PID {process.pid}; {process.image_path}; SHA256 {process.sha256}")
        for tool in commands.TOOL_COMMANDS:
            try:
                windows = commands.find_tool_windows(process.pid, tool)
                print(f"{tool}: {'open' if len(windows) == 1 else 'closed' if not windows else 'ambiguous'}")
            except (OSError, RuntimeError) as exc:
                print(f"{tool}: unavailable ({exc})")
        try:
            _raw, source = core.capture_debug_buffer(process.pid)
            capacity = source["debug_buffer_capacity_bytes"] / 1048576
            used = source["debug_buffer_used_bytes"] / 1048576
            print(f"Debug sink: active; used={used:.2f} MiB; capacity={capacity:.2f} MiB; HWND={source['debug_window_handle']}")
        except (OSError, core.ObservatoryError) as exc:
            print(f"Debug sink: unavailable ({exc})")
    history = capture_history(root)
    print(f"Captures: {len(history)}; folder: {root}")
    if history:
        show_capture(history[-1])


def launch_game(exe: Path, install_root: Path | None = None) -> None:
    verify_executable(exe)
    root = (install_root or exe.parent).resolve()
    if not root.is_dir():
        raise core.ObservatoryError("Install root is not a directory.")
    # User chooses launch; no flags, assets, configuration or EXE are altered.
    subprocess.Popen([str(exe.resolve())], cwd=root)


def _cmd_literal(text: str) -> str:
    if any(c in text for c in '\r\n"%!'):
        raise core.ObservatoryError("Launcher paths cannot contain quote, percent, exclamation or newline.")
    return text


def setup_launcher(output: Path, exe: Path | None) -> None:
    if not output.resolve().is_relative_to((REPO / "research-output").resolve()):
        raise core.ObservatoryError("Generate launcher inside research-output, then copy it next to the game.")
    script, python = _cmd_literal(str(Path(__file__).resolve())), _cmd_literal(sys.executable)
    extra = (' --exe "' + _cmd_literal(str(exe.resolve())) + '"') if exe else ''
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="") as stream:
        stream.write(f'@echo off\r\nsetlocal\r\nchcp 65001 >nul\r\n"{python}" "{script}"{extra} %*\r\n'
                     'set "observe_exit=%ERRORLEVEL%"\r\nif not "%observe_exit%"=="0" pause\r\nexit /b %observe_exit%\r\n')
    print(f"Created user-local launcher: {output}. You may copy this file next to the game.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int)
    parser.add_argument("--exe", type=Path)
    parser.add_argument("--install-root", type=Path)
    parser.add_argument("--capture-root", type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("status")
    capture = sub.add_parser("capture")
    capture.add_argument("label", nargs="?", default="snapshot")
    capture.add_argument("--manual-dump", action="store_true")
    recovery = sub.add_parser("recover", help="passively salvage the latest complete Dump; sends no game command")
    recovery.add_argument("label", nargs="?", default="recovered")
    show = sub.add_parser("show")
    show.add_argument("snapshot", nargs="?", type=Path)
    selection = show.add_mutually_exclusive_group()
    selection.add_argument("--last", action="store_true")
    selection.add_argument("--previous", action="store_true")
    diff = sub.add_parser("diff")
    diff.add_argument("before", nargs="?", type=Path)
    diff.add_argument("after", nargs="?", type=Path)
    diff.add_argument("--last", action="store_true")
    diff.add_argument("--preset", choices=(*PRESETS, "persistence"))
    diff.add_argument("--prefix", action="append", default=[])
    diff.add_argument("--ignore-revision-only", action="store_true")
    diff.add_argument("--json", action="store_true")
    report = sub.add_parser("persistence-report")
    report.add_argument("snapshot", nargs="?", type=Path)
    report.add_argument("--save-file")
    report.add_argument("--save-mode", choices=tuple(core.SAVE_MODE_FIELDS))
    report.add_argument("--scope", choices=("GLOBAL", "SCENE", "USER"))
    for tool in commands.TOOL_COMMANDS:
        sub.add_parser(tool)
    sub.add_parser("launch")
    setup = sub.add_parser("setup-launcher")
    setup.add_argument("--output", type=Path, default=REPO / "research-output/general-re/MRallye-Observatory.cmd")
    return parser


def execute(args, root: Path, config: dict[str, str], input_fn=None) -> int:
    command = args.command
    if command in {"show", "persistence-report"}:
        if command == "show" and (args.last or args.previous) and args.snapshot:
            raise core.ObservatoryError("Choose latest/previous or an explicit path, not both.")
        path = args.snapshot
        if path is None:
            history = capture_history(root)
            if not history:
                raise core.ObservatoryError("No complete captures found.")
            if command == "show" and args.previous:
                if len(history) < 2:
                    raise core.ObservatoryError("Need two complete capture pairs to show previous.")
                path = history[-2]
            else:
                path = history[-1]
        if command == "show":
            show_capture(path)
        else:
            core.print_persistence_report(core.persistence_report(core.load_snapshot(path), save_file=args.save_file,
                                                                  save_mode=args.save_mode, scope=args.scope))
        return 0
    if command == "diff":
        if args.last:
            if args.before or args.after:
                raise core.ObservatoryError("Choose --last or explicit paths, not both.")
            before, after = last_two(root)
        elif args.before is not None and args.after is not None:
            before, after = args.before, args.after
        else:
            raise core.ObservatoryError("Use diff --last or diff BEFORE AFTER.")
        result = filtered_diff(core.load_snapshot(before), core.load_snapshot(after), preset=args.preset,
                               ignore_revision_only=args.ignore_revision_only, prefixes=args.prefix)
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            core._print_diff_text(result)
        return 0
    exe = args.exe or (Path(config["retail_exe"]) if "retail_exe" in config else None)
    install = args.install_root or (Path(config["install_root"]) if "install_root" in config else None)
    if command == "setup-launcher":
        setup_launcher(args.output, exe)
        return 0
    if command == "launch":
        if exe is None:
            raise core.ObservatoryError("Configure the disposable retail install or supply --exe.")
        launch_game(exe, install)
        return 0
    candidates, rejected = discover_processes()
    process = select_process(candidates, args.pid, input_fn)
    if command == "status":
        status(root, process, rejected)
        return 0
    if process is None:
        raise core.ObservatoryError("Game is not running. Launch verified retail, then retry." + (" Rejected: " + "; ".join(rejected) if rejected else ""))
    if command in commands.TOOL_COMMANDS:
        ensure_tool(process, command)
        return 0
    if command == "recover":
        print("Passive recovery: no game command will be sent; freshness is NOT command-proven.")
        raw, source = capture_recovery(process)
    else:
        raw, source = capture_fresh(process, manual=args.manual_dump, input_fn=input_fn or input)
    path = store_capture(root, raw, source, args.label)
    show_capture(path)
    return 0


def interactive(args, root: Path, config: dict[str, str]) -> int:
    try:
        request = build_parser().parse_args(["status"])
        for key in ("pid", "exe", "install_root", "config", "capture_root"):
            setattr(request, key, getattr(args, key))
        execute(request, root, config, input)
    except (OSError, RuntimeError) as exc:
        print(f"Initial status unavailable: {exc}")
    while True:
        print("\nMaster Rallye Observatory\n[1] Open Broker Editor  [2] Capture snapshot  [3] Capture with label\n"
              "[4] Show latest  [5] Diff last two  [6] Diff two files\n[7] Open capture folder  [8] Open Flow Builder\n"
              "[9] Status  [L] Launch game  [W] Wait/recheck  [C] Configure install  [0] Exit")
        choice = input("Action: ").strip().casefold()
        if choice == "0":
            return 0
        try:
            if choice == "c":
                exe = Path(input("Path to disposable retail MRallye.exe: ").strip().strip('"')).resolve()
                verify_executable(exe)
                config.update({"retail_exe": str(exe), "install_root": str(exe.parent)})
                if not args.config.resolve().is_relative_to((REPO / "research-output").resolve()):
                    raise core.ObservatoryError("Writable local config must be inside ignored research-output.")
                core.write_json(args.config, config)
                continue
            if choice == "7":
                root.mkdir(parents=True, exist_ok=True)
                os.startfile(root)
                continue
            action = {"1": "broker-editor", "2": "capture", "3": "capture", "4": "show", "5": "diff",
                      "6": "diff", "8": "flow-builder", "9": "status", "w": "status", "l": "launch"}.get(choice)
            if action is None:
                continue
            tokens = [action]
            if action == "capture":
                tokens += [(input("Optional label [snapshot]: ").strip() or "snapshot") if choice == "3" else "snapshot"]
            if action == "diff":
                tokens += ["--last"] if choice == "5" else [input("Before JSON: ").strip().strip('"'), input("After JSON: ").strip().strip('"')]
                if input("Hide revision-only changes? [y/N]: ").casefold() == "y":
                    tokens += ["--ignore-revision-only"]
            request = build_parser().parse_args(tokens)
            for key in ("pid", "exe", "install_root", "config", "capture_root"):
                setattr(request, key, getattr(args, key))
            execute(request, root, config, input)
        except (OSError, RuntimeError, ValueError) as exc:
            print(f"Observatory: {exc}", file=sys.stderr)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(args.config)
        root = capture_root_for(args, config)
        if args.command is None:
            return interactive(args, root, config)
        return execute(args, root, config, input if sys.stdin.isatty() else None)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"mr_observe: {exc}", file=sys.stderr)
        return 2
    except (KeyboardInterrupt, EOFError):
        print("\nObservatory closed; no gameplay/persistence command sent.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
