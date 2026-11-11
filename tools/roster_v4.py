"""Derive a Roster V4 runtime bundle from a V-CAP runtime (docs/vehicle-manager/ROSTER_V4_PLAN.md).

The V-CAP builder keeps SDK33 order, never retires a record and never renames a family; the owner's V4 roster needs
all three. This tool applies them as an explicit, verified transform of a finished bundle (the same inputs the
Vehicle Manager compiles into roster.mrvr):

* class order / retirement: the MRVC class maps, counts and reverse tables in the native payload, the native class
  count operation and the selection publisher bound, and the Vehicle Select widget eggs (each car keeps its own
  widget block, frames and unlock bindings; a retired car's widget is removed);
* family renames: the native family string (payload or EXE-cave operation), DataGx/Vehicles/<Family>/ resources and
  the Vehicles/<Family>/ keys of vehicles.xml / Modifications.xml;
* display strings (manufacturer / model / names / drivers) by exact old -> new replacement.

A string that grows is moved into the payload tail and every absolute reference (payload or operation bytes) is
rewritten; a string without exactly the expected references is refused. The output is a new runtime directory;
the source bundle is never modified.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, struct, sys
from pathlib import Path

PAYLOAD_VA = 0x10000000
IMAGE_BASE = 0x00400000
CLASSES = ("T1", "T2", "T3")
# Native class-count owners (V-CAP core): T1/T2 constructor immediates in the EXE cave, T3 frozen immediate.
CLASS_COUNT_OPS = {"T1": (0x68E635, b"\xc7\x46\x20"), "T2": (0x68E63C, b"\xc7\x46\x24"), "T3": (0x480A65, b"")}


class Rvp:
    def __init__(self, raw: bytes):
        if raw[:4] != b"MRVP":
            raise ValueError("RVP1 expected")
        self.header = bytearray(raw[:120])
        count = struct.unpack_from("<I", raw, 20)[0]
        self.ops, at = [], 120
        for _ in range(count):
            fo, rva, ln, fl, pg = struct.unpack_from("<IIHBB", raw, at); at += 12
            before, after = raw[at:at + ln], bytearray(raw[at + ln:at + 2 * ln]); at += 2 * ln
            self.ops.append({"fo": fo, "rva": rva, "len": ln, "flags": fl, "page": pg, "before": before, "after": after})
        if at != len(raw):
            raise ValueError("RVP1 trailing bytes")

    def op_at(self, va: int):
        rva = va - IMAGE_BASE
        for op in self.ops:
            if op["flags"] != 1 and op["rva"] <= rva < op["rva"] + op["len"]:
                return op, rva - op["rva"]
        return None, 0

    def build(self) -> bytes:
        out = bytearray(self.header)
        struct.pack_into("<I", out, 20, len(self.ops))
        for op in self.ops:
            out += struct.pack("<IIHBB", op["fo"], op["rva"], op["len"], op["flags"], op["page"]) + op["before"] + op["after"]
        return bytes(out)


class Image:
    """Strings and absolute references across the private payload and the EXE operations."""

    def __init__(self, payload: bytes, rvp: Rvp, writable, exe: bytes):
        self.payload, self.rvp, self.writable = bytearray(payload), rvp, writable
        self.log = []
        self.exe = exe                                   # retail file bytes (preimages of new operations)
        self.recon = bytearray(exe)                      # retail file with every operation applied
        for op in rvp.ops:
            self.recon[op["fo"]:op["fo"] + op["len"]] = op["after"]

    def set_file_byte(self, fo: int, value: int):
        """Change one reconstructed byte: inside an owned operation, or as a new one-byte operation whose preimage is
        the retail byte. New operations are admitted only in the EXE cave where file offset == RVA (.text tail)."""
        for op in self.rvp.ops:
            if op["flags"] != 1 and op["fo"] <= fo < op["fo"] + op["len"]:
                op["after"][fo - op["fo"]] = value
                self.recon[fo] = value
                return
        if not any(op["flags"] != 1 and op["fo"] == op["rva"] and abs(op["fo"] - fo) < 0x400 for op in self.rvp.ops):
            raise ValueError(f"no owned code-cave context for file offset {fo:#x}")
        self.rvp.ops.append({"fo": fo, "rva": fo, "len": 1, "flags": 0, "page": 1, "before": bytes([self.exe[fo]]), "after": bytearray([value])})
        self.recon[fo] = value

    def stores(self):
        yield "payload", PAYLOAD_VA, self.payload
        for op in self.rvp.ops:
            if op["flags"] != 1:
                yield f"op@{IMAGE_BASE + op['rva']:#x}", IMAGE_BASE + op["rva"], op["after"]

    def find_string(self, text: str):
        """Exact NUL-terminated occurrences. Inside a payload a string starts after a NUL; an EXE-cave operation may
        end exactly at the string's last character (its terminator is an untouched original zero byte)."""
        needle = text.encode("ascii")
        hits = []
        for name, base, data in self.stores():
            for m in re.finditer(re.escape(needle), bytes(data)):
                end = m.end()
                terminated = end < len(data) and data[end] == 0 or (name != "payload" and end == len(data))
                starts = m.start() == 0 or data[m.start() - 1] == 0 or name != "payload"
                if terminated and starts:
                    hits.append(base + m.start())
        return hits

    def string_room(self, va: int, text: str) -> int:
        """Bytes owned at va for an in-place rewrite (string plus its terminator when that byte is owned here)."""
        if PAYLOAD_VA <= va < PAYLOAD_VA + len(self.payload):
            return len(text) + 1
        op, o = self.rvp.op_at(va)
        return min(len(text) + 1, op["len"] - o)

    def refs(self, va: int):
        """Absolute references: in the payload, and in the reconstructed EXE (they may straddle operations)."""
        pat = struct.pack("<I", va)
        out = [("payload", m.start()) for m in re.finditer(re.escape(pat), bytes(self.payload))]
        out += [("file", m.start()) for m in re.finditer(re.escape(pat), bytes(self.recon))]
        return out

    def write_ref(self, where, at, value: int):
        raw = struct.pack("<I", value)
        if where == "payload":
            self.payload[at:at + 4] = raw
        else:
            for i in range(4):
                if self.recon[at + i] != raw[i]:
                    self.set_file_byte(at + i, raw[i])

    def read(self, va, n):
        if PAYLOAD_VA <= va < PAYLOAD_VA + len(self.payload):
            o = va - PAYLOAD_VA
            return bytes(self.payload[o:o + n])
        op, o = self.rvp.op_at(va)
        return bytes(op["after"][o:o + n]) if op else None

    def write(self, va, data):
        if PAYLOAD_VA <= va < PAYLOAD_VA + len(self.payload):
            o = va - PAYLOAD_VA
            self.payload[o:o + len(data)] = data
            return
        op, o = self.rvp.op_at(va)
        if not op or o + len(data) > op["len"]:
            raise ValueError(f"write outside an owned operation at {va:#x}")
        op["after"][o:o + len(data)] = data
        self.recon[op["fo"] + o:op["fo"] + o + len(data)] = data

    def append(self, data: bytes) -> int:
        while len(self.payload) % 16:
            self.payload.append(0)
        va = PAYLOAD_VA + len(self.payload)
        self.payload += data
        return va

    def replace_string(self, old: str, new: str, expect_refs: int | None = None, only_va: int | None = None):
        hits = [only_va] if only_va else self.find_string(old)
        hits = [h for h in hits if self.refs(h)]
        if len(hits) != 1:
            raise ValueError(f"string {old!r}: expected one referenced occurrence, found {len(hits)}")
        va = hits[0]
        refs = self.refs(va)
        if expect_refs is not None and len(refs) != expect_refs:
            raise ValueError(f"string {old!r}: {len(refs)} references, expected {expect_refs}")
        raw = new.encode("ascii") + b"\0"
        room = self.string_room(va, old)
        # An owned terminator is required in place; a cave string without one keeps the original zero only when the
        # new text has exactly the old length.
        if len(raw) <= room or (len(new) == len(old) and room == len(old)):
            self.write(va, (raw + b"\0" * room)[:room])
            where = "in place"
        else:
            target = self.append(raw)
            for where, at in refs:
                self.write_ref(where, at, target)
            where = f"moved to {target:#x}, {len(refs)} reference(s) rewritten"
        self.log.append(f"{old!r} -> {new!r} ({where})")


