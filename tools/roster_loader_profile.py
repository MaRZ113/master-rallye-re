"""Add the MRLP loader profile to a roster: roster.mrvr v1 -> v2 (Roster V4 stage 4, loader independence).

The SDK/G1 Challenge composition used to be compiled into dinput8.dll per roster (extra_sdk_profile.hpp,
extra_options_package.hpp sdk_vehicles), so a loader built for V-CAP3 refused the V4 roster (BOOT_B_FAILED). This
tool derives that profile from the roster itself and stores it inside roster.mrvr (format in
src/native/rmod1/roster_loader_profile.hpp); a roster-independent loader reads it from there.

  checks      every native RVP operation of the roster as installed (rva, replacement bytes)
  hooks       the two F3 Challenge consumer sites with the bytes the roster maps there, validated by the accepted
              extra_options_sdk_binding.propose() against the F3 plan of the retail EXE + runtime core
  extension   private payload address/size and the immutable ranges of the roster's writable-range layout
  vehicles    physical IDs > 24 offered by the roster's MRVC class tables, their class, and the AI mode mask
              (from the V-CAP addon plan by physical ID; retired IDs are not offered and are left out)
  challenge_human_offset = RaceTest identity displacement - 4 (base + stride - 8, as the compiled profile had it)
"""
from __future__ import annotations
import argparse, hashlib, json, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from extra_options_sdk_binding import propose, extension_regions, RETAIL_LOAD  # noqa: E402
from r_mod1_native_plan import build_plan, public_plan, make_challenge_preview_code, make_challenge_consumer_code  # noqa: E402

HEADER = 256
MODES = ["quick_race", "rallye_cup", "master_rallye", "invitation", "challenge"]
HOOK_CODES = {"challenge-preview-identity": 0, "challenge-race-consume": 1}


