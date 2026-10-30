"""Hash-bound Evo2 color consumer replay and immutable source-scene variants.

The replay uses owner-local original x86 instructions in an isolated CPU only.
It is not an original game process, GPU emulation, or a TIFF alpha inference.
No original executable bytes are distributed with this implementation.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import math
import struct
from .. import universal_vehicle_scene as u
from . import evo2

SCHEMA = 'evo2-source-color/1'
MAX_EDGE = 512
START = 0x4276f8
PALETTE_END = 0x427c30
END = 0x427d23
TIFF_SHA256 = 'd3c777e4d96daea62da5bb7e015b58fa92349301e57ee0ff171ae48c6cfeb854'


def validate_inputs(samples: bytes, palette: bytes, size: int, color):
    if isinstance(size, bool) or not isinstance(size, int) or not 1 <= size <= MAX_EDGE:
        raise ValueError('Evo2 color dimensions/budget')
    if len(samples) != size * size * 2 or len(palette) != 1536:
        raise ValueError('Evo2 dual-plane/palette size mismatch')
    if not isinstance(color, (tuple, list)) or len(color) != 3:
        raise ValueError('Evo2 color record must contain HSV delta triplet')
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in color):
        raise ValueError('Evo2 nonfinite color record')
    if not 0 <= color[0] <= 360 or not all(-100 <= v <= 100 for v in color[1:]):
        raise ValueError('Evo2 color parameter range')
    # The qualified 4Runner's 16-bit ColorMap uses replicated byte values.
    # Refuse a different reduction rule until that loader branch is qualified.
    values = struct.unpack('<768H', palette)
    if any(v % 257 for v in values):
        raise ValueError('unqualified non-replicated Evo2 palette samples')
    return [tuple(values[k * 256 + i] // 257 for k in range(3)) for i in range(256)]


def composite(samples: bytes, original: bytes, adjusted: bytes) -> bytes:
    """Native pre-gloss packed BGRA; high byte retained as auxiliary, not opacity.

    00427c76/00428112: <=128 retains original RGB, 255 selects adjusted;
    intermediate samples mix with float32 weight (sample-128)/127. Original
    0060fb82 truncates toward zero; nonnegative mixed RGB therefore truncates.
    """
    if len(samples) > MAX_EDGE * MAX_EDGE * 2 or len(samples) % 2 or len(original) != 1024 or len(adjusted) != 1024:
        raise ValueError('Evo2 composite byte budget/palette size')
    out = bytearray(len(samples) * 2)
    for pixel in range(len(samples) // 2):
        index, sample = samples[pixel * 2:pixel * 2 + 2]
        a = original[index * 4:index * 4 + 3]
        b = adjusted[index * 4:index * 4 + 3]
        if sample <= 128: rgb = a
        elif sample == 255: rgb = b
        else:
            weight = struct.unpack('<f', struct.pack('<f', (sample - 128) / 127))[0]
            rgb = bytes(int(x * (1 - weight) + y * weight) for x, y in zip(a, b))
        out[pixel * 4:pixel * 4 + 4] = bytes((*rgb, sample))
    return bytes(out)


def reconstruct(executable: bytes, samples: bytes, palette: bytes, size: int, color) -> dict:
    """Run only the verified color consumer, excluding I/O, allocation and gloss.

    Entry follows loader-produced palette/plane binding. END precedes the
    optional BUMP/gloss branch. Original RGB<->HSV, palette selection, x87/CRT
    rounding and per-pixel mix instructions execute without Python substitutes.
    """
    colors = validate_inputs(samples, palette, size, color)
    if u.sha(executable) != evo2.EXE_SHA256:
        raise ValueError('unqualified Evo2 color executable SHA256')
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP
    emulator = Uc(UC_ARCH_X86, UC_MODE_32)
    emulator.mem_map(0x400000, 0xa00000)
    pe = struct.unpack_from('<I', executable, 0x3c)[0]
    count = struct.unpack_from('<H', executable, pe + 6)[0]
    optional = struct.unpack_from('<H', executable, pe + 20)[0]
    for index in range(count):
        at = pe + 24 + optional + index * 40
        _, rva, length, offset = struct.unpack_from('<4I', executable, at + 8)
        # Watcom .bss reports an allocation length with raw offset zero.
        if offset: emulator.mem_write(0x400000 + rva, executable[offset:offset + length])
    emulator.mem_map(0x1000000, 0x800000)
    frame = 0x1010000
    for offset, value in ((0x1180, 0x1100000), (0x1184, 0x1200000), (0x1100, 0x1300000), (0x11b8, size)):
        emulator.mem_write(frame + offset, struct.pack('<I', value))
    original = b''.join(struct.pack('<I', r << 16 | g << 8 | b) for r, g, b in colors)
    emulator.mem_write(0x1100000, samples[::2])
    emulator.mem_write(0x1200000, samples[1::2])
    emulator.mem_write(0x81f164, original)
    emulator.mem_write(0x672048, struct.pack('<I', 24))
    # Reset x87, as on game initialization. Normalized parameters are the
    # selected TRK floats divided by original float64 constants 360,100,100.
    emulator.mem_write(0x1000000, bytes.fromhex('dbe3'))
    emulator.emu_start(0x1000000, 0x1000002, count=1)
    floats = [struct.unpack('<f', struct.pack('<f', v))[0] for v in color]
    emulator.mem_write(frame + 0x11ac, struct.pack('<3f', floats[0] / 360, floats[1] / 100, floats[2] / 100))
    emulator.reg_write(UC_X86_REG_ESP, frame)
    emulator.emu_start(START, PALETTE_END, timeout=10_000_000, count=10_000_000)
    if emulator.reg_read(UC_X86_REG_EIP) != PALETTE_END:
        raise ValueError('Evo2 palette instruction/time budget')
    adjusted = bytes(emulator.mem_read(0x7e6da8, 1024))
    dominant_hsv = struct.unpack('<3f', bytes(emulator.mem_read(0x7e6d54, 12)))
    emulator.emu_start(PALETTE_END, END, timeout=10_000_000, count=30_000_000)
    if emulator.reg_read(UC_X86_REG_EIP) != END:
        raise ValueError('Evo2 composition instruction/time budget')
    packed = bytes(emulator.mem_read(0x1300000, size * size * 4))
    if packed[3::4] != samples[1::2]: raise ValueError('Evo2 auxiliary plane conservation failed')
    derived = composite(samples, original, adjusted)
    if derived != packed: raise ValueError('Evo2 native/Python arithmetic mismatch')
    rgba = bytearray(len(packed))
    for i in range(size * size):
        b, g, r, auxiliary = packed[i * 4:i * 4 + 4]
        rgba[i * 4:i * 4 + 4] = bytes((r, g, b, 255))
    return {'rgba': bytes(rgba), 'packed_bgra': packed, 'adjusted_palette': adjusted,
            'evidence': {'schema': SCHEMA, 'executable_sha256': u.sha(executable),
                'entry': hex(START), 'packed_format': 'original canonical24bit RGB branch with separately preserved high byte', 'palette_end': hex(PALETTE_END), 'exit_before_gloss': hex(END),
                'source_samples_sha256': u.sha(samples), 'source_palette_sha256': u.sha(palette),
                'hsv_delta_original': list(color), 'dominant_source_hsv': list(dominant_hsv),
                'native_composite_matches': True, 'rgba_sha256': u.sha(bytes(rgba)),
                'packed_bgra_sha256': u.sha(packed), 'high_byte_matches_second_sample': True,
                'boundary': 'isolated original CPU pre-gloss consumer; no GPU/runtime opacity equivalence',
                'preview_alpha_policy': 'opaque; original high byte kept separately, never inferred as opacity'}}


def derive_scene(source: Path, output: Path, executable: bytes, color_index: int) -> dict:
    source = Path(source)
    scene = u.load_scene(source)
    if scene['metadata'].get('source_adapter') != 'evo2-4runner/1':
        raise ValueError('qualified Evo2 source scene required')
    resources = {r['member'].casefold(): r['sha256'] for r in scene['source']['resources']}
    if resources.get(evo2.CATALOG.casefold()) != evo2.CATALOG_SHA256 or resources.get(evo2.BODY.casefold()) != evo2.BODY_SHA256 or scene['source']['executable']['sha256'] != evo2.EXE_SHA256:
        raise ValueError('Evo2 color source provenance mismatch')
    records = scene['source']['catalog_original']['color_records']
    if len(records) != 9: raise ValueError('unqualified Evo2 source color catalog')
    catalog=next(r for r in scene['source']['resources']if r['member'].casefold()==evo2.CATALOG.casefold())
    catalog_bytes=u.read_bounded(source.parent/catalog['snapshot_path'],1024*1024)
    if u.sha(catalog_bytes)!=evo2.CATALOG_SHA256 or evo2.parse_trk(catalog_bytes)['color_records']!=records:
        raise ValueError('Evo2 color rows disagree with original TRK')
    if isinstance(color_index, bool) or not isinstance(color_index, int) or not 0 <= color_index < len(records):
        raise ValueError('Evo2 source color index')
    raw_record = records[color_index]
    color = [float(v) for v in raw_record['value'].split(',')[:3]]
    textures = [t for t in scene['textures'] if t['source']['member'].casefold() == 'art/4runnersr5.tif']
    if len(textures) != 1: raise ValueError('ambiguous Evo2 body color texture')
    texture = textures[0]; channels = texture['source_channels']; root = source.parent
    if channels['photometric'] != 3 or channels['samples_per_pixel'] != 2 or channels['extra_samples'] != [0] or texture['width'] != texture['height']:
        raise ValueError('unqualified Evo2 TIFF layout')
    samples=u.read_bounded(root / channels['raw_samples_path'], 1024 * 1024)
    palette=u.read_bounded(root / channels['palette_path'], 1536)
    original_tiff=u.read_bounded(root/texture['source']['snapshot_path'],4*1024*1024)
    if texture['source']['sha256']!=TIFF_SHA256 or u.sha(original_tiff)!=TIFF_SHA256:raise ValueError('Original Evo2 TIFF provenance mismatch')
    _,_,decoded_samples,decoded_palette=evo2.decode_tiff(original_tiff)
    if samples!=decoded_samples or palette!=decoded_palette:raise ValueError('Evo2 planes/palette disagree with original TIFF bytes')
    result = reconstruct(executable,samples,palette,texture['width'],color)
    original_scene = deepcopy(scene)
    manifest = u.load_json(u.read_bounded(root / 'manifest.json', 2 * 1024 * 1024))
    assets = {name: u.read_bounded(root / name, u.MAX_OUTPUT_BYTES) for name in manifest['files'] if name != 'scene.json'}
    path = f'derived/color-{color_index:02d}.rgba'
    assets[path] = result['rgba']
    assets[f'derived/color-{color_index:02d}.packed-bgra'] = result['packed_bgra']
    assets[f'derived/color-{color_index:02d}.palette-bgra'] = result['adjusted_palette']
    evidence = {**result['evidence'], 'source_scene_sha256': u.sha(source.read_bytes()),
                'source_color_index': color_index, 'source_color_record': raw_record,
                'base_rgba_path': texture['rgba_path'], 'base_rgba_sha256': texture['rgba_sha256']}
    assets['derived/color-evidence.json'] = u.canonical(evidence)
    texture['rgba_path'] = path; texture['rgba_sha256'] = u.sha(result['rgba'])
    texture['derived_color'] = evidence
    scene['metadata']['source_color_experiment'] = evidence
    scene['metadata']['display_name'] += f' — original color {color_index + 1}'
    scene['unknown_semantics'].append({'id': 'evo2-color-gpu-boundary', 'status': 'WARN',
        'meaning': 'Native pre-gloss RGB qualified. Packed high byte and optional bump/gloss retained; GPU alpha/reflections and runtime parity remain unknown.'})
    for field in ('meshes', 'nodes', 'materials', 'source', 'coordinate_system'):
        if scene[field] != original_scene[field]: raise ValueError('Evo2 color derivation changed source/geometry')
    return u.save_scene(scene, Path(output), assets, protected_roots=[source.parent,Path(scene['source']['root']),*map(Path,scene['source'].get('protected_roots',[]))])
