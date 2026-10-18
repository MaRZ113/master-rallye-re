"""G-COLL query 2: where is PS2 collision solid above PC ground? XZ grid on Turkey3.

For each grid cell the PC ground height comes from tag100 (first solid contact from above). PS2 solidity is then tested at
fixed heights above that ground. The result is related to the RaceLine and to the outer limit lists of both scenes.
"""
import json
import math
import struct
import sys
import zlib
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools'))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
sys.path.insert(0, str(HERE))
import course_delta as cd  # noqa: E402
import gcoll_columns as gc  # noqa: E402
import geometry_delta as g  # noqa: E402
import ps2_bsp  # noqa: E402
import bsp_query as q  # noqa: E402

HEIGHTS = (3.0, 30.0, 100.0)
Y_TOP, Y_BOTTOM = 400.0, -200.0


def markers(sdk, data, name):
    doc = sdk.parse_course_xml_bytes(data, name)
    ml = doc.marker_list(name)
    return [] if ml is None else [(m.position[0], m.position[2]) for m in ml.markers if m.position]


def polyline_distance(pts, x, z):
    return min((math.dist((x, z), p) for p in pts), default=math.inf)


def png(path, w, h, rows):
    raw = b''.join(b'\x00' + bytes(r) for r in rows)
    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    Path(path).write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>2I5B', w, h, 8, 2, 0, 0, 0))
                           + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def main(ps2_root, pc_root, sdk_path, bsp_path, out_dir, step=16.0):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pc_root = Path(pc_root)
    bsp = ps2_bsp.parse(Path(bsp_path).read_bytes())
    pcn = gc.pc_nodes(pc_root / 'DataGx/Course/Turkey3/turkey3.dx')
    sdk, _ = cd.sdk_modules(Path(sdk_path))
    pc_xml = (pc_root / 'DataScene/RaceTest/Turkey3.xml').read_bytes()
    ps2_xml = (HERE.parent / 'data/cdelta1/cache/TNG/DATASCENE/RACETEST/TURKEY3.XML').read_bytes()
    route = markers(sdk, pc_xml, 'RaceLine')
    pc_limits = {n: markers(sdk, pc_xml, n) for n in ('LeftOuterLimit', 'RightOuterLimit')}
    ps2_limits = {n: markers(sdk, ps2_xml, n) for n in ('LeftOuterLimit2', 'RightOuterLimit2')}
    xs = [p[0] for p in route]
    zs = [p[1] for p in route]
    margin = 400.0
    x0, x1, z0, z1 = min(xs) - margin, max(xs) + margin, min(zs) - margin, max(zs) + margin
    nx, nz = int((x1 - x0) / step) + 1, int((z1 - z0) / step) + 1
    cells = []
    counts = Counter()
    for j in range(nz):
        row = []
        for i in range(nx):
            x, z = x0 + i * step, z0 + j * step
            t = gc.pc_first_contact(pcn, (x, Y_TOP, z), (x, Y_BOTTOM, z))
            if t is None:
                row.append(None)
                counts['pc_no_ground'] += 1
                continue
            ground = Y_TOP + (Y_BOTTOM - Y_TOP) * t
            solid = tuple(q.ps2_is_solid(bsp, (x, ground + h, z)) for h in HEIGHTS)
            row.append((ground, solid))
            counts['pc_ground'] += 1
            counts['solid_at_' + str(int(HEIGHTS[0]))] += solid[0]
            counts['solid_at_' + str(int(HEIGHTS[1]))] += solid[1]
            counts['solid_at_' + str(int(HEIGHTS[2]))] += solid[2]
        cells.append(row)
    # relation to the route and limits
    bands = Counter()
    limit_stats = {'pc_outer': [], 'ps2_outer': []}
    for j, row in enumerate(cells):
        for i, cell in enumerate(row):
            if cell is None:
                continue
            x, z = x0 + i * step, z0 + j * step
            d = polyline_distance(route, x, z)
            band = min(int(d // 25), 12)
            bands[band, cell[1][0]] += 1
    band_table = {f'{b*25}-{b*25+25}' if b < 12 else '300+': {
        'cells': bands[b, True] + bands[b, False],
        'ps2_solid_at_3_percent': round(100 * bands[b, True] / max(1, bands[b, True] + bands[b, False]), 1)}
        for b in range(13)}
    # image (SCALE pixels per cell): white RaceLine, red PS2 solid at +3, orange solid only higher, green open, dark no PC ground;
    # blue = PC outer limits, yellow = PS2 outer limits
    SCALE = 5
    def cell_of(p):
        return (int((p[0] - x0) / step), int((p[1] - z0) / step))
    marks = {}
    for pts, colour in ((route, (255, 255, 255)),):
        for p in pts:
            marks[cell_of(p)] = colour
    for pts in pc_limits.values():
        for p in pts:
            marks[cell_of(p)] = (60, 120, 255)
    for pts in ps2_limits.values():
        for p in pts:
            marks.setdefault(cell_of(p), (255, 230, 40))
    rows = []
    for j in range(nz - 1, -1, -1):
        r = []
        for i in range(nx):
            cell = cells[j][i]
            if (i, j) in marks:
                colour = marks[(i, j)]
            elif cell is None:
                colour = (10, 10, 40)
            elif cell[1][0]:
                colour = (200, 50, 50)
            elif cell[1][1] or cell[1][2]:
                colour = (240, 160, 40)
            else:
                colour = (60, 140, 60)
            r += list(colour) * SCALE
        for _ in range(SCALE):
            rows.append(r)
    png(out_dir / 'turkey3-ps2-solid-map.png', nx * SCALE, nz * SCALE, rows)
    summary = {'step': step, 'grid': [nx, nz], 'bounds': [x0, x1, z0, z1], 'counts': dict(counts),
               'by_route_distance': band_table,
               'limits': {'pc_outer_points': {k: len(v) for k, v in pc_limits.items()},
                          'ps2_outer_points': {k: len(v) for k, v in ps2_limits.items()}},
               'legend': 'white=RaceLine, red=PS2 solid at +3 above PC ground, orange=solid only higher, green=open, dark=no PC ground, blue=PC outer limits, yellow=PS2 outer limits'}
    (out_dir / 'turkey3-ps2-solid-map.json').write_text(json.dumps(summary, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:6])