def fnv64(data: bytes) -> int:
    h = 0xCBF29CE484222325
    for b in data:
        h = ((h ^ b) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return h


def parse_roster(data: bytes):
    if data[:4] != b"MRVR" or struct.unpack_from("<I", data, 4)[0] != 1:
        raise ValueError("expected a roster.mrvr v1")
    ext_address, ext_alloc, ext_size, rw_count = struct.unpack_from("<IIII", data, 16)
    rw = [struct.unpack_from("<II", data, 32 + i * 8) for i in range(rw_count)]
    rvp_off, rvp_size, ext_off, ext_size2 = struct.unpack_from("<IIII", data, 144)
    if fnv64(data[HEADER:]) != struct.unpack_from("<Q", data, 160)[0] or ext_size != ext_size2:
        raise ValueError("roster digest/layout mismatch")
    rvp = data[rvp_off:rvp_off + rvp_size]
    count, at, ops = struct.unpack_from("<I", rvp, 20)[0], 120, []
    for _ in range(count):
        fo, rva, ln, fl, pg = struct.unpack_from("<IIHBB", rvp, at); at += 12
        ops.append({"rva": rva, "flags": fl, "before": rvp[at:at + ln], "after": rvp[at + ln:at + 2 * ln]}); at += 2 * ln
    payload = data[ext_off:ext_off + ext_size]
    descriptor = struct.unpack_from("<11I", data, 100)
    return dict(ext_address=ext_address, ext_size=ext_size, writable=[{"offset": o, "size": s} for o, s in rw],
                ops=ops, payload=payload, descriptor=descriptor)


def class_map(r):
    d, payload, base = r["descriptor"], r["payload"], r["ext_address"]
    if d[0] != struct.unpack("<I", b"MRVC")[0]:
        raise ValueError("MRVC descriptor expected")
    count, classes = d[3], d[5]
    counts = struct.unpack_from(f"<{classes}I", payload, d[7] - base)
    tables = struct.unpack_from(f"<{classes}I", payload, d[8] - base)
    out = {}
    for c in range(classes):
        for i in range(counts[c]):
            out[struct.unpack_from("<I", payload, tables[c] - base + 4 * i)[0]] = c
    return count, out


def masks_from_plan(addon_plan: dict) -> dict:
    return {a["physical_id"]: sum(1 << i for i, m in enumerate(MODES) if a["ai_eligibility"].get(m, {}).get("enabled", False))
            for a in addon_plan["addons"]}


def read_profile_masks(roster_v2: bytes) -> dict:
    """AI masks by physical ID from an existing MRLP section (the Vehicle Manager keeps them with its base roster)."""
    at, size = struct.unpack_from("<II", roster_v2, 248)
    p = roster_v2[at:at + size]
    if p[:4] != b"MRLP":
        raise ValueError("no MRLP section")
    ranges, checks, hooks, vehicles = struct.unpack_from("<I", p, 24)[0], *struct.unpack_from("<III", p, 64)
    o = 80 + ranges * 8
    for _ in range(checks):
        o += 8 + struct.unpack_from("<H", p, o + 4)[0]
    o += hooks * 15
    return {pid: mask for pid, _cls, mask in (struct.unpack_from("<iiI", p, o + 12 * i) for i in range(vehicles))}


def strip_v2(roster: bytes) -> bytes:
    """roster.mrvr v2 -> the v1 roster it was made from (profile removed, digest recomputed)."""
    if struct.unpack_from("<I", roster, 4)[0] == 1:
        return roster
    at = struct.unpack_from("<I", roster, 248)[0]
    header = bytearray(roster[:HEADER])
    struct.pack_into("<I", header, 4, 1)
    header[248:256] = bytes(8)
    struct.pack_into("<Q", header, 160, fnv64(roster[HEADER:at]))
    return bytes(header) + roster[HEADER:at]


def build_profile(roster: bytes, retail: bytes, core: bytes, addon_plan: dict | None = None, masks: dict | None = None):
    r = parse_roster(roster)
    native = [op for op in r["ops"] if op["flags"] != 1]
    sdk = {"operations": [{"rva": op["rva"], "expected_original_bytes": op["before"].hex(),
                           "replacement_bytes": op["after"].hex(), "name": f"rvp-{op['rva']:x}"} for op in native]}
    public = public_plan(build_plan(retail, core, checkpoint="g1"))
    consumers = {o["id"]: o["rva"] for o in public["operations"] if o["id"] in HOOK_CODES}
    # The RaceTest identity displacement the roster maps into the consumer instruction.
    mapped = bytearray(RETAIL_LOAD)
    site = consumers["challenge-race-consume"]
    for op in native:
        lo, hi = max(op["rva"], site), min(op["rva"] + len(op["after"]), site + 7)
        if lo < hi:
            mapped[lo - site:hi - site] = op["after"][lo - op["rva"]:hi - op["rva"]]
    identity = struct.unpack_from("<I", mapped, 3)[0]
    proposal = propose(sdk, public, make_challenge_preview_code(), make_challenge_consumer_code(), identity_offset=identity)
    writable, immutable = extension_regions({"address": r["ext_address"], "size": r["ext_size"],
                                             "writable_ranges": r["writable"], "code_sha256": "0" * 64})
    code = b"".join(r["payload"][x["offset"]:x["offset"] + x["size"]] for x in immutable)
    count, classes = class_map(r)
    masks = masks if masks is not None else masks_from_plan(addon_plan)
    vehicles = [(pid, classes[pid], masks[pid]) for pid in sorted(classes) if pid > 24 and pid in masks]
    out = bytearray(b"MRLP" + struct.pack("<IIIIIII", 1, 0, count, r["ext_address"], r["ext_size"], len(immutable), 0))
    out += hashlib.sha256(code).digest()
    out += struct.pack("<IIII", len(proposal["sdk_checks"]), len(proposal["challenge"]), len(vehicles), identity - 4)
    for x in immutable:
        out += struct.pack("<II", x["offset"], x["size"])
    for c in proposal["sdk_checks"]:
        b = bytes.fromhex(c["expected_hex"])
        out += struct.pack("<IHH", c["rva"], len(b), 0) + b
    for h in sorted(proposal["challenge"], key=lambda x: HOOK_CODES[x["id"]]):
        out += struct.pack("<IBBH", h["rva"], HOOK_CODES[h["id"]], 7, 0) + bytes.fromhex(h["expected_mapped_hex"])
    for pid, cls, mask in vehicles:
        out += struct.pack("<iiI", pid, cls, mask)
    struct.pack_into("<I", out, 8, len(out))
    summary = {"checks": len(proposal["sdk_checks"]), "hooks": [h["id"] for h in proposal["challenge"]],
               "challenge_identity_offset": identity, "challenge_human_offset": identity - 4,
               "immutable_code_sha256": hashlib.sha256(code).hexdigest(), "registry_count": count,
               "sdk_vehicles": [{"id": v[0], "class": "T%d" % (v[1] + 1), "mode_mask": v[2]} for v in vehicles],
               "not_offered": sorted(set(masks) - set(classes))}
    return bytes(out), summary


def to_v2(roster: bytes, profile: bytes) -> bytes:
    header = bytearray(roster[:HEADER])
    struct.pack_into("<I", header, 4, 2)
    header[248:256] = struct.pack("<II", len(roster), len(profile))
    header[176:248] = header[176:248][:71] + b"\0"        # label shrinks to 71 characters in v2
    body = roster[HEADER:] + profile
    struct.pack_into("<Q", header, 160, fnv64(body))
    return bytes(header) + body


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--roster", type=Path, required=True, help="roster.mrvr v1")
    p.add_argument("--retail", type=Path, required=True, help="retail MRallye.exe (bf8aef32)")
    p.add_argument("--core", type=Path, required=True, help="MRallyeRandomizerRuntime.dll the loader uses")
    p.add_argument("--addon-plan", type=Path, required=True, help="V-CAP addon-plan.json (AI eligibility by physical ID)")
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    roster = a.roster.read_bytes()
    profile, summary = build_profile(roster, a.retail.read_bytes(), a.core.read_bytes(), json.loads(a.addon_plan.read_text()))
    v2 = to_v2(roster, profile)
    a.output.write_bytes(v2)
    summary.update(output=str(a.output), output_sha256=hashlib.sha256(v2).hexdigest(), profile_bytes=len(profile))
    print(json.dumps(summary, indent=1))
