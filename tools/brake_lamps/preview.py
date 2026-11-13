"""Native D3D9 brake-lamp preview: stage an MRLP scene from a car.dx and capture it with mr-lamp-preview.exe.

Modes reproduce what the PS2 Port renderer submits for the lamp layers:

* ``off``  - brake released: body + blight case 1 (OFF lamp glass).
* ``pc``   - BrakeGlow=0: blight case 2 drawn natively. Core opaque MODULATE with ZWRITE on; halo SRCALPHA/INVSRCALPHA
  with ZWRITE on (the states fleet_lamp_native.hpp verifies before it touches a lamp draw).
* ``ps2``  - BrakeGlow=1: core SELECTARG1 PS2BrakeOn (opaque, native ZWRITE); halo SELECTARG1 PS2BrakeGlow ONE/ONE with
  ZWRITE off (LampTransaction::brake_on_pass / emissive_pass). ZENABLE/ZFUNC are not touched by the renderer.

Body-scoped sets (MR-ADDON-LAMPS 3) are honoured through ``suppress``: draw indices of the set that is not presented.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import struct
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NATIVE_SOURCE = Path(__file__).resolve().parent / 'native' / 'lamp_preview.cpp'
DEFAULT_EXE = ROOT / '.research-output' / 'brake-lamps' / 'bin' / 'mr-lamp-preview.exe'

BLEND_OPAQUE, BLEND_ALPHA, BLEND_ADD = 0, 1, 2
CULL_NONE = 1
OP_MODULATE, OP_TEXTURE, OP_DIFFUSE = 0, 1, 2


@dataclass
class Camera:
    eye: tuple
    target: tuple
    up: tuple = (0.0, 1.0, 0.0)
    fov: float = 30.0
    width: int = 640
    height: int = 400

    @staticmethod
    def around(target, direction, distance, **kw) -> 'Camera':
        t = np.asarray(target, dtype=float)
        e = t + np.asarray(direction, dtype=float) * distance
        return Camera(tuple(e), tuple(t), **kw)


def gxi_bgra(data: bytes, *, opaque=False) -> tuple[int, int, bytes]:
    """PS2 Port 16x16 RGBA asset (8-byte header + 256 RGBA) -> BGRA rows, as BrakeGlow::BrakeGlow decodes it."""
    if len(data) != 1032:
        raise ValueError('PS2 lamp asset must be 1032 bytes')
    out = bytearray()
    for i in range(256):
        r, g, b, a = data[8 + 4 * i: 12 + 4 * i]
        out += bytes((b, g, r, 255 if opaque else a))
    return 16, 16, bytes(out)


def build_compiler(output: Path = DEFAULT_EXE) -> Path:
    """Compile the previewer with the local MSVC toolchain (x64)."""
    import sys
    sys.path.insert(0, str(ROOT / 'tools'))
    from build_r_mod1_candidate import locate_toolchain, compiler_environment
    vc, tool = locate_toolchain()
    env = compiler_environment(vc, 'x64')
    output.parent.mkdir(parents=True, exist_ok=True)
    cl = tool / 'bin/Hostx64/x64/cl.exe'
    result = subprocess.run([str(cl), '/nologo', '/std:c++17', '/EHsc', '/O2', '/MT', str(NATIVE_SOURCE), '/Fe:' + str(output),
                             '/Fo:' + str(output.with_suffix('.obj'))], env=env, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return output


class Scene:
    def __init__(self):
        self.textures = []
        self.keys = {}
        self.draws = []

    def texture(self, key, width, height, bgra) -> int:
        if key not in self.keys:
            self.keys[key] = len(self.textures)
            self.textures.append((width, height, bgra))
        return self.keys[key]

    def draw(self, positions, colors, uvs, triangles, *, texture=-1, blend=BLEND_OPAQUE, zwrite=True, zenable=True,
             colorop=OP_MODULATE, alphatest=False):
        self.draws.append((texture, blend, zwrite, zenable, colorop, alphatest, positions, colors, uvs, triangles))

    def encode(self, camera: Camera, clear=0xff2b3038) -> bytes:
        out = bytearray(struct.pack('<4I', 0x504c524d, 1, camera.width, camera.height))
        out += struct.pack('<9f3f', *camera.eye, *camera.target, *camera.up, camera.fov, 0.05, 200.0)
        out += struct.pack('<3I', clear, len(self.textures), len(self.draws))
        for w, h, px in self.textures:
            if len(px) != w * h * 4:
                raise ValueError('texture byte size')
            out += struct.pack('<2I', w, h) + px
        for texture, blend, zwrite, zenable, colorop, alphatest, pos, col, uv, tri in self.draws:
            out += struct.pack('<i6I', texture, blend, int(zwrite), int(zenable), CULL_NONE, colorop, int(alphatest))
            tri = np.asarray(tri, dtype=np.uint32).reshape(-1)
            out += struct.pack('<2I', len(pos), len(tri))
            for p, c, t in zip(pos, col, uv):
                out += struct.pack('<3fI2f', *p, c, *t)
            out += tri.tobytes()
        return bytes(out)


def mirror_camera(camera: Camera) -> Camera:
    """The SDK geometry is right-handed (see master_rallye.preview_scene.preview_bgra); the native-LH capture tool
    renders it through a mirrored model so lettering reads correctly. Mirror X of eye/target and of the scene."""
    e, t = list(camera.eye), list(camera.target)
    e[0], t[0] = -e[0], -t[0]
    return Camera(tuple(e), tuple(t), camera.up, camera.fov, camera.width, camera.height)


def stage(raw: bytes, read_texture, mode: str, *, ps2_assets=None, suppress=(), replace=None, highlight=None) -> Scene:
    """Scene for one presentation mode.

    ``read_texture(name)`` returns .dxt bytes for a native texture name. ``replace`` maps draw index -> DrawGeometry
    (authoring preview of a candidate layer). ``highlight`` maps draw index -> ARGB for a flat diagnostic colour.
    """
    if mode not in ('off', 'pc', 'ps2'):
        raise ValueError('mode must be off, pc or ps2')
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.dxt import parse_dxt_bytes
    from master_rallye.topology_writer import source_geometry
    from master_rallye.preview_scene import logical_cases
    m = parse_dx_bytes(raw)
    geometry = source_geometry(m)
    cases, _ = logical_cases(m)
    scene = Scene()
    replace = replace or {}
    highlight = highlight or {}

    def tex(name):
        if name.lower() == 'null':
            return -1
        try:
            t = parse_dxt_bytes(read_texture(name + '.dxt'), name)
        except KeyError:
            return -1
        return scene.texture(name, t.width, t.height, bytes(t.bgra))

    ps2 = {}
    if mode == 'ps2':
        if not ps2_assets:
            raise ValueError('ps2 mode needs the PS2BrakeOn/PS2BrakeGlow assets')
        ps2['core'] = scene.texture('ps2:on', *gxi_bgra(ps2_assets['on'], opaque=True))
        ps2['glow'] = scene.texture('ps2:glow', *gxi_bgra(ps2_assets['glow']))
    deferred = []
    for d in m.physical_draws:
        case = cases.get(d.draw_index)
        if d.draw_index in suppress:
            continue
        if case is not None:
            want = 2 if (case[0] == 1 and mode != 'off') else 1
            if case[1] != want:
                continue
        g = replace.get(d.draw_index, geometry[d.draw_index])
        pos = [(-v.position[0], v.position[1], v.position[2]) for v in g.vertices]  # see mirror_camera
        col = [int.from_bytes(bytes(v.color), 'little') if v.color else 0xffffffff for v in g.vertices]
        uv = [v.uvs[0] if v.uvs else (0.0, 0.0) for v in g.vertices]
        tri = [(a, c, b) for a, b, c in g.triangles]
        texture = d.texture_tuple[0]
        alpha = bool(d.flags_0x20[0])
        lamp = 'core' if texture == 'breaklightson-tga' else 'glow' if texture == 'breaklightsonglow-tga' else None
        args = dict(texture=tex(texture))
        if d.draw_index in highlight:
            args = dict(texture=-1, colorop=OP_DIFFUSE)
            col = [highlight[d.draw_index]] * len(pos)
        elif lamp and mode == 'ps2':
            args = dict(texture=ps2[lamp], colorop=OP_TEXTURE, blend=BLEND_ADD if lamp == 'glow' else BLEND_OPAQUE,
                        zwrite=lamp == 'core')
        elif lamp:
            args.update(blend=BLEND_ALPHA if alpha else BLEND_OPAQUE, zwrite=True)
        elif alpha:
            args.update(blend=BLEND_ALPHA, zwrite=False)
        item = (pos, col, uv, tri, args)
        # Native order is kept; translucent body panes (windows) go last like the game's alpha pass.
        if alpha and not lamp:
            deferred.append(item)
        else:
            scene.draw(pos, col, uv, tri, **args)
    for pos, col, uv, tri, args in deferred:
        scene.draw(pos, col, uv, tri, **args)
    return scene


def capture(scene: Scene, camera: Camera, output: Path, exe: Path = DEFAULT_EXE) -> Path:
    """Render through Direct3D 9 and write a PNG (the BMP from the native tool is converted)."""
    from PIL import Image
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not exe.is_file():
        build_compiler(exe)
    blob = output.with_suffix('.mrlp')
    bmp = output.with_suffix('.bmp')
    blob.write_bytes(scene.encode(mirror_camera(camera)))
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    result = subprocess.run([str(exe), str(blob), str(bmp)], capture_output=True, text=True, timeout=60, creationflags=flags)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or 'mr-lamp-preview failed')
    Image.open(bmp).convert('RGB').save(output)
    bmp.unlink()
    blob.unlink()
    return output


def lamp_camera(raw: bytes, direction=(0.0, 0.0, -1.0), *, distance=None, fov=30.0, width=640, height=400, focus='lamps') -> Camera:
    """Camera on the lamp cluster (or the whole rear) looking along -direction."""
    from master_rallye.dx import parse_dx_bytes
    m = parse_dx_bytes(raw)
    pos = np.asarray(m.vertices.positions, dtype=float)
    lo, hi = pos.min(axis=0), pos.max(axis=0)
    target = np.array([(lo[0] + hi[0]) / 2, lo[1] + .45 * (hi[1] - lo[1]), lo[2]])
    span = (hi[0] - lo[0]) * (1.25 if focus == 'lamps' else 1.6)
    dist = distance or span / (2 * math.tan(math.radians(fov) / 2)) * (width and 1.0)
    return Camera.around(target, direction, dist, fov=fov, width=width, height=height)


def lens_camera(car, side=+1, direction=(0.0, 0.0, -1.0), *, margin=2.2, fov=20.0, width=480, height=360) -> Camera:
    """Close-up on one OFF lens (side +1: +X cluster, -1: -X cluster) of a carmodel.CarModel."""
    lens = car.mesh('off_glass')
    if not len(lens.triangles):
        lens = car.mesh('on_core')
    p = lens.positions
    p = p[(p[:, 0] * side) > 0] if ((p[:, 0] * side) > 0).any() else p
    lo, hi = p.min(axis=0), p.max(axis=0)
    target = (lo + hi) / 2
    span = max(hi[0] - lo[0], hi[1] - lo[1], .05) * margin
    dist = span / (2 * math.tan(math.radians(fov) / 2))
    return Camera.around(target, direction, dist, fov=fov, width=width, height=height)
