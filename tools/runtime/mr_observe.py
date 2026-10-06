"""Convenient retail Observatory frontend; original Dump, passive read, offline diff.

No gameplay automation or persistence commands. Low-level parsing and memory
capture are imported from broker_observatory; verified window commands are
imported from dev_command_trigger.
"""
import sys

if sys.version_info < (3, 11):
    sys.stderr.write("Master Rallye Observatory requires Python 3.11 or newer.\n")
    raise SystemExit(2)

import argparse
import json
import os
import re
import subprocess
import time
import uuid
import traceback
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Sequence

import broker_observatory as core
import dev_command_trigger as commands
from observatory_version import VERSION, TOOL_NAME
from observatory_build_profiles import PROFILES, RETAIL_PRISTINE, match_profile

SCRIPT_DIR = Path(__file__).resolve().parent
PORTABLE = not (SCRIPT_DIR.name == "runtime" and SCRIPT_DIR.parent.name == "tools")
REPO = SCRIPT_DIR if PORTABLE else SCRIPT_DIR.parents[1]
if not PORTABLE:
    from observatory_profile_resolver import resolve_executable_profile
DATA_ROOT = REPO / "observatory-data" if PORTABLE else REPO / "research-output/general-re"
DEFAULT_CAPTURE_ROOT = DATA_ROOT / "captures" if PORTABLE else DATA_ROOT / "broker-observatory/captures"
DEFAULT_CONFIG = DATA_ROOT / "config.json" if PORTABLE else DATA_ROOT / "runtime-config.json"
VERBOSE = False
DEBUG = False


def data_boundary() -> Path:
    return (REPO / ("observatory-data" if PORTABLE else "research-output")).resolve()


class UserError(core.ObservatoryError):
    def __init__(self, message: str, detail: str = ""):
        super().__init__(message)
        self.detail = detail


def short_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO.resolve()))
    except ValueError:
        return str(path)


def report_error(exc: Exception) -> None:
    message = str(exc)
    lowered = message.casefold()
    if not isinstance(exc, UserError):
        if isinstance(exc, PermissionError):
            message = "Access denied. Use a writable Observatory folder and run the game/tool at the same privilege level."
        elif "logger sink" in lowered or ("debug" in lowered and ("sink" in lowered or "window" in lowered)):
            message = "Debug buffer unavailable. Enable Menues/Enabled=True in DataGame/dev.xml and restart the game."
        elif "timed out" in lowered and "dump" in lowered:
            message = "A fresh complete Dump did not appear in time. Let the game finish, then try recover; no second Dump was sent. " + str(exc)
        elif "snapshot" in lowered or "sidecar" in lowered or "capture pair" in lowered:
            message = "Capture pair is missing or corrupt. Select another pair or capture again; do not modify its JSON/raw files."
        elif "no complete" in lowered:
            message = "No complete Dump is available. Use Capture Snapshot and wait for completion."
        elif isinstance(exc, OSError):
            message = "File/process access failed. Check that the game is running and the Observatory data folder is writable."
        elif isinstance(exc, (KeyError, TypeError)):
            message = "Unexpected capture/status data. Select another capture or check Status; use --debug for details."
    print(message, file=sys.stderr)
    if VERBOSE and isinstance(exc, UserError) and exc.detail:
        print(exc.detail, file=sys.stderr)
    elif VERBOSE and message != str(exc):
        print(str(exc), file=sys.stderr)
    if DEBUG:
        traceback.print_exception(type(exc), exc, exc.__traceback__)

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
    resolved_profile: Any | None = None

    @property
    def profile(self):
        if self.resolved_profile is not None:
            if self.resolved_profile.sha256 != self.sha256:
                raise core.ObservatoryError("Resolved process profile no longer matches its image SHA256")
            return self.resolved_profile
        for profile in PROFILES:
            if profile.sha256 == self.sha256:
                return profile
        raise core.ObservatoryError("Unknown process build profile")


