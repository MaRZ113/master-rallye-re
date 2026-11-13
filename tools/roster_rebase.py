"""Rebase a Vehicle Manager base (manager/base) onto a new V-CAP runtime: new native vehicles, the owner fixes kept.

The manager base is the runtime compiled by `vehicle_roster_build.py` plus fixes authored later on the installed host
(presentation fix 01: race-marker colours and the Trooper small icon; lamps fix 02: the Forklift locked-description
branch; resource fixes: lamps, glass, Forester PS2, scene repairs). Rebuilding the base from a new runtime would drop
them, so this tool replays them three-way:

  old  = the previous runtime compiled the same way (roster.mrvr v1 + resources, no fixes)
  base = the installed manager/base (old + fixes)
  new  = the new runtime compiled the same way

Native (MRVR v1): the per-record initializer pushes (small icon, stats, class, id) and RGBA marker colours of every
record of `old` that `base` changed are written into `new` at the same record; the Forklift locked-description branch
is re-authored with `vehicle_lamp_authoring.unlock_description`. Nothing else may differ between old and base
(checked): the graft applied to `old` must reproduce `base` byte for byte, apart from the header label.

Resources: per file, base == old -> new; new == old -> base; base == new -> either; otherwise a `git merge-file`
three-way text merge. A conflict is resolved only by an explicit rule (--drop-family F removes the conflicting
Vehicles/F/ lines, used for a retired family); anything else stops the tool.

Output: a directory laid out like manager/base (roster.mrvr v1 + resources + the base's side files), ready for
`roster_loader_profile.py` (v2) and `vehicle_manager.py import-base`.
"""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, struct, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from roster_v4 import Image as NativeImage, Rvp, record_pushes, write_push   # noqa: E402
from roster_loader_profile import strip_v2                                 # noqa: E402
from vehicle_roster_build import fnv64                                     # noqa: E402


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load(raw: bytes, exe: bytes):
    if raw[:4] != b"MRVR":
        raise ValueError("MRVR expected")
    if struct.unpack_from("<I", raw, 4)[0] != 1:
        raw = strip_v2(raw)
    ro, rl, po, pl = struct.unpack_from("<4I", raw, 144)
    if fnv64(raw[256:]) != struct.unpack_from("<Q", raw, 160)[0]:
        raise ValueError("MRVR damaged")
    return raw, NativeImage(raw[po:po + pl], Rvp(raw[ro:ro + rl]), [], exe)


def value(img, slot) -> int:
    store, at, width = slot
    data = img.payload if store == "payload" else img.recon
    return int.from_bytes(bytes(data[at:at + width]), "little")


def write_colour(img, slot, bits: int):
    """Same rule as vehicle_presentation_fix: payload floats in place; EXE immediates edit the owning RVP operation
    byte by byte, or add an exact-preimage one-byte operation."""
    store, at, _ = slot
    if store == "payload":
        struct.pack_into("<I", img.payload, at, bits)
        return
    for index, byte in enumerate(struct.pack("<I", bits)):
        pos = at + index
        if img.recon[pos] == byte:
            continue
        owned = next((o for o in img.rvp.ops if o["flags"] != 1 and o["fo"] <= pos < o["fo"] + o["len"]), None)
        if owned:
            owned["after"][pos - owned["fo"]] = byte
        else:
            img.rvp.ops.append({"fo": pos, "rva": pos, "len": 1, "flags": 0, "page": 1,
                                "before": img.exe[pos:pos + 1], "after": bytearray([byte])})
        img.recon[pos] = byte


def native_delta(old, base, records: int):
    """What base changed relative to old, per record: {cid: {'pushes': {i: v}, 'colour': [bits x4]}}."""
    from vehicle_presentation_fix import marker_slots
    so, sb = marker_slots(old), marker_slots(base)
    delta = {}
    for cid in range(records):
        row = {}
        if cid >= 25:   # stock records are compiler code: only their colour immediates are authorable
            po, pb = record_pushes(old, cid), record_pushes(base, cid)
            pushes = {i: value(base, b) for i, (a, b) in enumerate(zip(po, pb)) if value(old, a) != value(base, b)}
            if pushes:
                row["pushes"] = pushes
        co = [value(old, s) for s in so[cid]]
        cb = [value(base, s) for s in sb[cid]]
        if co != cb:
            row["colour"] = cb
        if row:
            delta[cid] = row
    return delta


def apply_delta(img, delta, unlock: bool):
    from vehicle_presentation_fix import marker_slots
    slots = marker_slots(img)
    for cid, row in delta.items():
        pushes = record_pushes(img, cid)
        for i, v in row.get("pushes", {}).items():
            write_push(img, pushes[int(i)], v)
        for slot, bits in zip(slots[cid], row.get("colour", [])):
            write_colour(img, slot, bits)
    report = None
    if unlock:
        from vehicle_lamp_authoring import unlock_description
        report = unlock_description(None, img)
    return report


def serialize(raw: bytes, img, label: bytes) -> bytes:
    rvp = img.rvp.build()
    payload = bytes(img.payload)
    header = bytearray(raw[:256])
    if len(payload) > struct.unpack_from("<I", header, 20)[0]:
        raise ValueError("native payload exceeds the roster allocation")
    struct.pack_into("<I", header, 24, len(payload))
    struct.pack_into("<4I", header, 144, 256, len(rvp), 256 + len(rvp), len(payload))
    struct.pack_into("<Q", header, 160, fnv64(rvp + payload))
    header[176:256] = label.ljust(80, b"\0")
    return bytes(header) + rvp + payload


def tree(root: Path):
    return {p.relative_to(root).as_posix(): p for p in sorted(root.rglob("*")) if p.is_file()}