def egg_span(text: str, name: str):
    start = text.find(f'<Egg Name="{name}">')
    if start < 0:
        raise ValueError("missing scene egg " + name)
    depth, at = 0, start
    pattern = re.compile(r"<Egg\b|</Egg>")
    for m in pattern.finditer(text, start):
        depth += 1 if m.group(0).startswith("<Egg") else -1
        if depth == 0:
            return start, m.end()
    raise ValueError("unterminated egg " + name)


def set_value(block: str, name: str, value: str) -> str:
    out, n = re.subn(r'(<Value Name="' + re.escape(name) + r'" Type="[^"]+" Value=")[^"]*(")', lambda m: m[1] + value + m[2], block, count=1)
    if not n:
        raise ValueError("scene value missing: " + name)
    return out


def reorder_scene(xml: str, old: dict, new: dict) -> str:
    edits = []
    for cls in CLASSES:
        blocks = {}
        for n, physical in enumerate(old[cls]):
            a, b = egg_span(xml, f"{cls}_Car{n + 1}")
            blocks[physical] = xml[a:b]
        for n in range(len(old[cls])):
            a, b = egg_span(xml, f"{cls}_Car{n + 1}")
            if n >= len(new[cls]):
                edits.append((a, b, ""))          # retired: the class has one widget fewer
                continue
            block = re.sub(r'(<Egg Name=")' + cls + r'_Car\d+(">)', lambda m: m[1] + f"{cls}_Car{n + 1}" + m[2], blocks[new[cls][n]], count=1)
            block = set_value(block, "X ID", str(n))
            block = re.sub(r'Frontend/VehicleSelect/Button\d+XPos', f"Frontend/VehicleSelect/Button{n}XPos", block)
            edits.append((a, b, block))
    for a, b, block in sorted(edits, reverse=True):
        xml = xml[:a] + block + xml[b:]
    return xml