def verify_executable(path: Path):
    if path.name.casefold() != "mrallye.exe" or not path.is_file():
        raise UserError("MRallye.exe was not found. Select the installed retail MRallye.exe.", str(path))
    try:
        if PORTABLE:
            return match_profile(core.sha256_file(path), path.stat().st_size)
        cache_root = REPO / ".research-output/general-re/observatory/build-profiles"
        return resolve_executable_profile(path, cache_root=cache_root)
    except ValueError as exc:
        raise UserError("Unsupported Master Rallye executable. arbitrary patched EXEs are rejected unless an exact profile or safe Broker read core is proven.",
                        f"Known exact profiles: {', '.join(p.id + ': ' + p.sha256 for p in PROFILES)}\nSelected: {path}\n{exc}") from exc


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
                    profile = verify_executable(path)
                    candidates.append(ProcessCandidate(pid, path, profile.sha256, profile))
                except (OSError, core.ObservatoryError) as exc:
                    detail = f"\n{exc.detail}" if isinstance(exc, UserError) and exc.detail else ""
                    rejected.append(f"PID {pid}: {exc}{detail}")
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
        raise core.ObservatoryError("Multiple Master Rallye processes found. Close extra instances, use --pid, or select one in the interactive menu.")
    for i, process in enumerate(candidates, 1):
        print(f"[{i}] {process.profile.id} [{process.profile.profile_origin}; {process.profile.compatibility_family or 'exact profile'}] — PID {process.pid}: {process.image_path}")
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
    if not root.is_relative_to(data_boundary()):
        raise core.ObservatoryError("Choose a capture folder inside the Observatory data directory.")
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
            snapshot = checked_snapshot(path)
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
    capability = {"broker-editor": "open_broker_editor", "flow-builder": "flow_builder"}.get(tool)
    if capability is None:
        raise core.ObservatoryError("Tool is not verified for the selected build profile.")
    may_open = process.profile.supports(capability)
    may_use_existing = (tool == "broker-editor" and process.profile.supports("native_dump"))
    if not may_open and not may_use_existing:
        raise core.ObservatoryError("Tool is not verified for the selected build profile.")
    existing = commands.find_tool_windows(process.pid, tool, process.profile)
    if len(existing) == 1:
        return existing[0]
    if existing:
        raise core.ObservatoryError(f"Ambiguous {tool} windows; no command sent.")
    if not may_open:
        raise core.ObservatoryError("Broker Editor opener is disabled for this build; an already-open audited window may be used.")
    mains = [w for w in commands.find_retail_main_windows({process.pid: process.profile}) if w.pid == process.pid]
    if len(mains) != 1:
        raise core.ObservatoryError("Broker Editor cannot be opened. Enable Menues/Enabled=True in DataGame/dev.xml, restart the game, and close extra game windows.")
    print("Opening " + ("Broker Editor" if tool == "broker-editor" else "Flow Builder") + "...")
    commands.send_tool_command(mains[0], tool)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        existing = commands.find_tool_windows(process.pid, tool, process.profile)
        if len(existing) == 1:
            return existing[0]
        if len(existing) > 1:
            raise core.ObservatoryError(f"Ambiguous {tool} windows after open.")
        time.sleep(0.1)
    raise UserError(f"{tool} did not appear. Check the developer window setting, let the game respond, then check Status. No repeated open command was sent.")


def capture_fresh(process: ProcessCandidate, *, manual: bool = False,
                  input_fn: Callable[[str], str] = input, timeout: float = FRESH_DUMP_WAIT_SECONDS,
                  read_fn: Callable | None = None,
                  ensure_fn: Callable | None = None,
                  dump_fn: Callable | None = None) -> tuple[bytes, dict[str, Any]]:
    if not process.profile.supports("native_dump"):
        raise core.ObservatoryError("Native Dump request is disabled for this build. Use passive recover for an already-present complete Dump.")
    read_fn = read_fn or (lambda pid: core.capture_debug_buffer(pid, process.profile))
    ensure_fn = ensure_fn or ensure_tool
    dump_fn = dump_fn or commands.send_broker_dump
    broker = ensure_fn(process, "broker-editor")
    baseline, _ = read_fn(process.pid)
    dispatch = None
    if manual:
        input_fn("Press Broker Editor -> Debug -> Dump, then press Enter here: ")
    else:
        print("Requesting Broker Dump...")
        dispatch = dump_fn(broker)
        if dispatch == commands.DumpDispatchOutcome.TIMEOUT_COMPLETION_UNCERTAIN:
            print("Broker Dump is still processing...\nWaiting for a fresh complete dump.")
            if VERBOSE:
                print("Dispatch: ERROR_TIMEOUT 1460; completion uncertain. No retry will be sent.")
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
            print("Fresh Broker Dump captured.")
            return raw, source
        except core.ObservatoryError as exc:
            problem = str(exc)
        time.sleep(0.1)
    error = commands.ERROR_TIMEOUT if dispatch == commands.DumpDispatchOutcome.TIMEOUT_COMPLETION_UNCERTAIN else 0
    raise core.ObservatoryError(f"Fresh Dump capture timed out: {problem}; dispatch={dispatch}, Win32 error={error}; no automatic retry command was sent.")


