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


def build_profile(roster, retail, core, addon_plan=None, masks=None, *, template):
    """Recompose MRLP from an accepted base; class edits cannot change hook ABI.

    Preserve its hook sites and immutable-range ownership. Recompute all native
    checks and code digest from the final transaction, including retired IDs.
    No sibling checkout or per-car compiled launcher is needed.
    """
    r=parse_roster(roster)
    off,size=struct.unpack_from('<II',template,248)
    old=template[off:off+size]
    if old[:4]!=b'MRLP' or struct.unpack_from('<I',old,4)[0]!=1:raise ValueError('MRLP v1 base required')
    _,_,count,base,extent,nranges,_=struct.unpack_from('<7I',old,4)
    if (base,extent)!=(r['ext_address'],r['ext_size']):raise ValueError('Base allocation changed; regenerate native profile')
    checks,nhooks,nvehicles,human=struct.unpack_from('<4I',old,64)
    at=80;ranges=[]
    for _ in range(nranges):
        start,length=struct.unpack_from('<II',old,at);at+=8
        if start+length>len(r['payload']):raise ValueError('Invalid immutable range')
        ranges.append((start,length))
    for _ in range(checks):
        _,length,_=struct.unpack_from('<IHH',old,at);at+=8+length
    hooks=old[at:at+nhooks*15];at+=nhooks*15
    if at+nvehicles*12!=len(old):raise ValueError('MRLP size mismatch')
    count,classes=class_map(r);d=r['descriptor']
    reverse=struct.unpack_from(f'<{count}I',r['payload'],d[9]-base)
    masks=masks or {};vehicles=[(pid,classes.get(pid,reverse[pid]),masks.get(pid,0) if pid in classes else 0) for pid in range(26,count)]
    native=[op for op in r['ops'] if op['flags']!=1]
    out=bytearray(b'MRLP'+struct.pack('<7I',1,0,count,base,extent,nranges,0))
    out+=hashlib.sha256(b''.join(r['payload'][start:start+length]for start,length in ranges)).digest()
    out+=struct.pack('<4I',len(native),nhooks,len(vehicles),human)
    for start,length in ranges:out+=struct.pack('<II',start,length)
    for op in native:out+=struct.pack('<IHH',op['rva'],len(op['after']),0)+op['after']
    # Hook preimages must still agree with the final mapped native transaction.
    for i in range(nhooks):
        site,kind,length,_=struct.unpack_from('<IBBH',hooks,i*15)
        expected=hooks[i*15+8:i*15+15]
        mapped=bytearray(retail[site:site+7])
        for op in native:
            lo,hi=max(site,op['rva']),min(site+7,op['rva']+len(op['after']))
            if lo<hi:mapped[lo-site:hi-site]=op['after'][lo-op['rva']:hi-op['rva']]
        if length!=7 or mapped!=expected:raise ValueError('Challenge hook preimage changed')
    out+=hooks
    for v in vehicles:out+=struct.pack('<iiI',*v)
    struct.pack_into('<I',out,8,len(out))
    return bytes(out),{'checks':len(native),'registry_count':count,'sdk_vehicles':[{'id':p,'class':'T%d'%(c+1),'mode_mask':m}for p,c,m in vehicles]}


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