def rename_keys(text: str, renames: dict) -> str:
    for old, new in renames.items():
        # The retired-name block of the new family (e.g. the retail hidden Trooper physics) is replaced.
        text = re.sub(r'[ \t]*<Value Name="Vehicles/' + re.escape(new) + r'/[^\n]*\n', "", text)
        text = text.replace(f'"Vehicles/{old}/', f'"Vehicles/{new}/')
    return text


def transform(src: Path, out: Path, spec: dict) -> dict:
    src = src.resolve(); out = out.resolve()
    if out.exists():
        raise ValueError("choose a fresh output directory")
    profile = json.loads((src / "runtime-profile.json").read_text(encoding="utf-8"))
    ext = profile["native_extension"]
    rvp = Rvp((src / "native-patch-ops.rvp").read_bytes())
    img = Image((src / "native-extension.bin").read_bytes(), rvp, ext.get("writable_ranges", []), Path(spec["retail_exe"]).read_bytes())
    report = {"schema": "mr-roster-v4-transform/1", "source": str(src), "spec": spec}

    # ---- classes -------------------------------------------------------------------------------------------
    d_va = int(profile["vehicle_registry_descriptor"])
    d = struct.unpack("<4s6I4I", img.read(d_va, 44))
    count, counts_va, ptrs_va, rc_va, rl_va = d[3], d[7], d[8], d[9], d[10]
    old_counts = struct.unpack("<3I", img.read(counts_va, 12))
    ptrs = struct.unpack("<3I", img.read(ptrs_va, 12))
    old = {c: list(struct.unpack(f"<{old_counts[i]}I", img.read(ptrs[i], old_counts[i] * 4))) for i, c in enumerate(CLASSES)}
    new = {c: list(spec.get("classes", {}).get(c, old[c])) for c in CLASSES}
    retired = sorted(set(sum(old.values(), [])) - set(sum(new.values(), [])))
    for i, c in enumerate(CLASSES):
        if len(new[c]) > len(old[c]) or set(new[c]) - set(old[c]) or len(set(new[c])) != len(new[c]):
            raise ValueError(f"{c}: only in-class reordering and retirement are supported")
        img.write(ptrs[i], struct.pack(f"<{len(new[c])}I", *new[c]))
    img.write(counts_va, struct.pack("<3I", *[len(new[c]) for c in CLASSES]))
    reverse = {p: (i, n) for i, c in enumerate(CLASSES) for n, p in enumerate(new[c])}
    img.write(rc_va, struct.pack(f"<{count}I", *[reverse.get(p, (0, 0))[0] for p in range(count)]))
    img.write(rl_va, struct.pack(f"<{count}I", *[reverse.get(p, (0, 0))[1] for p in range(count)]))
    for c, (va, prefix) in CLASS_COUNT_OPS.items():
        current = img.read(va, len(prefix) + 1)
        if current is None or current[:len(prefix)] != prefix or current[-1] != len(old[c]):
            raise ValueError(f"class count owner of {c} differs at {va:#x}")
        img.write(va + len(prefix), bytes([len(new[c])]))
    pub = profile_entry = None
    for m in re.finditer(rb"\x81\xfe" + struct.pack("<I", max(old_counts)) + rb"\x0f\x8c", bytes(img.payload)):
        pub = m.start()
    if pub is None:
        raise ValueError("selection publisher bound not found")
    img.payload[pub + 2:pub + 6] = struct.pack("<I", max(len(new[c]) for c in CLASSES))
    report["classes"] = {"old": old, "new": new, "retired": retired}

    # ---- strings ------------------------------------------------------------------------------------------
    renames = spec.get("renames", {})
    for old_name, new_name in renames.items():
        img.replace_string(old_name, new_name)
    for item in spec.get("strings", []):
        img.replace_string(item["old"], item["new"], only_va=int(str(item["va"]), 0) if "va" in item else None)
    report["strings"] = img.log
    for r in img.writable:
        if r["offset"] < len(img.payload) <= r["offset"] + r["size"]:
            raise ValueError("payload growth reached a writable data page")

    # ---- resources ----------------------------------------------------------------------------------------
    index = [l.split("\t") for l in (src / "resource-index.tsv").read_text(encoding="utf-8").splitlines() if l]
    root, new_root = src / "resource-root", out / "resource-root"
    folder = {f"datagx/vehicles/{o.lower()}/": f"DataGx/Vehicles/{n}/" for o, n in renames.items()}
    rows = []
    for digest, size, rel in index:
        target = rel
        for prefix, repl in folder.items():
            if rel.lower().startswith(prefix):
                target = repl + rel[len(prefix):]
        data = None
        low = rel.lower()
        if low in ("datagame/vehicles.xml", "datagame/modifications.xml"):
            data = rename_keys((root / rel).read_text(encoding="utf-8-sig"), renames).encode("utf-8")
        elif low == "datascene/frontendscreens/vehiclesselect.xml" or low == "datascene/frontendscreens/vehicleselect.xml":
            raw = (root / rel).read_bytes()
            bom = raw.startswith(b"\xef\xbb\xbf")
            xml = reorder_scene(raw.decode("utf-8-sig"), old, new)
            data = (b"\xef\xbb\xbf" if bom else b"") + xml.encode("utf-8")
        dst = new_root / target
        dst.parent.mkdir(parents=True, exist_ok=True)
        if data is None:
            os.link(root / rel, dst)
            rows.append((digest, size, target))
        else:
            dst.write_bytes(data)
            rows.append((hashlib.sha256(data).hexdigest(), str(len(data)), target))
    (out / "resource-index.tsv").write_text("".join(f"{d}\t{s}\t{p}\n" for d, s, p in rows), encoding="utf-8")

    # ---- native files and profile ---------------------------------------------------------------------------
    payload = bytes(img.payload)
    if len(payload) > ext["allocation_size"]:
        raise ValueError("payload exceeds its private allocation")
    (out / "native-extension.bin").write_bytes(payload)
    (out / "native-patch-ops.rvp").write_bytes(rvp.build())
    profile["native_extension"] = dict(ext, size=len(payload), sha256=hashlib.sha256(payload).hexdigest())
    profile["roster_v4"] = {"source_runtime": str(src), "classes": new, "retired": retired, "renames": renames}
    (out / "runtime-profile.json").write_text(json.dumps(profile, indent=1) + "\n", encoding="utf-8")
    report["payload_size"] = len(payload)
    (out / "roster-v4-report.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--runtime", type=Path, required=True)
    p.add_argument("--spec", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    r = transform(a.runtime, a.output, json.loads(a.spec.read_text(encoding="utf-8")))
    print(json.dumps({k: r[k] for k in ("classes", "strings", "payload_size")}, indent=1))