def capture_recovery(process: ProcessCandidate, *,
                     read_fn: Callable | None = None) -> tuple[bytes, dict[str, Any]]:
    """Read only: latest complete block plus full buffer; no opener or Dump."""
    if not process.profile.supports("broker_read"):
        raise core.ObservatoryError("Passive Broker read is not verified for this build.")
    read_fn = read_fn or (lambda pid: core.capture_debug_buffer(pid, process.profile))
    raw, source = read_fn(process.pid)
    core.parse_dump_bytes(raw, source)  # Reject buffers without a complete Dump.
    source.update({"dump_request": "none-passive-recovery", "dump_dispatch": "not_sent",
                   "freshness": "not_command_proven"})
    return raw, source


def checked_snapshot(path: Path) -> dict:
    snapshot = core.load_snapshot(path)
    raw = path.with_suffix(".dump.bin")
    source = snapshot["source"]
    if (source.get("raw_sidecar") != raw.name or not raw.is_file()
            or raw.stat().st_size != source["raw_byte_length"]
            or core.sha256_file(raw) != source["raw_sha256"]):
        raise UserError("Capture pair is missing or corrupt. Select another pair or capture again.", str(path))
    payload = raw.read_bytes()
    offset, length = source["selected_block_offset"], source["selected_block_length"]
    if (type(offset) is not int or type(length) is not int or offset < 0 or length <= 0
            or offset + length > len(payload)
            or core.sha256_bytes(payload[offset:offset + length]) != source["selected_block_sha256"]):
        raise UserError("Capture pair is missing or corrupt. Select another pair or capture again.", str(path))
    return snapshot


def resolve_capture(value: str | Path, root: Path) -> Path:
    """Resolve only explicit JSON files or unique entries in validated history."""
    text = str(value).strip().strip('"')
    path = Path(text)
    if text and path.exists():
        if not path.is_file() or path.suffix.lower() != ".json":
            raise UserError("Select a capture JSON file, not a raw file or directory.")
        checked_snapshot(path)
        return path
    matches = []
    for candidate in capture_history(root):
        snapshot = checked_snapshot(candidate)
        label = snapshot["source"].get("label")
        if text and text in (candidate.name, candidate.stem, label,
                             label + ".json" if isinstance(label, str) else None):
            matches.append(candidate)
    if not matches:
        raise UserError("Capture not found. Use a capture filename, stem, label, or full JSON path.")
    if len(matches) != 1:
        candidates = "\n".join(f"  {p.relative_to(root)}" for p in matches[:10])
        extra = f"\n  ... {len(matches) - 10} more" if len(matches) > 10 else ""
        raise UserError("Capture name is ambiguous. Use a specific filename or full JSON path.\n" + candidates + extra)
    checked_snapshot(matches[0])
    return matches[0]


def show_capture(path: Path) -> None:
    snapshot = checked_snapshot(path)
    print(f"Snapshot: {snapshot['source'].get('label', 'snapshot')} ({snapshot['created_at_utc']})")
    print("Entries:")
    counts = snapshot["dump"]["reported_scope_counts"]
    for scope in ("GLOBAL", "SCENE", "USER", "TOTAL"):
        count = counts[scope]
        print(f"    {scope.upper():<7} {count}")
    if snapshot["source"].get("freshness") == "not_command_proven":
        print("Passive recovery: freshness is NOT command-proven; this Dump may be older.")
    if VERBOSE:
        print(f"Raw: {snapshot['source']['raw_byte_length'] / 1048576:.2f} MiB")
        print(f"Dispatch: {snapshot['source'].get('dump_dispatch', 'not recorded')}")
        print(f"Win32 error: {snapshot['source'].get('dump_dispatch_win32_error', 'not recorded')}")
    print(f"Saved:\n    {short_path(path)}\n    {short_path(path.with_suffix('.dump.bin'))}")


