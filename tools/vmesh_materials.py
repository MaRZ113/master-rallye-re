"""Reusable GT material/texture planner -> fixed donor draws and same-size donor DXT atlases.

Inputs: classified GT faces (``vmesh_lod0.Lod0Classifier`` roles), the GT textures, the donor car.dx/complete.dx.
Output: ``MaterialPlan`` - per face the target role and the remapped DX UVs, the pool atlases (RGBA images that become
same-size DXT edits), the alpha-flag toggles of the pool draws, and a full report.

Rules (reusable for other GT vehicles):

* alpha is judged per *UV footprint of the triangle*. Structural-coverage mode preserves solid paint panels, routes masks
  to dedicated alpha-test pools, and keeps true translucent surfaces blended. Raw alpha normalization is explicitly reported;
  the legacy footprint-only mode is retained for comparison;
* flat dark opaque regions (trim, cabin shell) use the donor black trim draw unchanged;
* donor pools are donor draws present once in both car.dx and complete.dx, not reserved (crew, wheels, glass, lamps,
  trim, shared textures); blend pools prefer draws without environment mapping;
* lamps and glass keep their donor draws; their texture is the packed GT texture of that role;
* resolution is adaptive: uniform texel density per pool (texels per m2), never above the source resolution.
"""
from __future__ import annotations

import collections
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import gtmat  # noqa: E402
from master_rallye.dx import parse_dx_bytes  # noqa: E402
from master_rallye.dxt import parse_dxt, decode_rgba_pixels, PNG_ROWS_FLIP_VERTICAL  # noqa: E402

FILES = {"car": "car.dx", "complete": "complete.dx"}
FLAT_STD_MAX = 8.0          # per-channel standard deviation below which an island counts as flat
FLAT_BLACK_MAX_CHANNEL = 22.0    # a flat island only counts as 'black trim' when every channel mean is this low (navy paint is not black)
DEFAULT_MIN_POOL_PIXELS = 16 * 16


def apply_alpha_test_mask(pixels: bytearray, width: int, height: int, placements, solid_alpha: int) -> None:
    """Apply GREATER-128 cutout masks inside alpha-test island rectangles; preserve attenuated solid alpha."""
    has_mask = any(getattr(i, "alpha_test", False) for i, *_ in placements)
    if len(pixels) != width * height * 4 or not (129 if has_mask else 0) <= solid_alpha <= 255:
        raise ValueError("invalid alpha-test pool image or solid alpha")
    source_alpha = bytes(pixels[3::4])
    pixels[3::4] = bytes([solid_alpha]) * (width * height)
    for island, x, y, rw, rh in placements:
        if not getattr(island, "alpha_test", False):
            continue
        if min(x, y, rw, rh) < 0 or x + rw > width or y + rh > height:
            raise ValueError("alpha-test island rectangle outside pool")
        for py in range(y, y + rh):
            for px_x in range(x, x + rw):
                pixel = py * width + px_x
                pixels[pixel * 4 + 3] = solid_alpha if source_alpha[pixel] > 128 else 0


@dataclass
class DonorPools:
    """Candidate pool draws discovered in the donor files."""
    pools: list = field(default_factory=list)      # gtmat.Pool with .draws {"car.dx": i, "complete.dx": j}; extra attrs below
    alpha_toggles: dict = field(default_factory=dict)


def _texture_usage(model):
    use = collections.defaultdict(list)
    for d in model.physical_draws:
        use[d.texture_slots[0].value].append(d.draw_index)
    return use


def discover_pools(donor_bytes: dict, donor_dir: Path, reserved: dict, min_pixels: int = DEFAULT_MIN_POOL_PIXELS) -> list[dict]:
    """Donor draws usable as texture pools.

    ``donor_bytes``/``reserved`` are keyed by file name (``car.dx``/``complete.dx``); ``reserved`` lists draw indices that
    must keep their texture (crew, wheels, glass, lamps, trim, interior...).  A pool is a slot-0 texture name that is used by
    exactly one draw in each file, never by a reserved draw, with an existing DXT of at least ``min_pixels`` texels.
    Returns dicts with name, width, height, draws, env (all draws environment-mapped), alpha (donor flag), mask."""
    models = {f: parse_dx_bytes(b) for f, b in donor_bytes.items()}
    usage = {f: _texture_usage(m) for f, m in models.items()}
    names = set.intersection(*(set(u) for u in usage.values()))
    out = []
    for name in sorted(names):
        draws = {}
        ok = True
        for f, u in usage.items():
            if len(u[name]) != 1 or u[name][0] in reserved.get(f, ()):
                ok = False
                break
            draws[f] = u[name][0]
        if not ok:
            continue
        path = donor_dir / (name + ".dxt")
        if not path.exists():
            continue
        tex = parse_dxt(path)
        if tex.width * tex.height < min_pixels:
            continue
        infos = [models[f].physical_draws[i] for f, i in draws.items()]
        if any(d.group_label for d in infos) or any(d.tag not in (2, 7, 8) for d in infos):
            continue
        out.append({"name": name, "file": name + ".dxt", "width": tex.width, "height": tex.height, "draws": draws,
                    "env": all(d.unknown_0x24 & 4 for d in infos), "alpha": any(d.flags_0x20[0] for d in infos),
                    "alpha_test": any(d.flags_0x20[1] for d in infos), "mask": {f: infos[k].unknown_0x24 for k, f in enumerate(draws)}})
    return [p for p in out if not p["alpha_test"]]


