"""Bounded read-only PC collision snapshots and optional x32dbg logpoint recipe.

No engine calls, process writes, injected DLL, resource registration or spawn.
Snapshots cannot prove the physics thread, a contact impulse or destruction.
The separate debugger recipe instruments live instructions with INT3; it does
not edit the original executable. It is generated only for the exact retail PE.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import time

EXE_SHA = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"
IMAGE_BASE = 0x400000
HOLDER_VA = 0x6F957C
BACKEND_VTABLE = 0x692318
PROP_BODY_VTABLE = 0x691A04
MAX_READ_BYTES = 65536
MAX_VECTOR_COUNT = 8192
PROCESS_ACCESS = 0x1000 | 0x0010  # QUERY_LIMITED_INFORMATION | VM_READ only

# Entries/RET instructions independently grounded in native-pc-lifecycle JSON.
LOGPOINTS = (
    (0x57CE60, "convex_reader_enter"), (0x57CEB5, "convex_reader_return"),
    (0x56EEF0, "collision_attach_enter"), (0x56F234, "collision_attach_return"),
    (0x621220, "instance_clone_enter"), (0x62129E, "instance_clone_return_a"),
    (0x6212B0, "instance_clone_return_b"), (0x621310, "body_bind_enter"),
    (0x43E2A0, "body_register_enter"), (0x43E4B7, "body_register_return"),
    (0x43F2C0, "physics_update_enter"), (0x56FCE0, "instance_cache_clear_enter"),
    (0x4F5840, "egg_retire_enter"), (0x4F5780, "egg_destroy_enter"),
)


class ProbeError(RuntimeError):
    pass


def pointer(value):
    if value < 0x10000 or value > 0x7FFFFFFC or value % 4:
        raise ProbeError("Invalid bounded 32-bit application pointer")
    return value


def u32(memory, address):
    return struct.unpack("<I", memory.read(address, 4))[0]


def vector_count(begin, end, capacity):
    if begin == end == capacity == 0:
        return 0
    pointer(begin)
    if not begin <= end <= capacity or (end - begin) % 4 or (capacity - begin) % 4:
        raise ProbeError("Invalid native vector bounds")
    count = (end - begin) // 4
    if (capacity - begin) // 4 > MAX_VECTOR_COUNT:
        raise ProbeError("Native vector exceeds diagnostic limit")
    return count


def sample_backend(memory, max_instances=8):
    """Only known installed-backend fields; fail closed on changed owner/header.

    Reads are NOT an atomic native snapshot. Rechecking headers and each
    instance detects some concurrent mutations, not pointer reuse/ABA.
    """
    if not 1 <= max_instances <= 16:
        raise ProbeError("max_instances must be 1..16")
    holder = u32(memory, HOLDER_VA)
    if not holder:
        return {"status": "NOT_INITIALIZED", "instances": []}
    backend = u32(memory, pointer(holder) + 8)
    if not backend:
        return {"status": "NO_INSTALLED_BACKEND", "instances": []}
    pointer(backend)
    if u32(memory, backend) != BACKEND_VTABLE:
        raise ProbeError("Unsupported installed collision backend vtable")
    if u32(memory, BACKEND_VTABLE + 0x30) != 0x56FCE0:
        raise ProbeError("Loaded backend cache-clear vtable slot differs")
    header = memory.read(backend + 0x14, 12)
    begin, end, capacity = struct.unpack("<III", header)
    count = vector_count(begin, end, capacity)
    selected = min(count, max_instances)
    addresses = memory.read(begin, 4 * selected) if selected else b""
    records = []
    for (address,) in struct.iter_unpack("<I", addresses):
        row = {"instance": address}
        try:
            raw = memory.read(pointer(address), 0x1C)
            rep_00, rep_04, base, body, category, name_id, egg_cache = struct.unpack("<7I", raw)
            row.update(representation_at_00=rep_00, representation_at_04=rep_04, base=base,
                       body=body, category=category, egg_name_id=name_id,
                       resolved_egg_cache=egg_cache)
            if body:
                vtable = u32(memory, pointer(body))
                row["body_vtable"] = vtable
                if vtable == PROP_BODY_VTABLE:
                    state_bytes = memory.read(body + 0xA0, 28)
                    state = struct.unpack("<7f", state_bytes)
                    if not all(math.isfinite(x) for x in state):
                        raise ProbeError("Non-finite original prop state")
                    row["native_nonvehicle_position"] = list(state[:3])
                    row["native_nonvehicle_orientation4_raw"] = list(state[3:])
                    row["native_nonvehicle_state_u32"] = list(struct.unpack("<7I", state_bytes))
                    row["body_egg_name_id"] = u32(memory, body + 0x1D0)
                    row["body_resolved_egg_cache"] = u32(memory, body + 0x1D4)
                else:
                    row["body_state"] = "UNDECODED_OTHER_BODY_TYPE"
            # Do not dereference the resolved Egg cache: it is transient, and
            # reading its matrix would not establish private ownership.
            if memory.read(address, 0x1C) != raw:
                raise ProbeError("Instance changed during read")
            row["status"] = "READ_SNAPSHOT_NOT_ATOMIC"
        except (ProbeError, OSError) as exc:
            row["status"] = "UNREADABLE_OR_CHANGED"
            row["reason"] = str(exc)
        records.append(row)
    if (u32(memory, HOLDER_VA) != holder or u32(memory, holder + 8) != backend
            or u32(memory, backend) != BACKEND_VTABLE
            or memory.read(backend + 0x14, 12) != header
            or (selected and memory.read(begin, selected * 4) != addresses)):
        raise ProbeError("Backend ownership/vector changed during read")
    return {"status": "READ_SNAPSHOT_NOT_ATOMIC", "holder": holder,
            "backend": backend, "backend_vtable": BACKEND_VTABLE,
            "native_instance_vector_count": count, "selected_count": selected,
            "selection_truncated": selected < count, "instances": records,
            "course_identity": "UNKNOWN", "physics_thread": "UNKNOWN",
            "vehicle_contact": "NOT_PROVED"}


def pe32_identity(data):
    if len(data) < 0x100 or data[:2] != b"MZ":
        raise ProbeError("Expected PE32 executable")
    offset = struct.unpack_from("<I", data, 0x3C)[0]
    if offset + 0x78 > len(data) or data[offset:offset + 4] != b"PE\0\0":
        raise ProbeError("Invalid PE header")
    machine = struct.unpack_from("<H", data, offset + 4)[0]
    magic = struct.unpack_from("<H", data, offset + 24)[0]
    base = struct.unpack_from("<I", data, offset + 24 + 28)[0]
    if (machine, magic, base) != (0x14C, 0x10B, IMAGE_BASE):
        raise ProbeError("Only original i386 PE32 image base 00400000 is supported")
    return {"machine": "i386", "format": "PE32", "image_base": base}


def verify_executable(path):
    data = Path(path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXE_SHA:
        raise ProbeError("Unsupported executable SHA256; no probe generated")
    return dict(pe32_identity(data), sha256=digest, bytes=len(data))


def debugger_script(max_hits=16):
    if not 1 <= max_hits <= 64:
        raise ProbeError("max_hits must be 1..64")
    lines = ["// Exact retail MRallye.exe only, image base00400000; manual cold-load control.",
             "// No run/call/injection commands. INT3 instrumentation changes timing.",
             "// Each breakpoint disables itself at its decimal hit limit."]
    for address, name in LOGPOINTS:
        a = f"{address:08X}"
        extra = "eax={p:eax}" if "return" in name else "caller={p:[esp]}"
        if name in ("convex_reader_enter", "instance_clone_enter", "body_bind_enter", "body_register_enter"):
            extra += " arg0={p:[esp+4]}"
        elif name == "collision_attach_enter":
            extra += " egg={p:[esp+4]} body={p:[esp+8]} category={x:[esp+C]}"
        lines += [f'bp {a}, "rigid_probe_{name}"', f"SetBreakpointCondition {a}, 0",
                  f"SetBreakpointFastResume {a}, 0", f"SetBreakpointSilent {a}, 1",
                  f'SetBreakpointLog {a}, "RIGID_PROBE event={name} tid={{x:tid()}} ip={{p:eip}} ecx={{p:ecx}} {extra} hit={{u:$breakpointcounter}}"',
                  f'SetBreakpointLogCondition {a}, "$breakpointcounter <= .{max_hits}"',
                  f'SetBreakpointCommand {a}, "bpd {a}"',
                  f'SetBreakpointCommandCondition {a}, "$breakpointcounter == .{max_hits}"']
    return "\n".join(lines) + "\n"


class WindowsReadOnlyProcess:
    """Explicit PID; read/query rights only. No implicit process discovery."""
    def __init__(self, pid):
        if os.name != "nt":
            raise ProbeError("Windows ReadProcessMemory is required")
        from ctypes import wintypes as w
        self.k = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "OpenProcess": ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            "CloseHandle": ([w.HANDLE], w.BOOL),
            "ReadProcessMemory": ([w.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                                   ctypes.POINTER(ctypes.c_size_t)], w.BOOL),
            "QueryFullProcessImageNameW": ([w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)], w.BOOL),
            "GetProcessTimes": ([w.HANDLE] + [ctypes.POINTER(w.FILETIME)] * 4, w.BOOL),
            "GetExitCodeProcess": ([w.HANDLE, ctypes.POINTER(w.DWORD)], w.BOOL),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.k, name); fn.argtypes = args; fn.restype = result
        self.handle = self.k.OpenProcess(PROCESS_ACCESS, False, pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        self.bytes_read = 0
        try:
            path = ctypes.create_unicode_buffer(32768); size = w.DWORD(len(path))
            if not self.k.QueryFullProcessImageNameW(self.handle, 0, path, ctypes.byref(size)):
                raise ctypes.WinError(ctypes.get_last_error())
            self.identity = verify_executable(path.value)
            # The whole-file hash locks the on-disk target. Check the actual
            # loaded PE header at the original base; reject relocation/build drift.
            loaded = pe32_identity(self.read(IMAGE_BASE, 4096))
            if loaded["image_base"] != self.identity["image_base"]:
                raise ProbeError("Loaded original PE base differs")
            creation, exit_time, kernel, user = (w.FILETIME() for _ in range(4))
            if not self.k.GetProcessTimes(self.handle, ctypes.byref(creation), ctypes.byref(exit_time),
                                          ctypes.byref(kernel), ctypes.byref(user)):
                raise ctypes.WinError(ctypes.get_last_error())
            self.identity["process_creation_filetime"] = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
            self.identity["pid"] = pid
        except BaseException:
            self.close(); raise

    def read(self, address, size):
        if not 0 <= size <= MAX_READ_BYTES or self.bytes_read + size > MAX_READ_BYTES:
            raise ProbeError("Per-sample64KiB read budget exceeded")
        if not size:
            return b""
        pointer(address)
        if address + size > 0x80000000:
            raise ProbeError("Read exceeds supported application address range")
        self.bytes_read += size
        buffer = ctypes.create_string_buffer(size); copied = ctypes.c_size_t()
        if not self.k.ReadProcessMemory(self.handle, address, buffer, size, ctypes.byref(copied)):
            raise ctypes.WinError(ctypes.get_last_error())
        if copied.value != size:
            raise ProbeError("Partial native memory read")
        return buffer.raw

    def alive(self):
        from ctypes import wintypes as w
        code = w.DWORD()
        if not self.k.GetExitCodeProcess(self.handle, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return code.value == 259

    def close(self):
        if self.handle:
            self.k.CloseHandle(self.handle); self.handle = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    verify = sub.add_parser("verify"); verify.add_argument("--exe", type=Path, required=True)
    script = sub.add_parser("script"); script.add_argument("--exe", type=Path, required=True)
    script.add_argument("--output", type=Path, required=True); script.add_argument("--max-hits", type=int, default=16)
    sample = sub.add_parser("sample"); sample.add_argument("--pid", type=int, required=True)
    sample.add_argument("--output", type=Path, required=True)
    sample.add_argument("--seconds", type=float, default=20); sample.add_argument("--interval-ms", type=int, default=100)
    sample.add_argument("--max-instances", type=int, default=8)
    args = parser.parse_args()
    if args.mode in ("verify", "script"):
        identity = verify_executable(args.exe)
        if args.mode == "script":
            with args.output.open("x", encoding="utf-8") as out:
                out.write(debugger_script(args.max_hits))
        print(json.dumps(identity, indent=2)); return
    if (not math.isfinite(args.seconds) or not 1 <= args.seconds <= 60
            or not 50 <= args.interval_ms <= 1000 or not 1 <= args.max_instances <= 16):
        raise ProbeError("Limits: seconds1..60, interval-ms50..1000, max-instances1..16")
    with args.output.open("x", encoding="utf-8") as out:
        process = WindowsReadOnlyProcess(args.pid)
        try:
            out.write(json.dumps({"schema": "mrr-rigid-readonly-v1", "event": "header",
                                  "process": process.identity, "engine_calls": False,
                                  "process_writes": False, "course_identity": "UNKNOWN",
                                  "sample_limit": math.ceil(args.seconds * 1000 / args.interval_ms)}) + "\n")
            start = time.monotonic()
            for sequence in range(math.ceil(args.seconds * 1000 / args.interval_ms)):
                if not process.alive() or time.monotonic() - start >= args.seconds:
                    break
                process.bytes_read = 0
                try:
                    row = sample_backend(process, args.max_instances)
                except (OSError, ProbeError) as exc:
                    row = {"status": "FAILED_CLOSED", "reason": str(exc)}
                row.update(event="snapshot", sequence=sequence, monotonic_seconds=time.monotonic() - start,
                           read_bytes=process.bytes_read)
                out.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n"); out.flush()
                time.sleep(args.interval_ms / 1000)
        finally:
            process.close()


if __name__ == "__main__":
    try:
        main()
    except (OSError, ProbeError) as exc:
        raise SystemExit("READ-ONLY PROBE ERROR: " + str(exc))