def print_diff(result: dict, before: dict, after: dict) -> None:
    for name, snapshot in (("A", before), ("B", after)):
        print(f"Snapshot {name}: {snapshot['source'].get('label', 'snapshot')} ({snapshot['created_at_utc']})")
    counts = Counter()
    for event in result["events"]:
        kind = event["kind"]
        if kind in {"ADDED", "REMOVED"}:
            counts[kind] += 1
        elif kind == "CHANGED":
            changes = set(event["changes"])
            counts["VALUE_CHANGED"] += bool(changes & {"VALUE_CHANGED", "TYPE_CHANGED"})
            counts["REVISION_ONLY"] += changes == {"REVISION_CHANGED"}
            counts["METADATA_CHANGED"] += bool(changes - {"VALUE_CHANGED", "TYPE_CHANGED", "REVISION_CHANGED"})
    for key, title in (("ADDED", "Added"), ("REMOVED", "Removed"), ("VALUE_CHANGED", "Value changed"),
                       ("METADATA_CHANGED", "Metadata changed"), ("REVISION_ONLY", "Revision-only")):
        print(f"{title}: {counts[key]}")
    if result["filters"].get("ignore_revision_only"):
        print("Revision-only changes hidden.")
    if VERBOSE:
        core._print_diff_text(result)
    else:
        for event in result["events"][:30]:
            print(f"  {event['kind']}: {event['path']}")
        if len(result["events"]) > 30:
            print("More changes available with --verbose or diff --json.")


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