def merge_text(old: bytes, base: bytes, new: bytes, drop_families) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        for name, data in (("new", new), ("old", old), ("base", base)):
            (t / name).write_bytes(data)
        run = subprocess.run(["git", "merge-file", "-p", str(t / "new"), str(t / "old"), str(t / "base")],
                             capture_output=True)
        if run.returncode < 0:
            raise ValueError("git merge-file failed")
        text = run.stdout.decode("utf-8")
    pattern = re.compile(r"<<<<<<< [^\n]*\n(.*?)=======\r?\n(.*?)>>>>>>> [^\n]*\n", re.S)

    def resolve(m):
        ours, theirs = m.group(1), m.group(2)
        lines = ours.splitlines(keepends=True)
        kept = [l for l in lines if not any(f"Vehicles/{f}/" in l for f in drop_families)]
        if theirs.strip() or not drop_families or len(kept) == len(lines):
            raise ValueError("unresolved three-way conflict:\n" + ours[:400] + "\n=======\n" + theirs[:400])
        return "".join(kept)
    text = pattern.sub(resolve, text)
    if "<<<<<<<" in text or any(f"Vehicles/{f}/" in text for f in drop_families):
        raise ValueError("merge left conflict markers or a dropped family")
    return text.encode("utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--old", type=Path, required=True, help="previous runtime compiled by vehicle_roster_build (active dir)")
    ap.add_argument("--base", type=Path, required=True, help="installed manager/base")
    ap.add_argument("--new", type=Path, required=True, help="new runtime compiled by vehicle_roster_build (active dir)")
    ap.add_argument("--retail", type=Path, required=True, help="retail MRallye.exe")
    ap.add_argument("--drop-family", action="append", default=[], help="retired family whose conflicting lines go")
    ap.add_argument("--label", default="Roster rebase")
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    if a.output.exists():
        raise SystemExit(f"{a.output} already exists")
    exe = a.retail.read_bytes()
    raw_old, img_old = load((a.old / "roster.mrvr").read_bytes(), exe)
    raw_base, img_base = load((a.base / "roster.mrvr").read_bytes(), exe)
    raw_new, img_new = load((a.new / "roster.mrvr").read_bytes(), exe)
    records = struct.unpack_from("<I", raw_old, 168)[0]
    if struct.unpack_from("<I", raw_base, 168)[0] != records or struct.unpack_from("<I", raw_new, 168)[0] < records:
        raise ValueError("record counts: base must equal old, new must extend it")
    delta = native_delta(img_old, img_base, records)
    unlock = b"UNLOCK WITH UNLOCK CARS CHEAT\0" in bytes(img_base.payload) and \
        b"UNLOCK WITH UNLOCK CARS CHEAT\0" not in bytes(img_old.payload)
    # Proof: the graft replayed on old reproduces base (header label aside).
    _, proof = load(raw_old, exe)
    apply_delta(proof, delta, unlock)
    replay = serialize(raw_old, proof, raw_base[176:256].rstrip(b"\0"))
    base_v1 = strip_v2((a.base / "roster.mrvr").read_bytes()) if struct.unpack_from("<I", (a.base / "roster.mrvr").read_bytes(), 4)[0] != 1 else (a.base / "roster.mrvr").read_bytes()
    if replay[256:] != base_v1[256:] or replay[:176] != base_v1[:176]:
        raise ValueError("base has native changes the graft does not explain; review before rebasing")
    unlock_report = apply_delta(img_new, delta, unlock)
    roster = serialize(raw_new, img_new, a.label.encode("ascii"))

    out = a.output
    (out / "resources").mkdir(parents=True)
    (out / "roster.mrvr").write_bytes(roster)
    O, B, N = tree(a.old / "resources"), tree(a.base / "resources"), tree(a.new / "resources")
    decisions = {"new": 0, "base": 0, "same": 0, "merged": []}
    for rel in sorted(set(O) | set(B) | set(N)):
        o, b, n = (d[rel].read_bytes() if rel in d else None for d in (O, B, N))
        if b == o:
            data, how = n, "new"
        elif n == o:
            data, how = b, "base"
        elif b == n:
            data, how = b, "same"
        else:
            if None in (o, b, n):
                raise ValueError(f"{rel}: added/removed on both sides")
            data, how = merge_text(o, b, n, a.drop_family), "merged"
        if how == "merged":
            decisions["merged"].append(rel)
        else:
            decisions[how] += 1
        if data is not None:
            p = out / "resources" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
    for side in ("names.json", "addon-brake-lamps.tsv"):
        if (a.base / side).is_file():
            shutil.copy2(a.base / side, out / side)
    catalog = json.loads((a.new / "catalog.json").read_text())
    base_catalog = json.loads((a.base / "catalog.json").read_text())
    if "variants" in base_catalog:
        catalog["variants"] = base_catalog["variants"]
    catalog.update(label=a.label, roster_mrvr_sha256=sha(roster),
                   resources=[{"path": p.relative_to(out / "resources").as_posix(), "size": p.stat().st_size,
                               "sha256": sha(p.read_bytes())} for p in sorted((out / "resources").rglob("*")) if p.is_file()],
                   rebase={"tool": "tools/roster_rebase.py", "old_roster_sha256": sha(raw_old),
                           "base_roster_sha256": sha((a.base / "roster.mrvr").read_bytes()), "new_roster_sha256": sha(raw_new),
                           "native_delta_records": sorted(delta), "unlock_description": unlock_report,
                           "resources": decisions, "dropped_families": a.drop_family})
    (out / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"roster_sha256": sha(roster), "native_delta": {str(k): v for k, v in delta.items()},
                      "unlock": bool(unlock_report), "resources": decisions}, indent=1))


if __name__ == "__main__":
    main()