def split_pools(candidates: list[dict], opaque_share: float = 0.5):
    """Assign candidate pools to the opaque or blend pass: opaque takes environment-mapped (shiny) draws first, blend the
    draws without environment mapping first; remaining ones alternate by capacity."""
    cands = sorted(candidates, key=lambda p: -(p["width"] * p["height"]))
    opaque = [p for p in cands if p["env"] and not p["alpha"]]
    blend = [p for p in cands if not p["env"] and not p["alpha"]]
    rest = [p for p in cands if p["alpha"] and not p["alpha_test"]]
    return opaque, blend, rest


# --------------------------------------------------------------------------- island content analysis
def island_flatness(tex: "gtmat.GtTexture", bbox) -> tuple[float, float]:
    """(max per-channel std, max per-channel mean) over the island's source region (visible texels, wrap addressing)."""
    u0, u1, v0, v1 = bbox
    x0, x1 = int(math.floor(u0 * tex.w)), max(int(math.floor(u0 * tex.w)) + 1, int(math.ceil(u1 * tex.w)))
    y0, y1 = int(math.floor((1 - v1) * tex.h)), max(int(math.floor((1 - v1) * tex.h)) + 1, int(math.ceil((1 - v0) * tex.h)))
    step_x, step_y = max(1, (x1 - x0) // 24), max(1, (y1 - y0) // 24)
    vals = [[], [], []]
    for y in range(y0, y1, step_y):
        for x in range(x0, x1, step_x):
            r, g, b, a = tex.texel(x, y)
            if a >= gtmat.CLEAR_MAX:
                vals[0].append(r)
                vals[1].append(g)
                vals[2].append(b)
    if not vals[0]:
        return 0.0, 0.0
    stds, means = [], []
    for c in vals:
        m = sum(c) / len(c)
        means.append(m)
        stds.append(math.sqrt(sum((v - m) ** 2 for v in c) / len(c)))
    return max(stds), max(means)


# --------------------------------------------------------------------------- the plan
class MaterialPlan:
    """Per-face routing + atlases.  Used by ``vmesh_geometry.build_candidate(material_plan=...)``."""

    def __init__(self, faces, textures: dict, classifier, scale: float, donor_bytes: dict, donor_dir: Path,
                 special_roles: dict, reserved: dict, glass_alpha_scale: float = 0.7, vertex_color=(255, 255, 255, 255),
                 trim_role: str = "black", min_pool_pixels: int = DEFAULT_MIN_POOL_PIXELS,
                 body_reflection_scale: float = 0.58, headlamp_reflection_scale: float = 0.72,
                 structural_coverage: bool = False, solid_trim_coverage: bool = False,
                 role_reflection_scales: dict | None = None, reflective_paint_masks: bool = False,
                 solid_black_swatches: bool = False, lamp_glass: bool = False,
                 reflection_in_helpers: bool = False, decal_priority: bool = False,
                 solid_paint_control_alpha: bool = False,
                 solid_black_lamp_caps_only: bool = False, density_weights: dict | None = None,
                 compact_decal_packing: bool = False):
        """``special_roles``: {role: {file: donor draw}} for roles that keep their donor draw (glass, head_lamp, tail_lamp);
        ``reserved``: {file: set(draw)} never used as generic pools."""
        donor_bytes = {f: b for f, b in donor_bytes.items() if f in FILES.values()}       # wheel.dx has no body draws
        for label, value in (("body_reflection_scale", body_reflection_scale),
                             ("headlamp_reflection_scale", headlamp_reflection_scale)):
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{label} must be finite and in [0, 1]")
        self.body_reflection_scale = body_reflection_scale
        self.reflection_in_helpers = reflection_in_helpers
        if reflection_in_helpers and body_reflection_scale <= 0:
            raise ValueError("helper reflection scale must be positive")
        self.scaled_helpers = set()
        self.role_reflection_scales = dict(role_reflection_scales or {})
        if any(not math.isfinite(v) or not 0 <= v <= 1 for v in self.role_reflection_scales.values()):
            raise ValueError("role reflection scales must be finite and in [0, 1]")
        self.headlamp_reflection_scale = headlamp_reflection_scale
        self.vertex_color_value = tuple(vertex_color)
        self.trim_role = trim_role
        density_weights = dict(density_weights or {})
        if any(not math.isfinite(w) or not 1 <= w <= 32 for w in density_weights.values()):
            raise ValueError('material density weights must be finite and in [1,32]')
        self.special_roles = dict(special_roles)
        self.textures = {m: gtmat.GtTexture(Path(p).read_bytes()) for m, p in textures.items()}
        self.decal_materials = set()
        if decal_priority:
            for m,t in self.textures.items():
                if t.w*t.h >= 16 and set(t.alpha) <= {0,255} and 0 in t.alpha and 255 in t.alpha:
                    visible=[max(t.rgba[i:i+3]) for i in range(0,len(t.rgba),4) if t.rgba[i+3]]
                    if visible and max(visible)>64:
                        self.decal_materials.add(m)
        self.structural_coverage = structural_coverage
        self.coverage_normalized = []
        if solid_paint_control_alpha:
            roles_by_material = collections.defaultdict(set)
            for o,m,_ in faces:
                roles_by_material[m].add(classifier._decide(o,m)[0])
            for material,tex in self.textures.items():
                evidence = paint_control_alpha_evidence(tex)
                if roles_by_material[material] == {'paint'} and evidence:
                    tex.rgba[3::4] = bytes([255]) * (tex.w*tex.h)
                    tex.alpha = bytes(tex.rgba[3::4])
                    self.coverage_normalized.append({'material':material,
                        'policy':'solid paint control-alpha palette heuristic', **evidence})
        restored_black_swatches = set()
        if solid_black_swatches:
            trim_materials = {m for o,m,_ in faces if classifier._decide(o,m)[0] == "black"}
            protected = {m for o,m,_ in faces if classifier._decide(o,m)[0] in ("glass","interior","exclude")}
            for material in sorted((trim_materials-protected) & self.textures.keys()):
                if solid_black_lamp_caps_only and not any(m==material and o in getattr(classifier,'lamp_objects',()) for o,m,_ in faces):
                    tex=self.textures[material]
                    if tex.w==tex.h==1 and tuple(tex.rgba)==(0,0,0,0):
                        self.coverage_normalized.append({'material':material,'policy':'preserve clear black non-lamp trim','nonzero_alpha_texels_promoted':0})
                    continue
                tex = self.textures[material]
                if tex.w == tex.h == 1 and tuple(tex.rgba) == (0,0,0,0):
                    tex.rgba[3] = 255
                    tex.alpha = bytes([255])
                    restored_black_swatches.add(material)
                    self.coverage_normalized.append({"material":material,"policy":"explicit solid black constant swatch", "nonzero_alpha_texels_promoted":0})
        if structural_coverage:
            # A paint shell is a solid panel, even when a nonzero source alpha encodes another
            # source-engine effect. Preserve zero coverage holes; keep true glazing/trim alpha.
            solid_roles = {"paint", "black"} if solid_trim_coverage else {"paint"}
            paint_materials = {m for o, m, _ in faces if classifier._decide(o, m)[0] in solid_roles}
            # A material shared with actual glazing is never promoted by this heuristic.
            paint_materials -= {m for o, m, _ in faces if classifier._decide(o, m)[0] == "glass"}
            for material in sorted(paint_materials & self.textures.keys()):
                tex = self.textures[material]
                changed = sum(1 for a in tex.alpha if gtmat.CLEAR_MAX <= a < 255)
                if changed:
                    tex.rgba[3::4] = bytes(255 if a >= gtmat.CLEAR_MAX else 0 for a in tex.alpha)
                    tex.alpha = bytes(tex.rgba[3::4])
                    self.coverage_normalized.append({"material": material, "nonzero_alpha_texels_promoted": changed,
                                                     "policy": "solid classified panel/trim coverage; preserve zero-alpha holes"})
        tex_dims = {m: (t.w, t.h) for m, t in self.textures.items()}
        self.lamp_glass_uv = None
        generated_glass_key = "__sdk_lamp_glass"
        if lamp_glass and getattr(classifier,"lamp_objects",()):
            if "glass" not in special_roles:
                raise ValueError("lamp glass requires an existing native glass role")
            self.textures[generated_glass_key] = gtmat.GtTexture(gtmat.png_from_rgba(1,1,bytes((110,130,150,96))))
            tex_dims[generated_glass_key] = (1,1)
        self.routes: dict[int, tuple] = {}              # face -> (role, uvs)
        self.report: dict = {"classes": collections.Counter(), "dropped_clear": [], "flat_trim": 0, "rejected": [], "pools": {}}
        items = {"opaque": [], "cutout": [], "blend": []}
        special_items = {r: [] for r in special_roles}
        if generated_glass_key in self.textures:
            special_items["glass"].append((generated_glass_key,"special",-1,[(0,0),(1,0),(0,1)],.08))
        face_class = {}
        for fi, (obj, material, tri) in enumerate(faces):
            role = classifier._decide(obj, material)[0]
            if role == "black" and material in restored_black_swatches and obj in getattr(classifier,"lamp_objects",()) and not solid_black_lamp_caps_only:
                # Constant source lens surfaces belong with the lamp helper,
                # rather than becoming nonreflective black trim.
                role = "head_lamp"
            if role == "exclude":
                continue
            tex = self.textures.get(material)
            if tex is None or any(c[3] is None for c in tri):
                continue
            uvs = [c[3] for c in tri]
            stats = gtmat.triangle_alpha_stats(tex, uvs)
            cls = gtmat.classify_alpha(stats)
            if solid_black_lamp_caps_only and material in restored_black_swatches and obj not in getattr(classifier,'lamp_objects',()):
                # The same constant may also label exterior effects on another object.
                # Restoring a lamp cap must not make those other uses opaque.
                cls = 'clear'
            self.report["classes"][(role, cls)] += 1
            area = 0.5 * math.sqrt(sum(x * x for x in _cross(_sub(tri[1][0], tri[0][0]), _sub(tri[2][0], tri[0][0])))) * scale * scale
            face_class[fi] = (role, cls)
            if cls == "clear":
                self.report["dropped_clear"].append({"face": fi, "object": obj, "material": material})
                self.routes[fi] = ("drop", None)
                continue
            if role in special_roles:
                special_items[role].append((material, "special", fi, uvs, area))
                continue
            pas = gtmat.pass_of(cls)
            # Cabin/interior masks can overlap glazing; keep those on the blend path to avoid
            # changing their existing pool density while body and bumper cutouts use alpha-test.
            if cls == "cutout" and role == "interior":
                pas = "blend"
            items[pas].append((material, pas, fi, uvs, area))
        # special pools (one texture each, donor flags fixed)
        self.pools: list = []
        self.alpha_toggles: dict = {f: {} for f in donor_bytes}
        self.alpha_test_toggles: dict = {f: {} for f in donor_bytes}
        self.env_toggles: dict = {f: {} for f in donor_bytes}
        models = {f: parse_dx_bytes(b) for f, b in donor_bytes.items()}
        for role, draws in special_roles.items():
            names = {models[f].physical_draws[i].texture_slots[0].value for f, i in draws.items()}
            if len(names) != 1:
                raise ValueError(f"special role {role}: car/complete draws use different textures {names}")
            name = names.pop()
            t = parse_dxt(donor_dir / (name + ".dxt"))
            pool = gtmat.Pool(name, t.width, t.height, "special", draws=dict(draws),
                              alpha_scale=(glass_alpha_scale if role == "glass" else
                                           headlamp_reflection_scale if role == "head_lamp" else 1.0))
            pool.role = role
            islands = gtmat.build_islands(special_items[role])
            if islands:
                leftover, rpt = gtmat.assign_to_pools(islands, [pool], tex_dims)
                if role == "head_lamp" and any(face_class.get(fi, (None, None))[1] == "cutout"
                                                for island in islands for fi in island.tris):
                    pool.alpha_test = True
                    for f, d in pool.draws.items():
                        self.alpha_toggles[f][d] = True
                        self.alpha_test_toggles[f][d] = True
                self._register(pool, rep_for(rpt, pool.name), leftover, role)
                if role == "glass" and -1 in self.routes:
                    _, spec = self.routes.pop(-1)
                    _, p, island, rect = spec
                    self.lamp_glass_uv = gtmat.remap_uv(p,island,rect,(.5,.5))
        # generic pools
        cand = discover_pools(donor_bytes, donor_dir, reserved, min_pool_pixels)
        opaque_c, blend_c, rest_c = split_pools(cand)
        islands_o = gtmat.build_islands(items["opaque"])
        # flat dark opaque islands -> donor trim draw (unchanged texture)
        keep_o = []
        for isl in islands_o:
            roles = {face_class[fi][0] for fi in isl.tris}
            isl.reflection_scale = min(self.role_reflection_scales.get(r, body_reflection_scale) for r in roles)
            std, peak = island_flatness(self.textures[isl.key[0]], isl.bbox)
            if std <= FLAT_STD_MAX and peak <= FLAT_BLACK_MAX_CHANNEL:
                for fi in isl.tris:
                    self.routes[fi] = (trim_role, [(0.5, 0.5)] * 3)
                self.report["flat_trim"] += len(isl.tris)
            else:
                isl.flat = std <= FLAT_STD_MAX          # uniform colour (e.g. tiled cabin fabric): minimal swatch, true colour
                keep_o.append(isl)
        islands_cut = gtmat.build_islands(items["cutout"])
        for isl in islands_cut:
            isl.flat = False
            isl.alpha_test = True
        islands_b = gtmat.build_islands(items["blend"])
        for island in (*keep_o,*islands_cut,*islands_b):
            island.density_weight = density_weights.get(island.key[0],1.0)
        for isl in islands_b:
            isl.flat = False
        unused_env: list = []
        reflective_masks = []
        reflective_cands = []
        decal_masks=[i for i in islands_cut if i.key[0] in self.decal_materials
                     and {face_class[f][0] for f in i.tris} == {'paint'}]
        islands_cut=[i for i in islands_cut if i not in decal_masks]
        decal_cands=[]
        if decal_masks:
            candidates=sorted(blend_c+rest_c,key=lambda c:-(c['width']*c['height']))
            if not candidates:raise ValueError('decal priority requires a non-environment atlas')
            decal_cands=candidates[:1]
            blend_c=[c for c in blend_c if c not in decal_cands]
            rest_c=[c for c in rest_c if c not in decal_cands]
        if reflective_paint_masks:
            reflective_masks = [i for i in islands_cut if {face_class[f][0] for f in i.tris} == {"paint"}]
            islands_cut = [i for i in islands_cut if i not in reflective_masks]
            if reflective_masks:
                # Keep the largest opaque atlas. Reserve the next largest existing
                # reflective pool for paint masks; its ordered helper stays intact.
                ordered_env = sorted(opaque_c,key=lambda c: -(c["width"]*c["height"]))
                if len(ordered_env)<2:
                    raise ValueError("reflective paint masks need a separate existing environment pool")
                reflective_cands = ordered_env[1:2]
                opaque_c = [c for c in opaque_c if c not in reflective_cands]
                for i in reflective_masks: i.reflection_scale = body_reflection_scale
        remaining_blend = list(blend_c + rest_c)
        if structural_coverage and islands_cut:
            if len(remaining_blend) < 2:
                raise ValueError("need independent non-environment pools for cutout and translucency")
            # Reserve one or two medium pools for masks, leaving the largest pool for true blend.
            ordered = sorted(remaining_blend, key=lambda c: c["width"] * c["height"])
            mask_cands = ordered[1:] if decal_cands else (ordered[1:-1] or ordered[:1])
            remaining_blend = [c for c in remaining_blend if c not in mask_cands]
            passes = (("opaque", keep_o), ("cutout", islands_cut), ("blend", islands_b))
        else:
            mask_cands = []
            passes = (("opaque", keep_o + islands_cut), ("blend", islands_b))
        if reflective_masks:
            passes = (*passes, ("reflective_cutout", reflective_masks))
        if decal_masks:
            passes = (*passes, ("decal_cutout",decal_masks))
        for pas, isl_list in passes:
            if pas == "opaque":
                pool_cands = opaque_c
            elif pas == "cutout":
                pool_cands = mask_cands
            elif pas == "reflective_cutout":
                pool_cands = reflective_cands
            elif pas == "decal_cutout":
                pool_cands = decal_cands
            else:
                pool_cands = remaining_blend + unused_env
            pools = []
            for c in pool_cands:
                pl = gtmat.Pool(c["name"], c["width"], c["height"], pas, draws=dict(c["draws"]))
                pl.role = f"pool:{c['name']}"
                if compact_decal_packing and pas=='decal_cutout':pl.packing='maxrects'
                pools.append(pl)
            rejected, rep = gtmat.assign_to_pools(isl_list, pools, tex_dims)
            for pl, c in zip(pools, pool_cands):
                if pl.placements:
                    if pas in ("cutout", "reflective_cutout", "decal_cutout") or pas == "opaque" and any(getattr(island, "alpha_test", False) for island, *_ in pl.placements):
                        pl.alpha_test = True
                    self._register(pl, rep_for(rep, pl.name), [], pl.role)
                    if pas == "blend":
                        for f, d in pl.draws.items():
                            self.alpha_toggles[f][d] = True
                    elif getattr(pl, "alpha_test", False):
                        for f, d in pl.draws.items():
                            self.alpha_toggles[f][d] = True
                            self.alpha_test_toggles[f][d] = True
                elif pas == "opaque":
                    unused_env.append(c)            # overflow capacity for the blend pass (environment-mapped draws)
            for isl in rejected:
                self.report["rejected"].append({"material": isl.key[0], "pass": pas, "triangles": len(isl.tris), "area_m2": round(isl.area, 3)})
                for fi in isl.tris:
                    self.routes[fi] = ("drop", None)        # never substituted by an opaque surface
        self.optional_roles = {"interior", "paint", "black", "glass", "head_lamp", "tail_lamp"} | {p.role for p in self.pools}
        self._cls = face_class
        if reflection_in_helpers:
            self.scaled_helpers={models['car.dx'].physical_draws[p.draws['car.dx']].texture_slots[1].value
                                 for p in self.pools if p.pass_ in ('opaque','reflective_cutout')}
        self._car_model=models['car.dx']
        if generated_glass_key in self.textures and self.lamp_glass_uv is None:
            raise ValueError("generated lamp glass swatch did not fit the native glass atlas")

    def reflection_scale(self, pool, island):
        if pool.pass_ in ("opaque", "reflective_cutout"):
            scale=getattr(island, "reflection_scale", self.body_reflection_scale)
        else:
            scale=self.role_reflection_scales.get(pool.role, pool.alpha_scale) if pool.pass_ == "special" and pool.role != "glass" else pool.alpha_scale
        if self.reflection_in_helpers and hasattr(self,'_car_model'):
            helper=self._car_model.physical_draws[pool.draws['car.dx']].texture_slots[1].value
            if helper in self.scaled_helpers:scale=min(1,scale/self.body_reflection_scale)
        return scale

    def _register(self, pool, rep, rejected, role):
        self.pools.append(pool)
        alpha_scale = (self.body_reflection_scale if pool.pass_ == "opaque" else pool.alpha_scale)
        self.report["pools"][pool.name] = {"role": role, "pass": pool.pass_, "size": [pool.width, pool.height],
                                           "alpha_test": bool(getattr(pool, "alpha_test", False)),
                                           "draws": pool.draws, "density_texels_per_m2": (rep or {}).get("density_texels_per_m2"),
                                           "texture_alpha_scale": alpha_scale,
                                           "islands": len(pool.placements),
                                           "materials": sorted({i.key[0] for i, *_ in pool.placements}),
                                           "triangles": sum(len(i.tris) for i, *_ in pool.placements),
                                           "degraded_to_swatch": [{"material": i.key[0], "triangles": len(i.tris), "area_m2": round(i.area, 3)}
                                                                  for i, *_ in pool.placements if i.degraded],
                                           "islands_spanning_over_one_tile": [{"material": i.key[0], "uv_span": [round(i.bbox[1] - i.bbox[0], 2), round(i.bbox[3] - i.bbox[2], 2)],
                                                                       "triangles": len(i.tris), "flat": i.flat}
                                                                      for i, *_ in pool.placements
                                                                      if i.bbox[1] - i.bbox[0] > 1.0001 or i.bbox[3] - i.bbox[2] > 1.0001]}
        for island, x, y, w, h in pool.placements:
            for fi in island.tris:
                self.routes[fi] = (pool.role, ("pool", pool, island, (x, y, w, h)))
        for isl in rejected:
            self.report["rejected"].append({"material": isl.key[0], "pass": pool.pass_, "triangles": len(isl.tris), "area_m2": round(isl.area, 3)})

    # ------------------------------------------------------------------ hooks for build_candidate
    def route(self, face_no: int, tri, role: str):
        """None = default routing; ("drop", None); or (role, [uv, uv, uv]) with remapped DX UVs."""
        r = self.routes.get(face_no)
        if r is None:
            return None
        if r[0] == "drop":
            return r
        target, spec = r
        if isinstance(spec, tuple) and spec and spec[0] == "pool":
            _, pool, island, rect = spec
            return target, [gtmat.remap_uv(pool, island, rect, c[3]) for c in tri]
        return target, spec

    def role_draws(self, profile: str) -> dict:
        f = FILES[profile]
        return {p.role: p.draws[f] for p in self.pools if p.role.startswith("pool:")}

    def vertex_color(self, role: str):
        return self.vertex_color_value

    def pool_images(self) -> dict:
        """{texture file: (width, height, RGBA bytes)} for every packed pool (special and generic)."""
        out = {}
        for p in self.pools:
            if p.placements:
                px = bytearray(gtmat.render_pool(p, self.textures))
                if p.pass_ in ("blend", "special", "cutout", "reflective_cutout", "decal_cutout"):
                    gtmat.dilate_color(px, p.width, p.height)
                if p.pass_ in ("cutout","decal_cutout"):
                    # D3D8 alpha-test reference is 128. Convert the packed mask to binary values so
                    # cutouts keep solid depth-writing surfaces instead of becoming translucent.
                    px[3::4] = bytes(255 if a > 128 else 0 for a in px[3::4])
                if p.pass_ == "reflective_cutout":
                    a = round(255 * self.reflection_scale(p,p.placements[0][0]))
                    if a <= 128:
                        raise ValueError("reflective cutout solid alpha must exceed native test reference 128")
                    px[3::4] = bytes(a if value > 128 else 0 for value in px[3::4])
                if p.pass_ == "opaque":
                    # On these donor pools, slot 1 is the audited environment helper. Keep
                    # opaque-pass geometry opaque (its blend flag remains off), while using
                    # texture alpha only to attenuate the environment-stage contribution.
                    alpha = max(0, min(255, int(255 * self.body_reflection_scale + 0.5)))
                    apply_alpha_test_mask(px, p.width, p.height, p.placements, alpha)
                    for island, x, y, w, h in p.placements:
                        a = round(255 * self.reflection_scale(p, island))
                        for yy in range(max(0, y - gtmat.GUTTER), min(p.height, y + h + gtmat.GUTTER)):
                            for xx in range(max(0, x - gtmat.GUTTER), min(p.width, x + w + gtmat.GUTTER)):
                                pos = (yy * p.width + xx) * 4 + 3
                                if not getattr(island, "alpha_test", False) or px[pos] > 128:
                                    px[pos] = a
                if p.pass_ == "special" and p.role == "tail_lamp" and p.role in self.role_reflection_scales:
                    # This donor lamp is opaque: alpha controls reflection, not coverage.
                    px[3::4] = bytes([round(255 * self.reflection_scale(p,p.placements[0][0]))]) * (p.width * p.height)
                if p.role == "head_lamp":
                    alpha = max(0, min(255, int(255 * p.alpha_scale + 0.5)))
                    px[3::4] = bytes(alpha if a > 128 else 0 for a in px[3::4])
                out[p.name + ".dxt"] = (p.width, p.height, bytes(px))
        return out


def paint_control_alpha_evidence(tex):
    """Conservative opt-in palette inference, never a general zero-alpha fill.

    Require a mixed control channel, one chromatic clear colour, and an almost
    identical dominant opaque paint colour. Binary decal masks and dark cavity
    palettes fail closed. The caller also requires exclusive paint-role usage.
    """
    counts=collections.Counter(tex.alpha)
    if not (counts[0] and counts[255] and any(0<a<255 for a in counts)):
        return None
    clear={tuple(tex.rgba[i:i+3]) for i in range(0,len(tex.rgba),4) if tex.rgba[i+3]==0}
    if len(clear)!=1:return None
    colour=next(iter(clear))
    if max(colour)<32 or max(colour)-min(colour)<24:return None
    opaque=collections.Counter(tuple(tex.rgba[i:i+3]) for i in range(0,len(tex.rgba),4) if tex.rgba[i+3]==255)
    dominant,number=opaque.most_common(1)[0]
    distance=math.dist(colour,dominant)
    if distance>8 or number<counts[255]*.5:return None
    return {'zero_alpha_texels_restored':counts[0], 'clear_rgb':list(colour),
            'dominant_opaque_rgb':list(dominant),'palette_distance':distance,
            'evidence_boundary':'palette inference; not recovered source runtime alpha semantics'}


def rep_for(rep, name):
    for r in rep:
        if r["pool"] == name:
            return r
    return None


def discover_pools_all(donor_bytes: dict, donor_dir: Path) -> list[dict]:
    """Like discover_pools without reservation/size filters (used to look up the donor texture of special roles)."""
    models = {f: parse_dx_bytes(b) for f, b in donor_bytes.items()}
    usage = {f: _texture_usage(m) for f, m in models.items()}
    out = []
    for name in sorted(set.intersection(*(set(u) for u in usage.values()))):
        draws = {f: u[name][0] for f, u in usage.items()}
        path = donor_dir / (name + ".dxt")
        if path.exists():
            t = parse_dxt(path)
            out.append({"name": name, "width": t.width, "height": t.height, "draws": draws})
    return out


def normalize_environment_helpers(plan: MaterialPlan, donor_bytes: dict, donor_dir: Path):
    """Make generic opaque pools use one donor helper appearance without changing ordered slot identities.

    Same-size texture edits resample the dominant helper. Reports every shared consumer because a donor helper may
    also be used by retained crew or wheel draws. This is local candidate texture authoring, never a retail edit.
    """
    model = parse_dx_bytes(donor_bytes["car.dx"])
    weights = collections.Counter()
    helper_pools = {}
    for p in plan.pools:
        if p.pass_ not in ("opaque", "reflective_cutout"):
            continue
        draw = model.physical_draws[p.draws["car.dx"]]
        helper = draw.texture_slots[1].value
        if not draw.unknown_0x24 & 4 or helper.casefold() == "null":
            continue
        weights[helper] += sum(i.area for i, *_ in p.placements)
        helper_pools.setdefault(helper, []).append(p.name)
    if not weights:
        return {}, {"status": "NO_REFLECTIVE_POOLS"}
    canonical = sorted(weights, key=lambda n: (-weights[n], n))[0]
    src = parse_dxt(donor_dir / (canonical + ".dxt"))
    rgba = decode_rgba_pixels(src, PNG_ROWS_FLIP_VERTICAL)
    images, rows = {}, []
    for helper in sorted(weights):
        brightness=plan.body_reflection_scale if plan.reflection_in_helpers else 1.0
        if helper == canonical and brightness == 1.0:
            continue
        target = parse_dxt(donor_dir / (helper + ".dxt"))
        out = bytearray(target.width * target.height * 4)
        for y in range(target.height):
            for x in range(target.width):
                sx, sy = min(src.width - 1, int((x + 0.5) * src.width / target.width)), min(src.height - 1, int((y + 0.5) * src.height / target.height))
                dst, pos = (y * target.width + x) * 4, (sy * src.width + sx) * 4
                out[dst:dst + 4] = rgba[pos:pos + 4]
                for channel in range(3):out[dst+channel]=round(out[dst+channel]*brightness)
        images[helper + ".dxt"] = (target.width, target.height, bytes(out))
        rows.append({"helper": helper, "source_helper": canonical, "brightness_scale":brightness,"body_pools": helper_pools[helper],
                     "shared_consumers": {f: [d.draw_index for d in parse_dx_bytes(b).physical_draws
                                              if any(s.value == helper for s in d.texture_slots)]
                                          for f, b in donor_bytes.items()}})
    return images, {"canonical_helper": canonical, "method": "dominant opaque surface area; same-size helper texture edits",
                    "edits": rows}


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


# --------------------------------------------------------------------------- offline validation
def verify_material_mapping(plan: MaterialPlan, faces, decoded: dict, tol: float = 28.0) -> dict:
    """Compare, per routed triangle, the source footprint (colour, alpha) with the footprint of its remapped UVs in the
    *final decoded DXT* of its pool.  ``decoded``: {texture file: (w, h, RGBA PNG-order bytes)}.

    Colour error is the mean absolute RGB difference of alpha-weighted footprint means; alpha error the difference of mean
    alpha (scaled by the pool's alpha_scale for glass).  Triangles that go to a pool are checked; opaque-pass triangles are
    additionally required to have opaque source footprints (no transparency was replaced by an opaque surface)."""
    rows, worst = [], []
    opaque_violations = 0
    checked = 0
    for fi, route in plan.routes.items():
        target, spec = route
        if target == "drop" or not (isinstance(spec, tuple) and spec and spec[0] == "pool"):
            continue
        _, pool, island, rect = spec
        obj, material, tri = faces[fi]
        tex = plan.textures[material]
        src_uv = [c[3] for c in tri]
        dst_uv = [gtmat.remap_uv(pool, island, rect, uv) for uv in src_uv]
        w, h, px = decoded[pool.name + ".dxt"]
        src_rgb, src_a = gtmat.footprint_mean(bytes(tex.rgba), tex.w, tex.h, src_uv)
        dst_rgb, dst_a = gtmat.footprint_mean(px, w, h, dst_uv)
        if pool.pass_ == "opaque" or pool.role == "tail_lamp":
            # Opaque native draws use alpha as reflectance, not RGB coverage.
            # A zero-reflection island must not be measured as black/invisible.
            solid_px = bytearray(px)
            solid_px[3::4] = bytes([255]) * (w * h)
            dst_rgb, _ = gtmat.footprint_mean(solid_px, w, h, dst_uv)
        err = sum(abs(a - b) for a, b in zip(src_rgb, dst_rgb)) / 3 if src_a > 8 else 0.0
        alpha_scale = plan.reflection_scale(pool, island)
        a_err = abs(src_a * alpha_scale - dst_a)
        if pool.pass_ == "opaque":
            stats = gtmat.triangle_alpha_stats(tex, src_uv)
            if gtmat.classify_alpha(stats) not in (("opaque", "cutout") if getattr(pool, "alpha_test", False) else ("opaque",)):
                opaque_violations += 1
        checked += 1
        rows.append((err, a_err))
        if err > tol or a_err > 40:
            worst.append({"face": fi, "pool": pool.name, "material": material, "colour_error": round(err, 1), "alpha_error": round(a_err, 1)})
    n = max(1, len(rows))
    return {"triangles_checked": checked, "mean_colour_error": round(sum(r[0] for r in rows) / n, 2),
            "max_colour_error": round(max((r[0] for r in rows), default=0.0), 1),
            "mean_alpha_error": round(sum(r[1] for r in rows) / n, 2),
            "triangles_over_tolerance": len(worst), "worst": sorted(worst, key=lambda x: -x["colour_error"])[:10],
            "opaque_pool_triangles_with_transparent_footprint": opaque_violations}