def status(root: Path, process: ProcessCandidate | None, rejected: Sequence[str] = (), *, detailed: bool = False) -> None:
    print(TOOL_NAME + "\n")
    for reason in rejected:
        print("Unsupported or inaccessible game process. No safe Broker read profile was proven; check --verbose for details.")
        if detailed or VERBOSE:
            print(reason)
    if process is None:
        print("Game: not running. Launch a supported retail-family build or select its installation with [C].")
    else:
        profile = process.profile
        print(f"Game: PID {process.pid}\nBuild: {profile.id}")
        print(f"Profile origin: {profile.profile_origin}")
        print(f"Broker family: {profile.compatibility_family or 'exact-profile-only'}")
        if profile.profile_origin == "committed_exact":
            print("Retail verified (committed exact profile)")
        else:
            print("Broker read core verified; optional capabilities remain separately gated")
        print(f"Vehicle registry: {profile.vehicle_registry_profile}")
        print("Capabilities:")
        for label, capability in (
            ("Broker read", "broker_read"),
            ("Native Dump", "native_dump"),
            ("Results Dump safe", "post_results_native_dump_safe"),
            ("Broker Editor", "open_broker_editor"),
            ("Flow Builder", "flow_builder"),
        ):
            value = profile.capabilities.get(capability)
            rendered = "UNKNOWN" if value is None else "YES" if value else "NO"
            print(f"    {label:<20} {rendered}")
        attract = profile.capabilities.get("legacy_loading_attract_present")
        print("    Legacy Attract      " + ("UNKNOWN" if attract is None else "PRESENT" if attract else "NEUTRALIZED"))
        if detailed or VERBOSE:
            print(f"EXE: {process.image_path}\nSHA256: {process.sha256}")
            if profile.audit_version:
                print(f"Audit: {profile.audit_version}; fingerprint: {profile.audit_fingerprint}")
            if profile.local_profile_cache:
                print(f"Local cache: {profile.local_profile_cache}; reused: {profile.cache_reused}")
        for tool, capability in (("broker-editor", "open_broker_editor"), ("flow-builder", "flow_builder")):
            if not profile.supports(capability) and not (tool == "broker-editor" and profile.supports("native_dump")):
                continue
            try:
                windows = commands.find_tool_windows(process.pid, tool, profile)
                name = "Broker Editor" if tool == "broker-editor" else "Flow Builder"
                state = 'open' if len(windows) == 1 else 'closed' if not windows else 'multiple windows; close extras'
                if tool == "broker-editor" and not profile.supports("open_broker_editor") and not windows:
                    state = "opener disabled; open Broker Editor manually"
                print(f"{name}: {state}")
            except (OSError, RuntimeError) as exc:
                report_error(exc)
        if profile.supports("broker_read"):
            try:
                _raw, source = core.capture_debug_buffer(process.pid, profile)
                print(f"Debug buffer: {source['debug_buffer_used_bytes']/1048576:.2f} / {source['debug_buffer_capacity_bytes']/1048576:.2f} MiB")
            except (OSError, core.ObservatoryError) as exc:
                report_error(exc)
    history = capture_history(root)
    print(f"Captures: {len(history)}")
    print(f"Capture folder: {root if detailed or VERBOSE else short_path(root)}")


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
    if not output.resolve().is_relative_to(data_boundary()):
        raise core.ObservatoryError("Generate the launcher inside the Observatory data directory, then copy it if needed.")
    script, python = _cmd_literal(str(Path(__file__).resolve())), _cmd_literal(sys.executable)
    extra = (' --exe "' + _cmd_literal(str(exe.resolve())) + '"') if exe else ''
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="") as stream:
        stream.write(f'@echo off\r\nsetlocal\r\nchcp 65001 >nul\r\n"{python}" "{script}"{extra} %*\r\n'
                     'set "observe_exit=%ERRORLEVEL%"\r\nif not "%observe_exit%"=="0" pause\r\nexit /b %observe_exit%\r\n')
    print(f"Created user-local launcher: {output}. You may copy this file next to the game.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=f"{TOOL_NAME} {VERSION}")
    parser.add_argument("--verbose", action="store_true", help="show paths, hashes and dispatch details")
    parser.add_argument("--debug", action="store_true", help="include diagnostic details and exception tracebacks")
    parser.add_argument("--pid", type=int)
    parser.add_argument("--exe", type=Path)
    parser.add_argument("--install-root", type=Path)
    parser.add_argument("--capture-root", type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("status")
    config = sub.add_parser("config", help="show/change/clear/reset local installation settings")
    config.add_argument("action", choices=("show", "set", "clear", "reset"), nargs="?", default="show")
    config.add_argument("exe", type=Path, nargs="?")
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
    setup.add_argument("--output", type=Path, default=DATA_ROOT / "MRallye-Observatory.cmd")
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
            core.print_persistence_report(core.persistence_report(checked_snapshot(path), save_file=args.save_file,
                                                                  save_mode=args.save_mode, scope=args.scope))
        return 0
    if command == "diff":
        if args.last:
            if args.before or args.after:
                raise core.ObservatoryError("Choose --last or explicit paths, not both.")
            before, after = last_two(root)
        elif args.before is not None and args.after is not None:
            before, after = resolve_capture(args.before, root), resolve_capture(args.after, root)
        else:
            raise core.ObservatoryError("Use diff --last or diff BEFORE AFTER.")
        left, right = checked_snapshot(before), checked_snapshot(after)
        result = filtered_diff(left, right, preset=args.preset,
                               ignore_revision_only=args.ignore_revision_only, prefixes=args.prefix)
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            print_diff(result, left, right)
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
    requested_profile = verify_executable(args.exe) if getattr(args, "exe", None) is not None else None
    candidates, rejected = discover_processes()
    if requested_profile is not None:
        requested_path = os.path.normcase(str(args.exe.resolve()))
        candidates = [
            ProcessCandidate(candidate.pid, candidate.image_path, requested_profile.sha256, requested_profile)
            for candidate in candidates
            if (os.path.normcase(str(candidate.image_path.resolve())) == requested_path
                and candidate.sha256 == requested_profile.sha256)
        ]
        if not candidates:
            rejected = [*rejected, f"No running MRallye.exe matches the selected path and resolved profile: {args.exe}"]
    process = select_process(candidates, args.pid, input_fn)
    if command == "status":
        status(root, process, rejected, detailed=not getattr(args, "compact", False))
        return 0
    if process is None:
        raise UserError("Master Rallye was not found. Launch pristine retail, then try again or select an installation with config set.", "\n".join(rejected))
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


def save_config(path: Path, config: dict[str, str]) -> None:
    if not path.resolve().is_relative_to(data_boundary()):
        raise UserError("Configuration must be saved inside the Observatory data directory.")
    core.write_json(path, config)


def configure_install(path: Path, config: dict[str, str], exe: Path) -> None:
    exe = exe.resolve()
    verify_executable(exe)
    updated = {**config, "retail_exe": str(exe), "install_root": str(exe.parent)}
    save_config(path, updated)
    config.clear()
    config.update(updated)
    print("Retail installation configured.")


def config_action(args, config: dict[str, str]) -> int:
    if args.action == "show":
        print("Configured installation: " + config.get("retail_exe", "not selected"))
        print(f"Local configuration: {args.config}")
    elif args.action == "set":
        if args.exe is None:
            raise UserError("Select MRallye.exe: config set PATH_TO_MRallye.exe")
        configure_install(args.config, config, args.exe)
    else:
        updated = {} if args.action == "reset" else {k: v for k, v in config.items() if k not in {"retail_exe", "install_root"}}
        save_config(args.config, updated)
        config.clear()
        config.update(updated)
        print("Configuration reset." if args.action == "reset" else "Configured installation cleared.")
    return 0


def installation_menu(args, config: dict[str, str]) -> None:
    print("Configured installation: " + config.get("retail_exe", "not selected"))
    choice = input("[1] Change installation  [2] Clear installation  [0] Back: ").strip()
    if choice == "1":
        configure_install(args.config, config, Path(input("Select retail MRallye.exe: ").strip().strip('"')))
        args.exe = args.install_root = None
    elif choice == "2":
        request = build_parser().parse_args(["config", "clear"])
        request.config = args.config
        config_action(request, config)
        args.exe = args.install_root = None


def first_run(args, config: dict[str, str]) -> bool:
    if args.exe is not None:
        verify_executable(args.exe)
        return True
    while not config.get("retail_exe"):
        candidates, rejected = discover_processes()
        if candidates:
            return True
        print(TOOL_NAME + "\n\nMaster Rallye was not found.\n1. Select Master Rallye installation\n2. Wait for manually launched game\n0. Exit")
        if rejected:
            print("Unsupported or inaccessible MRallye process detected; pristine retail is required.")
            if VERBOSE:
                print("\n".join(rejected))
        choice = input("Action: ").strip()
        if choice == "0":
            return False
        if choice == "1":
            try:
                configure_install(args.config, config, Path(input("Select retail MRallye.exe: ").strip().strip('"')))
            except Exception as exc:
                report_error(exc)
        elif choice == "2":
            input("Launch the game manually, then press Enter to check again: ")
    return True


def interactive(args, root: Path, config: dict[str, str]) -> int:
    if not first_run(args, config):
        return 0
    try:
        request = build_parser().parse_args(["status"])
        request.compact = True
        request.pid = args.pid
        request.exe = args.exe
        execute(request, root, config, input)
    except Exception as exc:
        report_error(exc)
    while True:
        print("\n[1] Broker Editor  [2] Capture Snapshot  [3] Capture with label\n"
              "[4] Latest  [5] Diff Last Two  [6] Diff Files\n[7] Capture Folder  [8] Flow Builder\n"
              "[9] Status  [L] Launch Game  [W] Recheck  [C] Installation  [0] Exit")
        choice = input("Action: ").strip().casefold()
        if choice == "0":
            return 0
        try:
            if choice == "c":
                installation_menu(args, config)
                continue
            if choice == "7":
                root.mkdir(parents=True, exist_ok=True)
                print(f"Capture folder: {root}")
                os.startfile(root)
                continue
            action = {"1": "broker-editor", "2": "capture", "3": "capture", "4": "show", "5": "diff",
                      "6": "diff", "8": "flow-builder", "9": "status", "w": "status", "l": "launch"}.get(choice)
            if action is None:
                continue
            tokens = [action]
            if action == "capture":
                tokens += [input("Label [snapshot]: ").strip() or "snapshot"]
            if action == "diff":
                if choice == "6":
                    recent = capture_history(root)[-3:]
                    if recent:
                        print("Recent captures:")
                        for path in recent:
                            print(f"  {path.name}  [{checked_snapshot(path)['source'].get('label', 'snapshot')}]")
                tokens += ["--last"] if choice == "5" else [input("Before JSON: ").strip().strip('"'), input("After JSON: ").strip().strip('"')]
                if input("Hide revision-only changes? [y/N]: ").strip().casefold() == "y":
                    tokens += ["--ignore-revision-only"]
            request = build_parser().parse_args(tokens)
            for key in ("pid", "exe", "install_root", "config", "capture_root"):
                setattr(request, key, getattr(args, key))
            execute(request, root, config, input)
        except Exception as exc:
            report_error(exc)


def main(argv: Sequence[str] | None = None) -> int:
    global VERBOSE, DEBUG
    args = build_parser().parse_args(argv)
    DEBUG = args.debug
    VERBOSE = args.verbose or DEBUG
    try:
        if args.command == "config" and args.action == "reset":
            return config_action(args, {})
        try:
            config = load_config(args.config)
        except core.ObservatoryError as exc:
            if args.command is not None:
                raise UserError("Local configuration is corrupt. Run config reset, then config set to select retail again.", str(exc)) from exc
            print("Local configuration is corrupt. Reset and select an installation again.")
            if input("[R] Reset configuration  [0] Exit: ").strip().casefold() != "r":
                return 2
            save_config(args.config, {})
            config = {}
        if args.command == "config":
            return config_action(args, config)
        root = capture_root_for(args, config)
        if args.command is None:
            return interactive(args, root, config)
        return execute(args, root, config, input if sys.stdin.isatty() else None)
    except (KeyboardInterrupt, EOFError):
        print("\nObservatory closed.")
        return 130
    except Exception as exc:
        report_error(exc)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
