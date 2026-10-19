"""W4: PC RaceTest XML with the PS2 race logic (limits, splits, replay cameras), byte-preserving edits of the retail PC XML.

The PC XML stays the base (the engine needs its PC-only objects: reset manager, HUD loader, pace notes, boot cars). Each change below is one
recorded edit of a byte span; everything outside the edited spans is the retail file byte for byte (checked).

Changes (each can be switched off):
- limits: `LeftOuterLimit`/`RightOuterLimit` take the PS2 `LeftOuterLimit2`/`RightOuterLimit2` positions in PS2 order. Y is written as 0.00 for
  every marker: the PS2 nearest-marker search is X/Z only (`FUN_001a6758`), the PC one is 3D (`0x004CE140`), and with one constant Y per list the
  3D minimum is the X/Z minimum. `--inner ps2` (default) also writes the PS2 lists into `Left/RightInnerLimit`: PS2 has one border, PC has an
  inner and an outer one and treats a car inside the inner one as inside. With inner = outer the PC border is the PS2 border.
  The lists are densified to 10 units (same polyline, extra points on the PS2 segments): the PC side test needs the car outside two
  consecutive segments, PS2 tests one segment chosen by the corner bisector; with short segments the two agree on 97.2 to 100% (median 99.8%) of the
  area around the road instead of 84.8 to 99.3% (median 98.4%) with the PS2 markers alone (`limit_sim.py`).
- splits: Radius, ExtraTime and position (matrix Row3) of each `gaRaceSplitTimeAI` from the PS2 Egg of the same name, `TimeToFirstCheckpoint`
  of `gaRacePostFirstSplitTimeAI` from PS2, and PC split Eggs without a PS2 counterpart (`Copy of SplitTime1` on Turkey3, `Copy of SplitTime0` on
  TurkeyS2Flip) removed.
- cameras: the `Cameras` marker list (replay/TV positions) from PS2, Marker Type kept from PC.
- sounds: PS2 `enAiSoundSource` Eggs with no PC sound source within 100 units, when the sound file exists on PC (3 on FranceM).

    python build_logic.py --all --out <dir>          # writes <dir>/<Course>.xml and logic-36.json
    python build_logic.py --course Turkey3 --out <dir> --no-cameras
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / 'src'))
import course_config as cc  # noqa: E402
from master_rallye.course_xml import parse_course_xml_bytes  # noqa: E402

LIMIT_PAIRS = {'LeftOuterLimit': 'LeftOuterLimit2', 'RightOuterLimit': 'RightOuterLimit2'}
INNER_PAIRS = {'LeftInnerLimit': 'LeftOuterLimit2', 'RightInnerLimit': 'RightOuterLimit2'}


class Edits:
    """Non-overlapping byte-span replacements on one source buffer."""

    def __init__(self, data: bytes):
        self.data = data
        self.spans = []          # (start, end, new bytes, label)

    def add(self, start, end, new, label):
        for s, e, _, lab in self.spans:
            if start < e and s < end:
                raise ValueError(f'edit {label} overlaps {lab}')
        self.spans.append((start, end, new, label))

    def apply(self):
        out, pos = [], 0
        for s, e, new, _ in sorted(self.spans):
            out += [self.data[pos:s], new]
            pos = e
        out.append(self.data[pos:])
        return b''.join(out)

    def untouched_equal(self, result):
        """Every byte outside the edited spans is the source byte, in order."""
        pos_src = pos_out = 0
        for s, e, new, _ in sorted(self.spans):
            if self.data[pos_src:s] != result[pos_out:pos_out + (s - pos_src)]:
                return False
            pos_out += (s - pos_src) + len(new)
            pos_src = e
        return self.data[pos_src:] == result[pos_out:]


def nl(data):
    return b'\r\n' if b'\r\n' in data[:200] else b'\n'


def list_body(data, name):
    m = re.search(rb'<List Name="' + re.escape(name.encode()) + rb'">\r?\n', data)
    if not m:
        return None
    end = data.index(b'</List>', m.end())
    end = data.rindex(b'\n', 0, end) + 1           # start of the closing line
    return m.end(), end


def markers_in(data, span):
    body = data[span[0]:span[1]]
    out = []
    for m in re.finditer(rb'<Marker No="[^"]*">(.*?)</Marker>', body, re.S):
        blk = m.group(1)
        typ = re.search(rb'Name="Marker Type" Type="String" Value="([^"]*)"', blk)
        pos = re.search(rb'Name="Marker Pos" Type="Vector3" Value="([^"]*)"', blk)
        drn = re.search(rb'Name="Marker Dir" Type="Vector3" Value="([^"]*)"', blk)
        out.append({'type': typ.group(1).decode('latin1') if typ else None,
                    'pos': tuple(float(v) for v in pos.group(1).split()) if pos else None,
                    'dir': drn.group(1).decode('latin1') if drn else '1.00 0.00 0.00'})
    return out


def marker_block(no, typ, pos, drn, eol, indent=b'      '):
    i2 = indent + b'  '
    return (indent + f'<Marker No="{no}">'.encode() + eol +
            i2 + f'<Value Name="Marker Type" Type="String" Value="{typ}"/>'.encode() + eol +
            i2 + f'<Value Name="Marker Pos" Type="Vector3" Value="{pos[0]:.2f} {pos[1]:.2f} {pos[2]:.2f}"/>'.encode() + eol +
            i2 + f'<Value Name="Marker Dir" Type="Vector3" Value="{drn}"/>'.encode() + eol +
            indent + b'</Marker>' + eol)


def egg_spans(data):
    """name -> list of (start of the '<Egg' line, end after the '</Egg>' line)."""
    out = {}
    for m in re.finditer(rb'[ \t]*<Egg Name="([^"]*)">', data):
        end = data.index(b'</Egg>', m.end())
        end = data.index(b'\n', end) + 1
        out.setdefault(m.group(1).decode('latin1'), []).append((m.start(), end))
    return out


def value_span(data, start, end, name, attr=b'Value'):
    """Span of the attribute value of <Value Name="name" ...> inside [start, end)."""
    m = re.compile(rb'<Value Name="' + re.escape(name.encode()) + rb'"[^>]*?' + attr + rb'="([^"]*)"').search(data, start, end)
    return None if m is None else (m.start(1), m.end(1), m.group(1))


def fmt_like(old: bytes, value: float) -> bytes:
    decimals = len(old.split(b'.')[1]) if b'.' in old else 0
    return f'{value:.{decimals}f}'.encode()


LIMIT_STEP = 10.0
SOUND_CLASSES = ('enAiSoundSource',)
SOUND_NEAR = 100.0
AUDIO_ROOT = Path('D:/Game/Master Rallye/corpora/retail/DataAudio')


def audio_files(root=AUDIO_ROOT):
    return {str(p.relative_to(root).with_suffix('')).replace('/', '\\').lower() for p in root.rglob('*.wav')}


def add_sounds(pc, ps2, ed, rep, eol):
    """PS2 sound sources with no PC sound source within SOUND_NEAR units, copied as Egg blocks to the end of the PC `Sound` list.

    Only classes the PC executable has, only when the sound file exists in the PC DataAudio tree. Sound parameters of sources present on both
    stay PC: on six courses the PS2 values are the exporter placeholder (`Environment/birds`, 40/80, volume 1) for every source."""
    doc_pc, doc_ps2 = parse_course_xml_bytes(pc, 'pc'), parse_course_xml_bytes(ps2, 'ps2')
    pc_pos = [e.matrix().position for e in doc_pc.eggs
              if any(k.tag in SOUND_CLASSES + ('gaAiWaterfallSound', 'gaAiBirdSound') for k in e.components()) and e.matrix() and e.matrix().position]
    names = {e.name for e in doc_pc.eggs}
    files = audio_files()
    spans_ps2 = egg_spans(ps2)
    span = list_body(pc, 'Sound')
    if span is None:
        return
    blocks = []
    for e in doc_ps2.eggs:
        comps = [k for k in e.components() if k.tag in SOUND_CLASSES]
        m = e.matrix()
        if not comps or m is None or m.position is None:
            continue
        if pc_pos and min(math.dist(m.position, q) for q in pc_pos) <= SOUND_NEAR:
            continue
        sound = next((v.value for v in comps[0].values if v.name == 'Sound'), None)
        if sound is None or sound.replace('/', '\\').lower() not in files:
            rep['changes'].append({'sound': e.name, 'skipped': f'sound file {sound} not in PC DataAudio'})
            continue
        if e.name in names or len(spans_ps2.get(e.name, [])) != 1:
            rep['changes'].append({'sound': e.name, 'skipped': 'name collision'})
            continue
        s, t = spans_ps2[e.name][0]
        blk = ps2[s:t]
        if eol == b'\r\n' and b'\r\n' not in blk:
            blk = blk.replace(b'\n', b'\r\n')
        blocks.append(blk)
        rep['changes'].append({'sound': e.name, 'added': sound, 'pos': list(m.position)})
    if blocks:
        ed.add(span[1], span[1], b''.join(blocks), 'sounds')


def densify(pts, step):
    """Same polyline with extra points so that no X/Z segment is longer than step (the PS2 markers are kept, in order)."""
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, math.ceil(math.dist((a[0], a[2]), (b[0], b[2])) / step))
        out += [tuple(a[i] + k / n * (b[i] - a[i]) for i in range(3)) for k in range(1, n + 1)]
    return out


def build(course, limits=True, inner='ps2', splits=True, cameras=True, sounds=True, limit_step=LIMIT_STEP):
    pc = course.pc_xml.read_bytes()
    ps2 = cc.read_ps2(course.ps2_xml)
    eol = nl(pc)
    ed = Edits(pc)
    rep = {'course': course.name, 'source_sha256': hashlib.sha256(pc).hexdigest(), 'changes': []}

    def replace_list(pc_name, ps2_name, y_zero, keep_type=True, step=None):
        span_pc, span_ps2 = list_body(pc, pc_name), list_body(ps2, ps2_name)
        if span_pc is None or span_ps2 is None:
            rep['changes'].append({'list': pc_name, 'skipped': 'list missing', 'pc': span_pc is not None, 'ps2': span_ps2 is not None})
            return
        old, new = markers_in(pc, span_pc), markers_in(ps2, span_ps2)
        typ = old[0]['type'] if old and keep_type else new[0]['type']
        n_ps2 = len(new)
        if step:
            new = [{'pos': q, 'dir': new[0]['dir']} for q in densify([m['pos'] for m in new], step)]
        body = b''.join(marker_block(i, typ, (m['pos'][0], 0.0 if y_zero else m['pos'][1], m['pos'][2]), m['dir'] if not y_zero else old[0]['dir'], eol)
                        for i, m in enumerate(new))
        ed.add(*span_pc, body, f'list {pc_name}')
        rep['changes'].append({'list': pc_name, 'from': ps2_name, 'pc_markers': len(old), 'ps2_markers': n_ps2, 'written_markers': len(new),
                               'y': 0.0 if y_zero else 'ps2', 'densify_step': step})

    if limits:
        for a, b in LIMIT_PAIRS.items():
            replace_list(a, b, True, step=limit_step)
        if inner == 'ps2':
            for a, b in INNER_PAIRS.items():
                replace_list(a, b, True, step=limit_step)
    if cameras:
        p, q = markers_in(pc, list_body(pc, 'Cameras') or (0, 0)), markers_in(ps2, list_body(ps2, 'Cameras') or (0, 0))
        if p and q and (len(p) != len(q) or any(math.dist(a['pos'], b['pos']) > 0.01 for a, b in zip(p, q))):
            replace_list('Cameras', 'Cameras', False)
    if splits:
        doc_pc, doc_ps2 = parse_course_xml_bytes(pc, 'pc'), parse_course_xml_bytes(ps2, 'ps2')
        ps2_split = {e.name: e for e in doc_ps2.split_time_eggs}
        eggs_pc, eggs_ps2 = egg_spans(pc), egg_spans(ps2)
        for e in doc_pc.split_time_eggs:
            spans = eggs_pc.get(e.name, [])
            if len(spans) != 1:
                rep['changes'].append({'split': e.name, 'skipped': f'{len(spans)} Eggs of that name'})
                continue
            s, t = spans[0]
            q = ps2_split.get(e.name)
            if q is None:
                ed.add(s, t, b'', f'remove {e.name}')
                rep['changes'].append({'split': e.name, 'removed': 'no PS2 Egg of that name'})
                continue
            qs, qt = eggs_ps2[e.name][0]
            for field in ('Radius', 'ExtraTime'):
                a, b = value_span(pc, s, t, field), value_span(ps2, qs, qt, field)
                if a and b and float(a[2]) != float(b[2]):
                    ed.add(a[0], a[1], fmt_like(a[2], float(b[2])), f'{e.name} {field}')
                    rep['changes'].append({'split': e.name, 'field': field, 'pc': float(a[2]), 'ps2': float(b[2])})
            a, b = value_span(pc, s, t, 'en3d Matrix', b'Row3'), value_span(ps2, qs, qt, 'en3d Matrix', b'Row3')
            if a and b:
                va, vb = [float(v) for v in a[2].split()], [float(v) for v in b[2].split()]
                if math.dist(va[:3], vb[:3]) > 0.005:
                    ed.add(a[0], a[1], b[2], f'{e.name} position')
                    rep['changes'].append({'split': e.name, 'field': 'position', 'pc': va[:3], 'ps2': vb[:3]})
        for name, spans in eggs_pc.items():
            a = [value_span(pc, s, t, 'TimeToFirstCheckpoint') for s, t in spans]
            if len(spans) != 1 or not a[0] or name not in eggs_ps2:
                continue
            b = value_span(ps2, *eggs_ps2[name][0], 'TimeToFirstCheckpoint')
            if b and float(a[0][2]) != float(b[2]):
                ed.add(a[0][0], a[0][1], fmt_like(a[0][2], float(b[2])), f'{name} TimeToFirstCheckpoint')
                rep['changes'].append({'egg': name, 'field': 'TimeToFirstCheckpoint', 'pc': float(a[0][2]), 'ps2': float(b[2])})

    if sounds:
        add_sounds(pc, ps2, ed, rep, eol)

    out = ed.apply()
    rep['candidate_sha256'] = hashlib.sha256(out).hexdigest()
    rep['checks'] = check(course, pc, ps2, out, ed, limits, inner, splits, cameras, rep['changes'], limit_step)
    return out, rep


def on_polyline(got, ref, tol=0.01):
    """got contains every ref point in order and every other got point lies on the ref segment between its neighbours (X/Z)."""
    if not got or not ref:
        return False
    j = 0
    for k, p in enumerate(got):
        if j < len(ref) and math.dist(p, ref[j]) <= tol:
            j += 1
            continue
        if j == 0 or j >= len(ref):
            return False
        a, b = ref[j - 1], ref[j]
        ab = (b[0] - a[0], b[1] - a[1])
        L2 = ab[0] ** 2 + ab[1] ** 2
        t = max(0.0, min(1.0, ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1]) / L2)) if L2 else 0.0
        if math.dist(p, (a[0] + t * ab[0], a[1] + t * ab[1])) > tol:
            return False
    return j == len(ref)


def check(course, pc, ps2, out, ed, limits, inner, splits, cameras, rep_changes=(), limit_step=None):
    res = {'untouched_bytes_equal': ed.untouched_equal(out)}
    try:
        doc = parse_course_xml_bytes(out, 'candidate')
        res['parses'] = True
    except Exception as e:  # noqa: BLE001
        res['parses'] = f'{type(e).__name__}: {e}'
        return res
    ps2doc, pcdoc = parse_course_xml_bytes(ps2, 'ps2'), parse_course_xml_bytes(pc, 'pc')

    def xz(doc_, name):
        ml = doc_.marker_list(name)
        return None if ml is None else [(m.position[0], m.position[2]) for m in ml.markers]

    def same(a, b):
        return a is not None and b is not None and len(a) == len(b) and all(math.dist(p, q) <= 0.006 for p, q in zip(a, b))
    if limits:
        pairs = dict(LIMIT_PAIRS, **(INNER_PAIRS if inner == 'ps2' else {}))
        if limit_step:
            res['limits_on_ps2_polyline_xz'] = all(on_polyline(xz(doc, a), xz(ps2doc, b)) for a, b in pairs.items())
        else:
            res['limits_equal_ps2_xz'] = all(same(xz(doc, a), xz(ps2doc, b)) for a, b in pairs.items())
        res['limits_constant_y'] = all(len({m.position[1] for m in doc.marker_list(a).markers}) == 1 for a in pairs)
    if splits:
        ps2s = {e.name: e for e in ps2doc.split_time_eggs}
        got = {e.name: e for e in doc.split_time_eggs}
        res['split_names_equal_ps2'] = sorted(got) == sorted(ps2s)
        res['split_values_equal_ps2'] = all(
            {v.name: float(v.value) for v in got[n].split_time_component.values} == {v.name: float(v.value) for v in ps2s[n].split_time_component.values}
            for n in got if n in ps2s)
    # nothing else changed: same Egg names (minus removed splits) and same marker lists
    removed = {e.name for e in pcdoc.split_time_eggs} - {e.name for e in doc.split_time_eggs}
    added = sorted(c['sound'] for c in rep_changes if 'added' in c)
    res['other_eggs_kept'] = sorted(e.name or '' for e in doc.eggs) == sorted([e.name or '' for e in pcdoc.eggs if e.name not in removed] + added)
    res['marker_lists_kept'] = [m.name for m in doc.marker_lists] == [m.name for m in pcdoc.marker_lists]
    if cameras and doc.marker_list('Cameras') and ps2doc.marker_list('Cameras'):
        res['cameras_equal_ps2'] = len(doc.marker_list('Cameras').markers) == len(ps2doc.marker_list('Cameras').markers) and all(
            math.dist(a.position, b.position) <= 0.006 for a, b in zip(doc.marker_list('Cameras').markers, ps2doc.marker_list('Cameras').markers))
    res['pass'] = all(v is True for v in res.values())
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--course')
    g.add_argument('--all', action='store_true')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--no-limits', action='store_true')
    ap.add_argument('--inner', choices=('ps2', 'keep'), default='ps2')
    ap.add_argument('--no-splits', action='store_true')
    ap.add_argument('--no-cameras', action='store_true')
    ap.add_argument('--no-sounds', action='store_true')
    ap.add_argument('--limit-step', type=float, default=LIMIT_STEP, help='densify the limit lists to this X/Z spacing (0 = PS2 markers only)')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    todo = cc.courses() if a.all else [cc.course(a.course)]
    reps = {}
    for c in todo:
        data, rep = build(c, not a.no_limits, a.inner, not a.no_splits, not a.no_cameras, not a.no_sounds, a.limit_step or None)
        (a.out / f'{c.name}.xml').write_bytes(data)
        reps[c.name] = rep
        print(c.name, 'pass' if rep['checks'].get('pass') else rep['checks'], len(rep['changes']), 'changes')
    (a.out / ('logic-36.json' if a.all else f'logic-{todo[0].name}.json')).write_text(json.dumps(reps, indent=1))


if __name__ == '__main__':
    main()
