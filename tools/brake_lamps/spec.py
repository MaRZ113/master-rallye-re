"""``brake_lamps.json``: per-car Brake Glow-ON description (schema ``mr-brake-lamps/1``).

Importer-friendly: every field except ``family`` and ``lamps[].lens`` has a default, so an importer can emit
just the lens faces of each lamp (or painted-on faces of a body draw) and let auto-fit do the rest.

Example::

    {
      "schema": "mr-brake-lamps/1",
      "family": "Trooper",
      "source_car_sha256": "<sha256 of the car.dx the face IDs were taken from; informative>",
      "lamps": [
        {
          "id": "left",
          "body": "ANY",                       # ANY | PC | PS2 (body-scoped sets, MR-ADDON-LAMPS 3)
          "lens": {"draw": "blight", "faces": ["9f0c...", ...]},   # stable face IDs (carmodel.face_ids)
          "source": {"kind": "from_glass"},     # blazer | ps2 | custom | from_glass
          "transform": {"offset": [0,0,0], "rotation": [0,0,0], "scale": [1,1,1], "normal_offset_mm": 0},
          "fit": {"mode": "project", "offset_mm": 1.5, "max_edge_m": 0.02},
          "halo": {"size": 1.0, "color": [255,255,255], "brightness": 1.0},
          "depth": {"halo": "native"},
          "mirror": null                        # or {"of": "right"}: mirrored copy of another lamp across X=0
        }
      ]
    }

``lens.draw`` is ``"blight"`` (the OFF case of the existing brake state group), ``"any"`` (faces of any draw shown
with the brake released, e.g. painted lamp art around a small OFF lens) or an integer draw index. When the model
has a blight group, every lamp is an overlay in its ON case. Without one (painted-on lamps of imported cars), the
faces of one body draw are extracted into a new brake group (only for models that have no state groups yet). ``source``:

* ``blazer``      - retail ChevyBlazer ON core/halo of ``side`` (``left``/``right``, default by lens X).
* ``ps2``         - original PS2 meshes: ``{"asset": <.ps2vehicle path>, "core": <mesh path>, "glow": <mesh path>}``.
* ``custom``      - inline meshes ``{"core": {"positions","uvs","triangles"}, "glow": {...}}`` (model space).
* ``from_glass``  - core = the selected lens faces, halo = a ring grown from the lens outline (the Blazer construction).

``fit.mode``: ``plane`` (best-fit lens plane, in front of every lens vertex), ``project`` (each vertex cast along the lens
normal onto the lens, halo onto lens or body, whichever is outermost), ``shrinkwrap`` (closest point on lens/body).
``fit.max_edge_m`` (core tessellation, 2 cm) and ``fit.halo_max_edge_m`` (halo, 3 cm: every lamp draw is hashed
by the renderer on first sight, so the halo stays coarse). ``fit.offset_mm`` (0.5..5, default 1.5) lifts the layer off the surface along the local normal; auto-fit raises it in
0.5 mm steps up to ``fit.max_offset_mm`` (default 3) until no sample is buried.

``halo.size`` scales the ring width (1.0 = Blazer proportion, 0.45 x lens extent) or a donor halo about the lens centre.
``halo.color``/``brightness`` tint the per-car PC halo texture (BrakeGlow=0). BrakeGlow=1 uses the renderer's global
PS2 halo asset, which this module does not change. ``depth.halo``: ``native`` only (the renderer keeps native
ZENABLE/ZFUNC; a correctly fitted layer needs no depth override).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

SCHEMA = 'mr-brake-lamps/1'
SOURCES = ('blazer', 'ps2', 'custom', 'from_glass')
FITS = ('plane', 'project', 'shrinkwrap', 'none')
BODIES = ('ANY', 'PC', 'PS2')
DEPTH = ('native',)

LAMP_DEFAULTS = {
    'body': 'ANY',
    'source': {'kind': 'from_glass'},
    'transform': {'offset': [0.0, 0.0, 0.0], 'rotation': [0.0, 0.0, 0.0], 'scale': [1.0, 1.0, 1.0], 'normal_offset_mm': 0.0},
    'fit': {'mode': 'project', 'offset_mm': 1.5, 'max_offset_mm': 3.0, 'max_edge_m': 0.02, 'halo_max_edge_m': 0.03},
    'halo': {'size': 1.0, 'color': [255, 255, 255], 'brightness': 1.0},
    'depth': {'halo': 'native'},
    'mirror': None,
}


class SpecError(ValueError):
    pass


def _merge(default, value):
    if isinstance(default, dict) and isinstance(value, dict):
        out = copy.deepcopy(default)
        for k, v in value.items():
            out[k] = _merge(default.get(k), v) if k in default else v
        return out
    return copy.deepcopy(value) if value is not None or default is None else copy.deepcopy(default)


def _vec(value, n, what):
    if not isinstance(value, (list, tuple)) or len(value) != n or not all(isinstance(x, (int, float)) for x in value):
        raise SpecError(f'{what} must be {n} numbers')
    return [float(x) for x in value]


def normalise(data: dict) -> dict:
    """Validate and fill defaults. Returns a new dict; raises SpecError with the offending path."""
    if not isinstance(data, dict):
        raise SpecError('brake_lamps.json must be an object')
    if data.get('schema', SCHEMA) != SCHEMA:
        raise SpecError(f'unsupported schema {data.get("schema")!r}')
    family = data.get('family')
    if not isinstance(family, str) or not family or any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-' for c in family):
        raise SpecError('family must be a registry-safe name')
    lamps = data.get('lamps')
    if not isinstance(lamps, list) or not lamps:
        raise SpecError('lamps must be a non-empty list')
    out = {'schema': SCHEMA, 'family': family, 'source_car_sha256': data.get('source_car_sha256'), 'lamps': []}
    if 'notes' in data:
        out['notes'] = data['notes']
    ids = set()
    for n, raw in enumerate(lamps):
        where = f'lamps[{n}]'
        if not isinstance(raw, dict):
            raise SpecError(f'{where} must be an object')
        lamp = {k: _merge(v, raw.get(k)) if k in raw else copy.deepcopy(v) for k, v in LAMP_DEFAULTS.items()}
        lamp['id'] = raw.get('id', f'lamp{n}')
        if not isinstance(lamp['id'], str) or lamp['id'] in ids:
            raise SpecError(f'{where}.id must be a unique string')
        ids.add(lamp['id'])
        if lamp['body'] not in BODIES:
            raise SpecError(f'{where}.body must be one of {BODIES}')
        mirror = raw.get('mirror')
        if mirror is not None:
            if not isinstance(mirror, dict) or not isinstance(mirror.get('of'), str):
                raise SpecError(f'{where}.mirror must be {{"of": <lamp id>}}')
            lamp['mirror'] = {'of': mirror['of']}
        lens = raw.get('lens')
        if mirror is None:
            if not isinstance(lens, dict) or not isinstance(lens.get('faces'), list) or not lens['faces']:
                raise SpecError(f'{where}.lens.faces must list stable face IDs')
            draw = lens.get('draw', 'blight')
            if draw not in ('blight', 'any') and not (isinstance(draw, int) and draw >= 0):
                raise SpecError(f'{where}.lens.draw must be "blight", "any" or a draw index')
            if not all(isinstance(f, str) and len(f) == 16 and all(c in '0123456789abcdef' for c in f) for f in lens['faces']):
                raise SpecError(f'{where}.lens.faces entries must be 16-hex face IDs')
            lamp['lens'] = {'draw': draw, 'faces': list(dict.fromkeys(lens['faces']))}
        elif lens is not None:
            raise SpecError(f'{where}: a mirrored lamp takes its lens from the mirrored lamp')
        src = lamp['source']
        if src.get('kind') not in SOURCES:
            raise SpecError(f'{where}.source.kind must be one of {SOURCES}')
        if src['kind'] == 'blazer' and src.get('side') not in (None, 'left', 'right'):
            raise SpecError(f'{where}.source.side must be left or right')
        if src['kind'] == 'ps2' and not all(isinstance(src.get(k), str) for k in ('asset', 'core', 'glow')):
            raise SpecError(f'{where}.source needs asset/core/glow for ps2')
        if src['kind'] == 'custom':
            for layer in ('core', 'glow'):
                mesh = src.get(layer)
                if not isinstance(mesh, dict) or not all(isinstance(mesh.get(k), list) for k in ('positions', 'uvs', 'triangles')):
                    raise SpecError(f'{where}.source.{layer} needs positions/uvs/triangles')
                if len(mesh['positions']) != len(mesh['uvs']) or not mesh['triangles']:
                    raise SpecError(f'{where}.source.{layer}: positions/uvs mismatch or no triangles')
        t = lamp['transform']
        t['offset'] = _vec(t['offset'], 3, f'{where}.transform.offset')
        t['rotation'] = _vec(t['rotation'], 3, f'{where}.transform.rotation')
        t['scale'] = _vec(t['scale'], 3, f'{where}.transform.scale')
        if not all(.05 <= s <= 4 for s in t['scale']):
            raise SpecError(f'{where}.transform.scale outside 0.05..4')
        if not -20 <= float(t['normal_offset_mm']) <= 20:
            raise SpecError(f'{where}.transform.normal_offset_mm outside -20..20')
        f = lamp['fit']
        if f['mode'] not in FITS:
            raise SpecError(f'{where}.fit.mode must be one of {FITS}')
        if not .5 <= float(f['offset_mm']) <= 5 or not float(f['offset_mm']) <= float(f['max_offset_mm']) <= 5:
            raise SpecError(f'{where}.fit.offset_mm must be 0.5..5 and <= max_offset_mm <= 5')
        if not .002 <= float(f['max_edge_m']) <= 1 or not .005 <= float(f['halo_max_edge_m']) <= 1:
            raise SpecError(f'{where}.fit.max_edge_m / halo_max_edge_m outside 0.002..1 / 0.005..1')
        h = lamp['halo']
        if not .1 <= float(h['size']) <= 4:
            raise SpecError(f'{where}.halo.size outside 0.1..4')
        h['color'] = [int(c) for c in _vec(h['color'], 3, f'{where}.halo.color')]
        if not all(0 <= c <= 255 for c in h['color']) or not 0 <= float(h['brightness']) <= 4:
            raise SpecError(f'{where}.halo colour 0..255 / brightness 0..4')
        if lamp['depth'].get('halo') not in DEPTH:
            raise SpecError(f'{where}.depth.halo: only "native" is supported (renderer keeps native depth state)')
        if 'notes' in raw:
            lamp['notes'] = str(raw['notes'])
        out['lamps'].append(lamp)
    by_id = {l['id']: l for l in out['lamps']}
    for lamp in out['lamps']:
        if lamp['mirror']:
            target = by_id.get(lamp['mirror']['of'])
            if target is None or target['mirror'] is not None or target is lamp:
                raise SpecError(f'lamp {lamp["id"]}: mirror target must be another non-mirrored lamp')
    return out


def load(path) -> dict:
    return normalise(json.loads(Path(path).read_text(encoding='utf-8')))


def dump(spec: dict, path) -> None:
    Path(path).write_text(json.dumps(normalise(spec), indent=1) + '\n', encoding='utf-8')
