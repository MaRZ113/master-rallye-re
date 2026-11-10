"""Material vocabulary of the Retail course pipeline.

Every value below is evidence-backed:

* surface types are the ten ``Surface_Type_<n>`` rows of ``DataGame/Surface.xml``
  (friction/restitution/track texture/solid per type). The physics finds a
  material's surface by the first ``$surfacetype(...)`` token of its name, which
  the cooker stores per triangle in the tag-1400 land database;
* shaders are the ``$shader(...)`` tokens used by Retail sources;
* the draw-record fields are the Retail cooker contract recovered from the
  game-cooked ``invspaingx.dx`` (cooked by Retail ``MRallye.exe`` from our GXM)
  and a census of Retail course records against their TXT material names.

``encode_record_fields`` returns those fields; :func:`native_name` builds a name
string with the same token grammar as the Retail sources.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

SURFACES = ("tarmac", "harddirt", "grass", "gravel", "mud", "metal", "rubber", "rock", "hay", "water")
SURFACE_LABELS = {
    "tarmac": "Tarmac", "harddirt": "Hard dirt", "grass": "Grass", "gravel": "Gravel", "mud": "Mud",
    "metal": "Metal", "rubber": "Rubber", "rock": "Rock", "hay": "Hay", "water": "Water (not solid)",
}
# DataGame/Surface.xml (Retail): quality, restitution, friction, track texture, solid.
SURFACE_TABLE = {
    "tarmac": (1.0, 0.0, 1.0, "misc\\tracks\\tarmac", True),
    "harddirt": (1.0, 0.0, 1.0, "misc\\tracks\\harddirt", True),
    "grass": (1.0, 0.0, 1.0, "misc\\tracks\\grass", True),
    "gravel": (1.0, 0.0, 1.0, "misc\\tracks\\gravel", True),
    "mud": (1.0, 0.0, 1.0, "misc\\tracks\\mud", True),
    "metal": (1.0, 0.5, 1.0, "misc\\tracks\\metal", True),
    "rubber": (1.0, 0.0, 1.0, "misc\\tracks\\rubber", True),
    "rock": (1.0, 0.0, 1.0, "misc\\tracks\\rock", True),
    "hay": (1.0, 0.2, 1.0, "misc\\tracks\\hay", True),
    "water": (1.0, 0.0, 1.0, "misc\\tracks\\water", False),
}

SHADERS = ("ground", "object", "sign", "metal", "tree", "water", "puddle", "waterall")
SHADER_LABELS = {
    "ground": "Ground (terrain, noise detail pass)",
    "object": "Object",
    "sign": "Sign / banner",
    "metal": "Metal (environment layer)",
    "tree": "Vegetation (alpha test)",
    "water": "Water surface",
    "puddle": "Puddle",
    "waterall": "Waterfall (scrolling)",
}
ALPHA_MODES = ("opaque", "blend", "cutout")
CLAMP_MODES = ("", "u", "v", "uv")
# Draw-record address word (Retail census): wrap both = 1, clamp u = 2, clamp v = 4, clamp both = 0.
ADDRESS_WORD = {"": 1, "u": 2, "v": 4, "uv": 0}
NOISE_UV_SCALE = 1.0 / 37.0      # cooked noise pass: uv1 = (x, z) / 37 + 0.5 (+ integer shifts)
NOISE_TEXTURE = "noise-tga"
METAL_DEFAULT_SECONDARY = "aluminium-tga"


@dataclass(frozen=True)
class RecordFields:
    address: int        # core word 0x14
    effect: int         # core word 0x18: 0 normal, 1 water/puddle, 2 scrolling
    mip: float          # core float 0x1C ($mip value)
    flags: bytes        # core bytes 0x20: blend, alpha test, vertex lighting, 1
    slot_mask: int      # core word 0x24: bit0/2/3 texture slots 0/1/2, bit1 vertex lighting, bit4 water
    sort_class: int     # cooker draw order: 0 opaque, 1 water, 2 blend, 3 alpha test


def encode_record_fields(*, shader: str, alpha: str, clamp: str, mip: float, has_secondary: bool,
                         has_noise: bool, has_base: bool, scroll: bool) -> RecordFields:
    if shader not in SHADERS:
        raise ValueError(f"unknown shader {shader!r}")
    if alpha not in ALPHA_MODES or clamp not in CLAMP_MODES:
        raise ValueError(f"unsupported alpha {alpha!r} or clamp {clamp!r}")
    water = shader in ("water", "puddle")
    effect = 1 if water else 2 if (scroll or shader == "waterall") else 0
    blend = alpha in ("blend", "cutout")
    flags = bytes((1 if blend else 0, 1 if alpha == "cutout" else 0, 1, 1))
    mask = 2 | (1 if has_base else 0) | (4 if has_secondary else 0) | (8 if has_noise else 0) | (16 if water else 0)
    sort = 3 if alpha == "cutout" else 2 if alpha == "blend" else 1 if water else 0
    return RecordFields(ADDRESS_WORD[clamp], effect, float(mip), flags, mask, sort)


def _fmt_mip(value: float) -> str:
    return f"{value:.1f}" if abs(value * 10 - round(value * 10)) < 1e-6 else f"{value:g}"


def native_name(*, label: str, shader: str, surface: str | None, alpha: str, clamp: str, mip: float,
                scroll: str | None, noise: bool) -> str:
    """Material name in Retail token grammar, e.g. ``Road $surfacetype(tarmac) $shader(ground) $mip(1.0)``."""
    parts = []
    if label:
        parts.append(label.replace("$", "").strip())
    if surface:
        if surface not in SURFACES:
            raise ValueError(f"unknown surface {surface!r}")
        parts.append(f"$surfacetype({surface})")
    if clamp:
        parts.append(f"$clamp({clamp})")
    if alpha == "cutout":
        parts.append("$alphatest()")
    parts.append(f"$shader({shader})")
    if scroll:
        parts.append(f"$scroll({scroll})")
    parts.append(f"$mip({_fmt_mip(mip)})")
    name = " ".join(parts)
    if noise:
        name += "Noise Pass"   # Retail multi-material suffix of the noise layer
    return name


_TOKEN = re.compile(r"\$(\w+)\(([^)]*)\)")


def parse_native_name(name: str) -> dict:
    """Structured fields of a Retail material name. Unknown tokens are reported, not dropped."""
    tokens = _TOKEN.findall(name)
    out = {"label": _TOKEN.sub("", name).replace("Noise Pass", "").strip(), "surface": None, "shader": "object",
           "alpha": "opaque", "clamp": "", "mip": 1.0, "scroll": None, "noise": "Noise Pass" in name,
           "unknown_tokens": []}
    for key, value in tokens:
        if key == "surfacetype" and out["surface"] is None:
            out["surface"] = value if value in SURFACES else None
            if value not in SURFACES:
                out["unknown_tokens"].append(f"$surfacetype({value})")
        elif key == "shader":
            out["shader"] = value if value in SHADERS else "object"
            if value not in SHADERS:
                out["unknown_tokens"].append(f"$shader({value})")
        elif key == "alphatest":
            out["alpha"] = "cutout"
        elif key == "clamp":
            out["clamp"] = value if value in CLAMP_MODES else ""
        elif key == "mip":
            try:
                out["mip"] = float(value)
            except ValueError:
                out["unknown_tokens"].append(f"$mip({value})")
        elif key == "scroll":
            out["scroll"] = value
        elif key not in ("grnd", "surfacetype"):
            out["unknown_tokens"].append(f"${key}({value})")
    return out


def surface_of_name(name: str) -> str | None:
    match = re.search(r"\$surfacetype\((\w+)\)", name)
    return match.group(1) if match and match.group(1) in SURFACES else None


# Presets offered by the Materials editor ("New Material" templates).
PRESETS = {
    "Tarmac road": dict(shader="ground", surface="tarmac", noise=True),
    "Gravel road": dict(shader="ground", surface="gravel", noise=True),
    "Hard dirt": dict(shader="ground", surface="harddirt", noise=True),
    "Grass": dict(shader="ground", surface="grass", noise=True),
    "Mud": dict(shader="ground", surface="mud", noise=True),
    "Rock face": dict(shader="ground", surface="rock", noise=True),
    "Building / object": dict(shader="object", surface=None, noise=False),
    "Metal object": dict(shader="metal", surface="metal", noise=False),
    "Sign / banner": dict(shader="sign", surface=None, noise=False),
    "Tree / bush (alpha)": dict(shader="tree", surface=None, noise=False, alpha="cutout"),
    "Water": dict(shader="water", surface="water", noise=False),
}
