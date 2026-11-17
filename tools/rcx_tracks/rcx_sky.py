"""RCX skybox -> Atmosphere course sky (RCX-SKY1).

Each RCX PC stage has skybox.qto (a textured box/dome around the camera, QTO v7.2) and its .tex faces. The skybox is
ray-cast into the MR sky-cylinder panorama the Atmosphere custom sky uses (CustomSkyProjection=1: v from elevation,
row 0 = horizon, v = .003 + .995 * tan(elevation)), then exported as an Atmosphere sky pair that keeps the native MR
alpha masks byte for byte (the runtime only accepts the preset-3 masks): clouds.dxt = the panorama, layer.dxt = its
azimuthal mean (the haze band; the native layer is drawn over the whole dome).

Azimuth: u in [0, 1) = MR world azimuth atan2(z, x) / 2pi. The renderer (RCX-SKY1) re-anchors the native dome U of a
course sky to that azimuth, so RCX horizons line up with the stage. RCX -> MR axes as rcx_to_course.to_mr: (-x, -y, z).

    py -3 rcx_sky.py --level <rcx levels>/<stage> --native <MR Data>/DataGx/Misc/Sky/cloud3 --out <dir> [--scene RcxScottish2]
    -> <out>/<scene>/sky/{clouds,layer}.dxt (+ .png previews) and sky.json; copy <scene>/sky into
       <host>/Atmosphere/courses/<scene>/ (rcx_sky.py --host does it).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rcx_tex import decode_tex  # noqa: E402

WIDTH, HEIGHT = 1024, 192


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def read_qto(raw: bytes) -> dict:
    """QTO v7.2 (same bounded layout as source-formats/rcx/qto_inspect.py)."""
    ver, sub, ng, nt, nv, ni, na, _ = struct.unpack_from("<8I", raw)
    if (ver, sub) != (7, 2) or ng > 1000 or nt > 1000 or nv > 65535:
        raise ValueError("unsupported QTO")
    off = 32 + ng * 57
    groups = []
    for i in range(ng):
        p = 32 + i * 57
        _, tex = struct.unpack_from("<2I", raw, p)
        start, count, ntri = struct.unpack_from("<3I", raw, p + 17)
        groups.append((tex, start, start + count))
    names = []
    for _ in range(nt):
        end = raw.index(b"\0", off)
        names.append(raw[off:end].decode("ascii"))
        off = end + 1
    if off + nv * 64 + ni * 2 + na * 2 != len(raw):
        raise ValueError("unexpected QTO array layout")
    pos = np.array([struct.unpack_from("<3f", raw, off + i * 64) for i in range(nv)], np.float64)
    uv = np.array([struct.unpack_from("<2f", raw, off + i * 64 + 48) for i in range(nv)], np.float64)
    idx = np.array(struct.unpack_from(f"<{ni}H", raw, off + nv * 64), np.int64)
    return {"groups": groups, "textures": names, "positions": pos, "uv": uv, "indices": idx}


def directions():
    u = (np.arange(WIDTH) + .5) / WIDTH
    v = (np.arange(HEIGHT) + .5) / HEIGHT
    theta = 2 * np.pi * u
    elev = np.arctan(np.maximum(0, (v - .003) / .995))
    ce = np.cos(elev)[:, None]
    mr = np.stack(np.broadcast_arrays(ce * np.cos(theta)[None, :], np.sin(elev)[:, None] + 0 * theta[None, :],
                                      ce * np.sin(theta)[None, :]), axis=-1).reshape(-1, 3)
    return mr * np.array([-1.0, -1.0, 1.0])            # MR -> RCX (to_mr is its own inverse)


def project(level: Path) -> tuple[Image.Image, dict]:
    q = read_qto((level / "skybox.qto").read_bytes())
    textures = []
    for name in q["textures"]:
        t = decode_tex((level / Path(name.replace("\\", "/")).name).read_bytes())
        textures.append(np.frombuffer(t["rgba"], np.uint8).reshape(t["height"], t["width"], 4)[:, :, :3].astype(np.float64))
    dirs = directions()
    dist = np.full(len(dirs), np.inf)
    rgb = np.zeros((len(dirs), 3))
    P, UV, I = q["positions"], q["uv"], q["indices"]
    for tex, start, end in q["groups"]:
        img = textures[tex]
        h, w = img.shape[:2]
        for t in range(start, end, 3):
            f = I[t:t + 3]
            a, b, c = P[f]
            e1, e2 = b - a, c - a
            cross = np.cross(dirs, e2)
            det = cross @ e1
            ok = np.abs(det) > 1e-12
            inv = np.divide(1, det, out=np.zeros_like(det), where=ok)
            tv = -a
            pp = (cross @ tv) * inv
            qv = np.cross(tv, e1)
            qq = (dirs @ qv) * inv
            tt = float(e2 @ qv) * inv
            hit = ok & (pp >= -1e-6) & (qq >= -1e-6) & (pp + qq <= 1 + 1e-6) & (tt > 1e-6) & (tt < dist)
            ids = np.flatnonzero(hit)
            if not len(ids):
                continue
            wts = np.stack((1 - pp[ids] - qq[ids], pp[ids], qq[ids]), axis=1)
            co = wts @ UV[f]
            x = np.clip((co[:, 0] % 1.0 if False else np.clip(co[:, 0], 0, 1)) * (w - 1), 0, w - 1)
            y = np.clip(np.clip(co[:, 1], 0, 1) * (h - 1), 0, h - 1)
            xi, yi = x.astype(int), y.astype(int)
            xn, yn = np.minimum(xi + 1, w - 1), np.minimum(yi + 1, h - 1)
            fx, fy = (x - xi)[:, None], (y - yi)[:, None]
            rgb[ids] = (img[yi, xi] * (1 - fx) + img[yi, xn] * fx) * (1 - fy) + (img[yn, xi] * (1 - fx) + img[yn, xn] * fx) * fy
            dist[ids] = tt[ids]
    cover = float(np.isfinite(dist).mean())
    if cover < .99:
        raise ValueError(f"{level.name}: sky ray coverage {cover:.3f}")
    return Image.fromarray(np.rint(np.clip(rgb.reshape(HEIGHT, WIDTH, 3), 0, 255)).astype(np.uint8)), {
        "ray_coverage": cover, "textures": q["textures"], "triangles": int(len(I) // 3)}


def export(pano: Image.Image, native: Path, out: Path) -> dict:
    sys.path.insert(0, str(HERE.parents[2] / "master-rallye-re-base" / "src"))
    from master_rallye.dxt import parse_dxt
    out.mkdir(parents=True, exist_ok=True)
    rgb = np.asarray(pano.resize((256, 256), Image.Resampling.LANCZOS)).copy()
    seam = np.rint((rgb[:, 0].astype(float) + rgb[:, -1]) / 2).astype(np.uint8)
    rgb[:, 0] = seam; rgb[:, -1] = seam
    rows = []
    for layer, name in enumerate(("clouds", "layer")):
        t = parse_dxt(native / ("cloud3-tga.dxt" if not layer else "layer3-tga.dxt"))
        color = rgb if not layer else np.broadcast_to(np.rint(rgb.mean(axis=1, keepdims=True)).astype(np.uint8), rgb.shape)
        bgra = np.empty((256, 256, 4), np.uint8)
        bgra[:, :, :3] = color[:, :, ::-1]
        bgra[:, :, 3] = np.frombuffer(t.bgra, np.uint8).reshape(256, 256, 4)[:, :, 3]
        payload = t.header + bgra.tobytes()
        (out / (name + ".dxt")).write_bytes(payload)
        Image.fromarray(bgra[:, :, [2, 1, 0, 3]]).save(out / (name + ".png"))
        rows.append({"name": name, "sha256": sha(payload), "alpha_sha256": sha(bgra[:, :, 3].tobytes())})
    fog = np.median(rgb[:6], axis=(0, 1)).astype(int).tolist()
    return {"resources": rows, "horizon_rgb": fog}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--level", type=Path, action="append", required=True, help="extracted RCX level folder (repeatable)")
    ap.add_argument("--scene", action="append", help="MR scene per level (default Rcx<Level>, e.g. RcxScottish2)")
    ap.add_argument("--native", type=Path, required=True, help="MR DataGx/Misc/Sky/cloud3 (native alpha masks)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--host", type=Path, help="also install into <host>/Atmosphere/courses/<scene>/sky")
    a = ap.parse_args(argv)
    report = []
    for i, level in enumerate(a.level):
        scene = (a.scene[i] if a.scene and i < len(a.scene) else "Rcx" + level.name[:1].upper() + level.name[1:])
        pano, info = project(level)
        dest = a.out / scene / "sky"
        dest.mkdir(parents=True, exist_ok=True)
        pano.save(a.out / scene / "panorama.png")
        info.update(export(pano, a.native, dest))
        info.update({"scene": scene, "level": level.name, "azimuth": "u = MR atan2(z, x) / 2pi (renderer re-anchors U)",
                     "projection": "MR sky cylinder, v = .003 + .995 * tan(elevation), row 0 = horizon"})
        (dest / "sky.json").write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8")
        if a.host:
            target = a.host / "Atmosphere" / "courses" / scene / "sky"
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(dest, target)
        report.append({k: info[k] for k in ("scene", "ray_coverage", "horizon_rgb")})
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
