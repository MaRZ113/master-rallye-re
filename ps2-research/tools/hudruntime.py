"""PS2-UI2 data-only RaceLine reader and recovered minimap math.

No live process access, asset writer, screenshot fitting, or GS emulation.
Geometry outputs are restricted to the ignored ps2-research/data directory.
Arithmetic follows recovered scalar equations in Python precision; it does
not claim bit-exact R5900 floating-point/rasterization behavior.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MAX_POINTS = 65536
MAX_XML_SIZE = 16 * 1024 * 1024
STRIDE = 0x50
POSITION_OFFSET = 0x40
ELF_SHA = 'b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2'
SCALE = struct.unpack('<f', bytes.fromhex('cdcccc3e'))[0]


class FormatError(ValueError):
    pass


def finite(values, size):
    if len(values) != size or not all(math.isfinite(x) for x in values):
        raise FormatError('Required geometry must have finite components')
    return tuple(float(x) for x in values)


def f32(x):
    try:
        result = struct.unpack('<f', struct.pack('<f', float(x)))[0]
    except (ValueError, OverflowError, struct.error) as exc:
        raise FormatError('Invalid float32 geometry') from exc
    if not math.isfinite(result):
        raise FormatError('Non-finite float32 geometry')
    return result


def read_xml_route(data):
    """Use document order, as 1ff6a0 does; require canonical numbered records.

    Marker No is validation, not a sort key. Other scene lists are untouched.
    Only Marker Pos is exported; the complete orientation basis is not rebuilt.
    """
    if not 0 < len(data) <= MAX_XML_SIZE or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise FormatError('Unsupported XML size or declarations')
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise FormatError('Malformed route XML') from exc
    lists = root.findall("./MarkerLists/List[@Name='RaceLine']")
    if len(lists) != 1:
        raise FormatError('Expected one MarkerLists/RaceLine')
    markers = list(lists[0])
    if not 2 <= len(markers) <= MAX_POINTS or any(m.tag != 'Marker' for m in markers):
        raise FormatError('Impossible route count or malformed marker list')
    points = []
    for index, marker in enumerate(markers):
        if marker.get('No') != str(index):
            raise FormatError('Non-canonical document-order Marker No')
        pos = marker.findall("Value[@Name='Marker Pos']")
        if len(pos) != 1 or pos[0].get('Type') != 'Vector3':
            raise FormatError('Missing or ambiguous Marker Pos')
        value = pos[0].get('Value', '').split()
        if len(value) != 3:
            raise FormatError('Marker Pos must have three components')
        points.append(tuple(f32(x) for x in value))
    return points


def read_memory_route(data, offset, count):
    """Read an explicitly selected contiguous record array, not scan a dump."""
    if type(offset) is not int or offset < 0 or offset % 4:
        raise FormatError('Invalid route array offset/alignment')
    if type(count) is not int or not 2 <= count <= MAX_POINTS:
        raise FormatError('Impossible route count')
    if offset > len(data) or count * STRIDE > len(data) - offset:
        raise FormatError('Route array outside dump')
    return [finite(struct.unpack_from('<3f', data, offset + i * STRIDE + POSITION_OFFSET), 3)
            for i in range(count)]


def read_memory_vector(data, header_offset, base_address):
    """Resolve the recovered begin/end/capacity header within one memory image."""
    if (type(header_offset) is not int or header_offset < 0 or header_offset % 4
            or header_offset + 12 > len(data) or type(base_address) is not int
            or not 0 <= base_address <= 0xffffffff or base_address + len(data) > 0x100000000):
        raise FormatError('Invalid vector header or dump base')
    begin, end, capacity = struct.unpack_from('<3I', data, header_offset)
    if not base_address <= begin <= end <= capacity <= base_address + len(data):
        raise FormatError('Vector pointers outside dump or reversed')
    if (end - begin) % STRIDE or (capacity - begin) % STRIDE:
        raise FormatError('Malformed marker vector stride')
    return read_memory_route(data, begin - base_address, (end - begin) // STRIDE)


def route_bounds(points):
    if not 2 <= len(points) <= MAX_POINTS:
        raise FormatError('Impossible route count')
    checked = [finite(p, 3) for p in points]
    return {'min_xyz': [min(p[i] for p in checked) for i in range(3)],
            'max_xyz': [max(p[i] for p in checked) for i in range(3)]}


def world_to_map(point_xz, player_xz, heading_xz):
    wx, wz = finite(point_xz, 2)
    px, pz = finite(player_xz, 2)
    hx, hz = finite(heading_xz, 2)
    length = hx * hx + hz * hz
    if abs(length - 1) > 2e-6:
        raise FormatError('Heading must be the recovered unit state at map +0x78/+0x74')
    dx, dz = wx - px, wz - pz
    return finite((SCALE * (hz * dx - hx * dz), SCALE * (hx * dx + hz * dz)), 2)


def clip_segment(start, end, width, height):
    """1469f0: Cohen-Sutherland clip, before adding top-left logical center."""
    x0, y0 = finite(start, 2)
    x1, y1 = finite(end, 2)
    width, height = finite((width, height), 2)
    if width <= 0 or height <= 0:
        raise FormatError('Clip dimensions must be positive')
    w, h = width / 2, height / 2

    def code(x, y):
        return (1 if y > h else 2 if y < -h else 0) | (4 if x > w else 8 if x < -w else 0)

    for _ in range(12):
        a, b = code(x0, y0), code(x1, y1)
        if not a | b:
            return ((x0, y0), (x1, y1))
        if a & b:
            return None
        out = a or b
        if out & 1:
            y = h
            x = x0 + (x1 - x0) * (y - y0) / (y1 - y0)
        elif out & 2:
            y = -h
            x = x0 + (x1 - x0) * (y - y0) / (y1 - y0)
        elif out & 4:
            x = w
            y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        else:
            x = -w
            y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
        finite((x, y), 2)
        if out == a:
            x0, y0 = x, y
        else:
            x1, y1 = x, y
    raise FormatError('Clip failed to converge')


def reconstruct(points, player_xz, heading_xz, last_marker, finish_marker,
                center=(74, 392), width=90, height=86, opponents=()):
    """Recover route-window and marker centerlines for an explicit input state.

    No inferred live player state. Split/finish crossbars and GS stroke joins
    are deliberately outside this diagnostic centerline reconstruction.
    """
    bounds = route_bounds(points)
    n = len(points)
    if type(last_marker) is not int or type(finish_marker) is not int or not 0 <= finish_marker < n:
        raise FormatError('Invalid finish/last marker index')
    last = last_marker if 0 < last_marker < n else 0
    first, stop = max(last - 32, 0), min(last + 32, finish_marker)
    cx, cy = finite(center, 2)
    clip_segment((0, 0), (0, 0), width, height)
    local = [world_to_map((p[0], p[2]), player_xz, heading_xz) for p in points]

    def shifted(pair):
        return [[x + cx, y + cy] for x, y in pair]

    segments, strips = [], []
    for i in range(first, stop):
        pair = clip_segment(local[i], local[i + 1], width, height)
        if pair is None:
            continue
        segment = shifted(pair)
        segments.append({'source_indices': [i, i + 1], 'xy': segment})
        if strips and strips[-1][-1] == segment[0]:
            strips[-1].append(segment[1])
        else:
            strips.append(segment.copy())
    # 146d80 compares odd-index point against its cached preceding EVEN point,
    # not against the following segment's start. Ordinary nonzero segments
    # therefore flush separately. Keep visual continuity distinct from actual
    # queue batches. Final one-past-end lookahead cannot affect an emitted
    # nondegenerate batch and is not read by this offline diagnostic.
    flat = [p for segment in segments for p in segment['xy']]
    batches = []
    if flat:
        scratch, previous = [flat[0]], flat[0]
        for i in range(1, len(flat), 2):
            scratch.append(flat[i])
            if flat[i] != previous:
                batches.append(scratch)
                scratch = [flat[i + 1]] if i + 1 < len(flat) else []
            if i + 1 < len(flat):
                previous = flat[i + 1]
        if len(scratch) > 1:
            batches.append(scratch)
    opponent_records = []
    for p in opponents:
        x, y = world_to_map(p, player_xz, heading_xz)
        lines = [((x - 4, y - 4), (x + 4, y + 4)),
                 ((x + 4, y - 4), (x - 4, y + 4))]
        visible = [shifted(c) for a, b in lines if (c := clip_segment(a, b, width, height)) is not None]
        opponent_records.append({'local_xy': [x, y], 'foreground_segments': visible})
    return {'schema_version': 1, 'scope': 'recovered centerlines; explicit state, not live capture',
            'arithmetic': 'Python precision with float32 route input and ELF scale; not GS emulation',
            'state': {'player_xz': list(finite(player_xz, 2)), 'heading_xz': list(finite(heading_xz, 2)),
                      'last_marker': last_marker, 'effective_last_marker': last,
                      'finish_marker': finish_marker, 'center_xy': [cx, cy],
                      'clip_width': width, 'clip_height': height, 'scale': SCALE},
            'route_bounds': bounds, 'point_count': n, 'segment_window': [first, stop],
            'route_world_xyz': [list(p) for p in points], 'route_local_xy': [list(p) for p in local],
            'route_clipped_segments': segments, 'route_polyline_batches': batches,
            'route_visual_strips': strips,
            'renderer_rejected_batch_indices': [i for i, batch in enumerate(batches) if len(batch) > 64],
            'player_foreground_xy': [[cx - 5, cy + 5], [cx, cy - 5], [cx + 5, cy + 5]],
            'opponents': opponent_records,
            'excluded': ['split/finish crossbars', 'heading state evolution', 'stroke joins', 'GS rasterization']}


def sprite_logical_point(position, local_xy):
    """Global en2d, identity linear matrix, zero command cursor.

    Conditional logical screen equation; physical vertical factor is separate.
    No prediction of an owner-modified matrix or dynamic text rectangle.
    """
    tx, ty = finite(position, 2)
    x, y = finite(local_xy, 2)
    return tx + x - 0.5, 480 - ty + y - 0.5


def sprite_logical_rect(position, local_rect):
    x0, y0, x1, y1 = finite(local_rect, 4)
    if x0 > x1 or y0 > y1:
        raise FormatError('Reversed sprite bounds')
    return list(sprite_logical_point(position, (x0, y0)) + sprite_logical_point(position, (x1, y1)))


def local_output(path, sources=()):
    """Resolve before writing; refuse traversal, links outside data, and inputs."""
    result, root = Path(path).resolve(), (ROOT / 'data').resolve()
    if not result.is_relative_to(root) or result == root or result in {Path(p).resolve() for p in sources}:
        raise FormatError('Geometry output must be inside ignored data and distinct from inputs')
    if result.exists():
        raise FormatError('Output already exists; choose a new diagnostic path')
    return result


def svg(document):
    def coords(points):
        return ' '.join(f'{x:.9g},{y:.9g}' for x, y in points)
    s = document['state']
    cx, cy = s['center_xy']
    w, h = s['clip_width'], s['clip_height']
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480">',
             '<title>PS2-UI2 recovered RaceLine; explicit diagnostic state</title>',
             '<rect width="640" height="480" fill="#101010"/>',
             f'<rect x="{cx-w/2:.9g}" y="{cy-h/2:.9g}" width="{w:.9g}" height="{h:.9g}" fill="none" stroke="#888"/>']
    for strip in document['route_visual_strips']:
        lines.append(f'<polyline points="{coords(strip)}" fill="none" stroke="#329619" stroke-width="3"/>')
    lines.append(f'<polyline points="{coords(document["player_foreground_xy"])}" fill="none" stroke="white" stroke-width="4"/>')
    for opponent in document['opponents']:
        for line in opponent['foreground_segments']:
            lines.append(f'<polyline points="{coords(line)}" fill="none" stroke="#ff8000" stroke-width="4"/>')
    lines.append('</svg>')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--xml', type=Path)
    source.add_argument('--inputs', type=Path, help='Canonical PackFS directory; reads one named XML')
    source.add_argument('--memory', type=Path)
    parser.add_argument('--resource', default=r'\TNG\DATASCENE\RACETEST\ITALYS1.XML')
    parser.add_argument('--offset', type=lambda s: int(s, 0))
    parser.add_argument('--count', type=int)
    parser.add_argument('--vector-offset', type=lambda s: int(s, 0))
    parser.add_argument('--base-address', type=lambda s: int(s, 0))
    parser.add_argument('--player', nargs=2, type=float, required=True, metavar=('X', 'Z'))
    parser.add_argument('--heading', nargs=2, type=float, required=True, metavar=('HX', 'HZ'))
    parser.add_argument('--last', type=int, required=True)
    parser.add_argument('--finish', type=int, required=True)
    parser.add_argument('--center', nargs=2, type=float, default=(74, 392))
    parser.add_argument('--width', type=float, default=90)
    parser.add_argument('--height', type=float, default=86)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--svg', type=Path)
    args = parser.parse_args()
    try:
        if not args.memory and any(v is not None for v in (args.offset, args.count, args.vector_offset, args.base_address)):
            raise FormatError('Memory offsets supplied for XML source')
        if args.inputs:
            import tngtool as t
            from build_report import EXPECTED
            for name, expected in EXPECTED.items():
                if t.file_hash(args.inputs / name) != expected:
                    raise FormatError('Canonical input hash mismatch: ' + name)
            manifest, _ = t.load_pak(args.inputs / 'TNG.PAK')
            entries = [e for e in manifest['entries'] if e['kind'] == 'file' and e['path'] == args.resource]
            if len(entries) != 1 or not args.resource.endswith('.XML'):
                raise FormatError('Resource must resolve to one named XML file')
            data, provenance = t.read_payload(entries[0], args.inputs / 'TNG.000')
            provenance['asset_format'] = 'TEXT_XML'
            sources = [args.inputs / name for name in EXPECTED]
            points = read_xml_route(data)
        else:
            path = args.xml or args.memory
            sources = [path]
            if path.stat().st_size > (MAX_XML_SIZE if args.xml else 512 * 1024 * 1024):
                raise FormatError('Input size outside supported bounds')
            data = path.read_bytes()
            provenance = {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                          'source_kind': 'XML' if args.xml else 'explicit memory array'}
            if args.xml:
                points = read_xml_route(data)
            elif args.vector_offset is not None:
                if args.base_address is None or args.offset is not None or args.count is not None:
                    raise FormatError('Vector header requires only base-address and vector-offset')
                points = read_memory_vector(data, args.vector_offset, args.base_address)
                provenance.update(vector_offset=args.vector_offset, base_address=args.base_address)
            else:
                if args.offset is None or args.count is None or args.base_address is not None:
                    raise FormatError('Memory array requires offset and count')
                points = read_memory_route(data, args.offset, args.count)
                provenance.update(array_offset=args.offset, count=args.count)
        report = reconstruct(points, args.player, args.heading, args.last, args.finish,
                             args.center, args.width, args.height)
        report['provenance'] = provenance
        report['elf_sha256'] = ELF_SHA
        dest = local_output(args.output, sources)
        debug = local_output(args.svg, sources + [dest]) if args.svg else None
        content = json.dumps(report, indent=2, allow_nan=False) + '\n'
        preview = svg(report) if debug else None
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding='utf-8', newline='\n')
        if debug:
            debug.parent.mkdir(parents=True, exist_ok=True)
            debug.write_text(preview, encoding='utf-8', newline='\n')
        print(f'{len(points)} points; {len(report["route_clipped_segments"])} clipped segments; {dest}')
    except (FormatError, OSError, ValueError) as exc:
        parser.exit(2, 'hudruntime: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
