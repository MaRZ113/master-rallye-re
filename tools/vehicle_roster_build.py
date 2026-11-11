"""Compile a Vehicle Manager active roster (MRMods/Vehicles/active) from a V-CAP runtime bundle.

Vehicle Manager phase 2 (docs/vehicle-manager/DESIGN.md). The output is data for the generic dinput8 VehicleRoster
module (src/native/rmod1/vehicle_roster.hpp), which installs it in DllMain instead of the external launcher:

  active/roster.mrvr      MRVR v1 = 256-byte header + the bundle's RVP1 table + its native payload
  active/resources/...    only the indexed files whose bytes differ from what the target game folder already
                          provides (loose file first, then Data.sma), i.e. the vehicle families, composed XML/UI
  active/catalog.json     provenance, record count, classes, resource list

The target game folder is never modified except for MRMods/Vehicles: a fresh active.new/ is written and verified,
then swapped in atomically (the previous active/ is kept as active.prev/).
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, struct, sys, zlib
from pathlib import Path

HEADER = 256
DESCRIPTOR_SIZE = 44
MUTABLE = {"datagame/options.xml"}


def norm(name: str) -> str:
    return name.replace("\\", "/").lower()


def archive_index(path: Path):
    """Data.sma = ZIP local headers only (no central directory)."""
    data = path.read_bytes()
    out, at = {}, 0
    while at + 30 <= len(data):
        sig, _v, flags, method, _t, _d, _crc, cs, us, nl, xl = struct.unpack_from("<IHHHHHIIIHH", data, at)
        if sig != 0x04034B50:
            break
        if flags & 8:
            raise ValueError("Data.sma uses data descriptors; unsupported")
        start = at + 30 + nl + xl
        out[norm(data[at + 30:at + 30 + nl].decode("latin-1"))] = (method, start, cs, us)
        at = start + cs
    return data, out


def archive_sha(blob, entry):
    method, start, cs, _us = entry
    raw = blob[start:start + cs]
    return hashlib.sha256(raw if method == 0 else zlib.decompress(raw, -15)).hexdigest()


def fnv64(data: bytes) -> int:
    h = 0xCBF29CE484222325
    for b in data:
        h ^= b
        h = (h * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def build(runtime: Path, game: Path, label: str) -> dict:
    runtime, game = runtime.resolve(), game.resolve()
    profile = json.loads((runtime / "runtime-profile.json").read_text(encoding="utf-8"))
    ext = profile["native_extension"]
    payload = (runtime / "native-extension.bin").read_bytes()
    if len(payload) != ext["size"] or hashlib.sha256(payload).hexdigest() != ext["sha256"]:
        raise ValueError("native-extension.bin does not match runtime-profile.json")
    rvp = (runtime / "native-patch-ops.rvp").read_bytes()
    if rvp[:4] != b"MRVP" or struct.unpack_from("<H", rvp, 4)[0] != 1:
        raise ValueError("unsupported RVP table")
    descriptor_va = int(profile["vehicle_registry_descriptor"])
    off = descriptor_va - ext["address"]
    if not 0 <= off <= len(payload) - DESCRIPTOR_SIZE or payload[off:off + 4] != b"MRVC":
        raise ValueError("MRVC descriptor not inside the native payload")
    descriptor = payload[off:off + DESCRIPTOR_SIZE]
    rw = ext.get("writable_ranges", [])
    if len(rw) > 8:
        raise ValueError("too many writable ranges")

    header = bytearray(HEADER)
    header[0:4] = b"MRVR"
    struct.pack_into("<IIII", header, 4, 1, HEADER, 0, ext["address"])
    struct.pack_into("<III", header, 20, ext["allocation_size"], ext["size"], len(rw))
    for i, r in enumerate(rw):
        struct.pack_into("<II", header, 32 + i * 8, r["offset"], r["size"])
    struct.pack_into("<I", header, 96, descriptor_va)
    header[100:144] = descriptor
    body = rvp + payload
    struct.pack_into("<IIII", header, 144, HEADER, len(rvp), HEADER + len(rvp), len(payload))
    struct.pack_into("<Q", header, 160, fnv64(body))
    struct.pack_into("<I", header, 168, struct.unpack_from("<I", descriptor, 12)[0])
    header[176:176 + min(79, len(label))] = label.encode("ascii", "replace")[:79]
    roster = bytes(header) + body

    # Resource delta against what the target game folder already provides.
    root = runtime / "resource-root"
    blob, members = archive_index(game / "Data.sma")
    index = [line.split("\t") for line in (runtime / "resource-index.tsv").read_text(encoding="utf-8").splitlines() if line]
    resources, provided = [], 0
    for digest, size, rel in index:
        key = norm(rel)
        if key == "data.sma" or key in MUTABLE:
            continue
        loose = game / Path(rel)
        if loose.is_file():
            same = loose.stat().st_size == int(size) and hashlib.sha256(loose.read_bytes()).hexdigest() == digest
        else:
            entry = members.get(key)
            same = entry is not None and entry[3] == int(size) and archive_sha(blob, entry) == digest
        if same:
            provided += 1
        else:
            resources.append((rel, digest, int(size)))

    mods = game / "MRMods" / "Vehicles"
    staging, active, previous = mods / "active.new", mods / "active", mods / "active.prev"
    if staging.exists():
        shutil.rmtree(staging)
    (staging / "resources").mkdir(parents=True)
    (staging / "roster.mrvr").write_bytes(roster)
    for rel, digest, size in resources:
        source, target = root / Path(rel), staging / "resources" / Path(rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise ValueError(f"resource copy mismatch: {rel}")
    catalog = {
        "schema": "mr-vehicle-roster/1", "label": label,
        "source_runtime": str(runtime), "native_patch_operations_sha256": hashlib.sha256(rvp).hexdigest(),
        "native_extension_sha256": ext["sha256"], "descriptor_va": descriptor_va,
        "record_count": struct.unpack_from("<I", descriptor, 12)[0],
        "classes": profile.get("capacity_profile", {}).get("classes"),
        "game_data_sha256": hashlib.sha256(blob).hexdigest(),
        "resources_provided_by_game": provided,
        "resources": [{"path": rel, "sha256": digest, "size": size} for rel, digest, size in resources],
        "roster_mrvr_sha256": hashlib.sha256(roster).hexdigest(),
    }
    (staging / "catalog.json").write_text(json.dumps(catalog, indent=1) + "\n", encoding="utf-8")
    def retry(action, *args):
        # Explorer/antivirus can hold a folder handle for a moment; the swap is retried, never forced.
        import time
        for attempt in range(4):
            try:
                return action(*args)
            except PermissionError:
                if attempt == 3:
                    raise
                time.sleep(0.5)
    def sync_in_place():
        # A held directory handle (an Explorer window, the indexer) blocks renaming the folder but not its files:
        # copy the new files over, drop stale ones, and replace roster.mrvr last so the loader never sees a mix.
        new_files = {p.relative_to(staging) for p in staging.rglob("*") if p.is_file()}
        for p in sorted(active.rglob("*"), reverse=True):
            rel = p.relative_to(active)
            if p.is_file() and rel not in new_files:
                p.unlink()
            elif p.is_dir() and not any(p.iterdir()):
                try: p.rmdir()
                except OSError: pass
        for rel in sorted(new_files, key=lambda r: r.name == "roster.mrvr"):
            dst = active / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            tmp = dst.with_name(dst.name + ".new")
            shutil.copyfile(staging / rel, tmp)
            os.replace(tmp, dst)
        shutil.rmtree(staging, ignore_errors=True)
    if previous.exists():
        retry(shutil.rmtree, previous)
    try:
        if active.exists():
            retry(os.replace, active, previous)
        retry(os.replace, staging, active)
    except PermissionError:
        sync_in_place()
    return {k: catalog[k] for k in ("label", "record_count", "resources_provided_by_game", "roster_mrvr_sha256")} | {
        "resources": len(resources), "active": str(active)}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--runtime", type=Path, required=True, help="V-CAP runtime bundle (runtime-profile.json, native-*.bin/.rvp, resource-root)")
    p.add_argument("--game", type=Path, required=True, help="target game folder (Data.sma, MRallye.exe)")
    p.add_argument("--label", default="vehicle-roster")
    a = p.parse_args()
    print(json.dumps(build(a.runtime, a.game, a.label), indent=1))
