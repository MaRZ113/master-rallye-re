"""Offline gaEntitySpline diagnostic for the canonical PS2 build.

This reconstructs controller ticks, not captured gameplay or the PS2 FPU.
Only finite, nondegenerate authored routes are accepted. Output containing
route coordinates must stay under this repository's ignored data directory.
See ambient1/spline-algorithm.md and transform-pipeline.md for proof boundaries.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

import tngtool

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA = 'b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2'
INPUTS = {
    'SLES_509.06': (3739852, ELF_SHA),
    'SYSTEM.CNF': (56, 'db08eef06278820a562f9cdacd6a2d5d2bb31870e7cf3a51e83daee3a90c5df2'),
    'TNG.PAK': (135556, tngtool.PAK_SHA),
    'TNG.000': (1225915283, tngtool.DATA_SHA),
}


class ContractError(ValueError):
    """Unsupported or numerically unsafe diagnostic input; no guessed repair."""


def f32(x):
    try:
        y = struct.unpack('<f', struct.pack('<f', x))[0]
    except (OverflowError, struct.error) as e:
        raise ContractError('float32 overflow') from e
    if not math.isfinite(y):
        raise ContractError('nonfinite float32')
    return y


def add(a, b): return f32(a + b)
def sub(a, b): return f32(a - b)
def mul(a, b): return f32(a * b)
def div(a, b):
    if b == 0: raise ContractError('zero denominator')
    return f32(a / b)


def dot(a, b):
    return add(add(mul(a[0], b[0]), mul(a[1], b[1])), mul(a[2], b[2]))


def delta(a, b): return tuple(sub(x, y) for x, y in zip(a, b))
def norm(a): return f32(math.sqrt(dot(a, a)))


def forward(new, old, previous):
    """001a9e08: normalized displacement, with two original small-vector tests."""
    d = delta(new, old)
    if all(abs(x) <= f32(.0001) for x in d): return previous
    length2 = dot(d, d)
    if length2 <= f32(2**-23): return previous
    r = div(1., f32(math.sqrt(length2)))
    v = tuple(mul(x, r) for x in d)
    return previous if dot(v, v) < f32(.0001) else v


def properties(node):
    """Retain every Value, its type, lexical numbers and original order."""
    return [dict(v.attrib) for v in node.findall('Value')]


def value(rows, name, typ, absent=None):
    # Typed broker scans stop at the first matching typed property. Metadata
    # retains subsequent duplicates; it is never converted to a name dictionary.
    for r in rows:
        if r.get('Name') == name and r.get('Type') == typ:
            return r.get('Value')
    return absent


def vector(text):
    try: v = tuple(f32(float(x)) for x in text.split())
    except (AttributeError, ValueError) as e: raise ContractError('invalid Vector3') from e
    if len(v) != 3: raise ContractError('Vector3 needs three components')
    return v


@dataclass(frozen=True)
class Config:
    const_speed: bool
    loop: bool
    trigger: bool
    speed: float
    on: float
    off: float
    rest: bool
    rest_ticks: int
    banking: float
    samples: int

    @classmethod
    def from_properties(cls, rows):
        def boolean(n):
            s = value(rows, n, 'Bool', 'False')
            if s not in ('True', 'False'): raise ContractError('invalid Bool: '+n)
            return s == 'True'
        def number(n):
            try: return f32(float(value(rows, n, 'Float', '0')))
            except ValueError as e: raise ContractError('invalid Float: '+n) from e
        def integer(n):
            try: return int(value(rows, n, 'Int', '0'))
            except ValueError as e: raise ContractError('invalid Int: '+n) from e
        seconds = integer('Rest Time (sec)')
        ticks = ((seconds * 30 + 2**31) % 2**32) - 2**31
        c = cls(boolean('Use Const Speed'), boolean('Use Closed Loop'),
                boolean('Use Trigger System'), number('Max Speed/Const Speed'),
                number('Trigger Dist On'), number('Trigger Dist Off'),
                boolean('Use Rest On NonLoop'), ticks, number('Banking'),
                integer('Number Of Samples'))
        if c.speed <= f32(.0001): raise ContractError('speed must exceed 0.0001')
        if not 1 <= c.samples <= 100000: raise ContractError('unsafe sample buffer size')
        return c


def parse_case(payload, source, egg_name, occurrence=0):
    if b'<!DOCTYPE' in payload.upper() or b'<!ENTITY' in payload.upper():
        raise ContractError('XML declarations are outside the course contract')
    try: tree = ET.fromstring(payload)
    except ET.ParseError as e: raise ContractError('malformed XML') from e
    candidates = []
    for egg in tree.findall('./EggLists_Version4/List/Egg'):
        if egg.get('Name') != egg_name: continue
        for ai in egg.findall('AI_List/AI'):
            if value(properties(ai), 'AI Name', 'String') != 'gaEntitySpline': continue
            owner = ai.find('gaEntitySpline')
            if owner is None: raise ContractError('missing owner configuration')
            candidates.append((egg, ai, owner))
    if occurrence < 0 or occurrence >= len(candidates):
        raise ContractError('named spline Egg/occurrence absent')
    egg, ai, owner = candidates[occurrence]
    rows = properties(owner)
    name = value(rows, 'MarkerList Name', 'String')
    lists = [r for r in tree.findall('MarkerLists/List') if r.get('Name') == name]
    if len(lists) != 1: raise ContractError('named marker list absent or ambiguous')
    markers = [{'attributes': dict(m.attrib), 'properties': properties(m)}
               for m in lists[0].findall('Marker')]
    points = [vector(value(m['properties'], 'Marker Pos', 'Vector3')) for m in markers]
    for m in markers:
        # Shared loader requires Type, Pos and Dir; spline geometry uses only Pos.
        if value(m['properties'], 'Marker Type', 'String') is None:
            raise ContractError('missing Marker Type')
        vector(value(m['properties'], 'Marker Dir', 'Vector3'))
    identity = {'source': source, 'decoded_sha256': tngtool.sha(payload),
                'egg': egg_name, 'occurrence': occurrence,
                'ai_attributes': dict(ai.attrib), 'owner': 'gaEntitySpline',
                'model': value(properties(egg), 'en3d Model Name', 'String'),
                'egg_properties': properties(egg), 'parameters': rows,
                'marker_list': name, 'markers': markers}
    identity['route_sha256'] = tngtool.sha(json.dumps(
        {'name': name, 'markers': markers}, ensure_ascii=False,
        separators=(',', ':')).encode('utf-8'))
    return identity, points, Config.from_properties(rows)


class Corpus:
    """Read-only named PackFS access, using the existing validated decoder."""
    def __init__(self, directory):
        self.directory = Path(directory)
        self.provenance = {}
        for name, (size, sha) in INPUTS.items():
            p = self.directory / name
            if p.stat().st_size != size or tngtool.file_hash(p) != sha:
                raise ContractError('unsupported canonical input: '+name)
            self.provenance[name] = {'size': size, 'sha256': sha}
        self.manifest, _ = tngtool.load_pak(self.directory / 'TNG.PAK')

    def case(self, course, egg, occurrence=0):
        if not course or any(x not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_' for x in course):
            raise ContractError('invalid course identifier')
        logical = '\\TNG\\DATASCENE\\RACETEST\\'+course+'.XML'
        matches = [e for e in self.manifest['entries'] if e['path'] == logical]
        if len(matches) != 1: raise ContractError('course resource absent')
        payload, report = tngtool.read_payload(matches[0], self.directory / 'TNG.000')
        identity, points, config = parse_case(payload, logical, egg, occurrence)
        identity['packfs'] = report
        return identity, points, config


def weights(u):
    """001a9ccc..001a9d1c, original scalar operation order."""
    h = mul(u, .5)
    a = mul(h, u)
    b = mul(a, u)
    double_a = add(a, a)
    four_a = add(double_a, double_a)
    triple_b = mul(b, 3.)
    return (sub(add(-b, double_a), h),
            add(sub(triple_b, add(four_a, a)), 1.),
            add(add(-triple_b, four_a), h), sub(b, a))


class PathState:
    def __init__(self, points, config):
        self.config = config
        self.points = [tuple(f32(x) for x in p) for p in points]
        if len(self.points) < 4: raise ContractError('setup requires at least four points')
        lengths = [norm(delta(b, a)) for a, b in zip(self.points, self.points[1:])]
        if any(d == 0 for d in lengths): raise ContractError('duplicate adjacent route points')
        closing = norm(delta(self.points[0], self.points[-1]))
        self.knots = [0.]
        if config.const_speed:
            intervals = [div(d, config.speed) for d in lengths]
            # 001a8694..001a869c: also set for an OPEN constant-speed route.
            self.closing_time = div(closing, config.speed)
        else:
            total = 0.
            for d in lengths: total = add(total, d)
            if config.loop: total = add(total, closing)
            interval = div(div(total, config.speed), f32(len(self.points)))
            intervals = [interval] * (len(self.points) - 1)
            self.closing_time = interval if config.loop else 0.
        for d in intervals: self.knots.append(add(self.knots[-1], d))
        self.duration = add(self.knots[-1], self.closing_time)
        if self.duration <= 0: raise ContractError('nonpositive route duration')
        self.cached_local = None
        self.cached_weights = None

    def evaluate(self, time):
        t = f32(time)
        if t < 0: raise ContractError('negative path time is outside the diagnostic domain')
        if self.config.loop:
            if t / self.duration > 100000: raise ContractError('excessive wrap count')
            while t >= self.duration: t = sub(t, self.duration)
        else: t = min(t, self.knots[-1])
        segment = len(self.points) - 1
        for i in range(len(self.knots) - 1):
            if t < self.knots[i+1]:
                segment = i
                break
        start = self.knots[segment]
        end = (add(start, self.closing_time) if segment == len(self.points)-1
               and self.config.loop else self.knots[min(segment+1, len(self.knots)-1)])
        coordinate = add(f32(segment), div(sub(t, start), sub(end, start))) if end != start else f32(segment)
        index = math.floor(coordinate)
        local = sub(coordinate, f32(index))
        # ELF compares the global coordinate to a cache storing the local one.
        # Closed evaluation clears the validity flag each time (001a9580).
        if self.config.loop or self.cached_local != coordinate:
            self.cached_weights = weights(local)
            self.cached_local = local
        w = self.cached_weights
        def point(i):
            return self.points[i % len(self.points)] if self.config.loop else self.points[max(0, min(i, len(self.points)-1))]
        controls = [point(index-1), point(index), point(index+1), point(index+2)]
        out = []
        for axis in range(3):
            q = mul(controls[0][axis], w[0])
            for p, weight in zip(controls[1:], w[1:]): q = add(q, mul(p[axis], weight))
            out.append(q)
        return tuple(out)


def trigger_state(active, distance2, on, off):
    if active: return False if mul(off, off) < distance2 else True
    return True if distance2 < mul(on, on) else False


def matrix(position, direction, up):
    # 001aa2e0 is deliberately NOT a cross product. Banking affects only up.
    right = (direction[2], direction[1], -direction[0])
    return [list(right)+[0.], list(up)+[0.], list(direction)+[0.], list(position)+[1.]]


@dataclass
class Controller:
    path: PathState
    initial_bank_flag: int
    time: float = 0.
    rest_counter: int = 0
    ring_index: int = 0
    bank_mean: float = 0.
    history: list = field(default_factory=list)

    def __post_init__(self):
        if self.initial_bank_flag != 0:
            raise ContractError('initializer bank flag must explicitly be 0; other heap state needs a capture')
        c = self.path.config
        ahead = self.path.evaluate(1.)
        self.position = self.path.evaluate(0.)
        self.direction = forward(ahead, self.position, (0., 0., 0.))
        if dot(self.direction, self.direction) == 0:
            raise ContractError('initial forward needs unknown cached state')
        self.up = (0., 1., 0.)
        self.active = not c.trigger
        self.history = [0.] * c.samples
        self.time = f32(self.time)

    def bank_up(self, new, direction):
        c = self.path.config
        if c.banking == 0: return (0., 1., 0.)
        ratio = div(mul(norm(delta(new, self.position)), 30.), c.speed)
        b = mul(sub(1., dot(direction, self.direction)), .5)
        b = mul(mul(mul(mul(b, ratio), c.banking), f32(math.pi)), 5000.)
        sideways = (-self.direction[2], self.direction[1], self.direction[0])
        if dot(direction, sideways) > 0: b = -b
        n = f32(c.samples)
        self.bank_mean = add(sub(self.bank_mean, div(self.history[self.ring_index], n)), div(b, n))
        self.history[self.ring_index] = b
        half = mul(self.bank_mean, .5)
        sine, cosine = f32(math.sin(half)), f32(math.cos(half))
        x, y, z = (mul(sine, v) for v in direction)
        xx, yy, zz = mul(add(x, x), x), mul(add(y, y), y), mul(add(z, z), z)
        # Row 1 of the quaternion matrix, transformed (0,1,0) by 001ca568.
        return (add(mul(add(y, y), x), mul(add(z, z), cosine)),
                sub(1., add(xx, zz)),
                sub(mul(add(z, z), y), mul(add(x, x), cosine)))

    def step(self, observer):
        c = self.path.config
        published_time = self.time
        distance2 = None
        status = 'NO_OBSERVER'
        if observer is not None:
            observer = tuple(f32(x) for x in observer)
            if len(observer) != 3: raise ContractError('observer needs XYZ')
            d = delta(observer, self.position)
            distance2 = add(add(mul(d[0], d[0]), 0.), mul(d[2], d[2]))
            if c.trigger: self.active = trigger_state(self.active, distance2, c.on, c.off)
            status = 'INACTIVE'
            if self.active:
                status = 'ACTIVE'
                self.ring_index = (self.ring_index + 1) % c.samples
                new = self.path.evaluate(self.time)
                direction = forward(new, self.position, self.direction)
                self.up = self.bank_up(new, direction)
                self.position, self.direction = new, direction
                self.time = add(self.time, f32(1/30))
                if self.path.duration < self.time:
                    if c.loop: self.time = 0.
                    else:
                        self.time = self.path.duration
                        if c.rest:
                            if self.rest_counter < c.rest_ticks: self.rest_counter += 1
                            else: self.time, self.rest_counter = 0., 0
        return {'status': status, 'active': self.active, 'observer_distance2_xz': distance2,
                'evaluated_time': published_time if status == 'ACTIVE' else None,
                'next_time': self.time, 'rest_counter': self.rest_counter,
                'ring_index': self.ring_index, 'bank_mean': self.bank_mean,
                'position': list(self.position), 'forward': list(self.direction),
                'up': list(self.up), 'world_rows': matrix(self.position, self.direction, self.up)}


def probe_basis_from_elf(elf, coordinate, segment):
    """Execute original 001a9c9c..001a9d1c words with an independent scalar decoder.

    This is an IEEE float32 probe of the finite basis instruction window, not
    emulation of the R5900 or its rounding/exception/denormal behavior.
    No spline equation or weights() call is used here.
    """
    blob = Path(elf).read_bytes()
    if tngtool.sha(blob) != ELF_SHA: raise ContractError('unsupported ELF SHA256')
    g, f = [0]*32, [0.]*32
    g[7], f[1] = segment, f32(coordinate)
    for va in range(0x1a9c9c, 0x1a9d20, 4):
        w = struct.unpack_from('<I', blob, va-0xff000)[0]
        op, rs, rt, imm = w >> 26, (w >> 21)&31, (w >> 16)&31, w&65535
        fs, fd, fn = (w >> 11)&31, (w >> 6)&31, w&63
        if op == 15: g[rt] = imm << 16
        elif op == 9: g[rt] = (g[rs] + (imm if imm < 32768 else imm-65536)) & 0xffffffff
        elif op in (43, 57): pass  # Cache stores do not change basis registers.
        elif op == 17 and rs == 4: f[fs] = struct.unpack('<f', struct.pack('<I', g[rt]))[0]
        elif op == 17 and rs == 20 and fn == 32:
            raw = struct.unpack('<i', struct.pack('<f', f[fs]))[0]
            f[fd] = f32(raw)
        elif op == 17 and rs == 16:
            if fn == 0: f[fd] = add(f[fs], f[rt])
            elif fn == 1: f[fd] = sub(f[fs], f[rt])
            elif fn == 2: f[fd] = mul(f[fs], f[rt])
            elif fn == 7: f[fd] = -f[fs]
            else: raise ContractError('unexpected FPU probe operation')
        elif w == 0: pass
        else: raise ContractError('unexpected instruction in basis probe')
    return tuple(f[i] for i in (0, 6, 7, 10))


def ignored_output(path):
    path = Path(path).resolve()
    if not path.is_relative_to((ROOT/'data').resolve()):
        raise ContractError('proprietary diagnostic output must stay under ps2-research/data')
    return path


def diagnostic(identity, points, config, observers, *, initial_bank_flag, initial_time=0., initial_active=None):
    path = PathState(points, config)
    controller = Controller(path, initial_bank_flag, time=initial_time)
    if initial_active is not None: controller.active = initial_active
    return {'schema_version': 1, 'evidence': 'FLOAT32_RECONSTRUCTION',
            'runtime_validation': 'NOT_PERFORMED', 'identity': identity,
            'assumptions': {'initializer_bank_flag_0x128': initial_bank_flag,
                            'observer': 'explicit Car0/gaVehicleOutputData positions or absent',
                            'cadence': 'one controller invocation per step; no host scheduling claim',
                            'math': 'IEEE float32; host sqrt/sin/cos; not bit-exact PS2'},
            'config': config.__dict__, 'knots': path.knots,
            'closing_time': path.closing_time, 'duration': path.duration,
            'timeline': [dict(tick=i, **controller.step(p)) for i, p in enumerate(observers)]}


def write_svg(path, points, timeline):
    xy = [(p[0], p[2]) for p in points]
    lo = [min(p[i] for p in xy) for i in range(2)]
    hi = [max(p[i] for p in xy) for i in range(2)]
    scale = 700 / max(hi[0]-lo[0], hi[1]-lo[1], 1.)
    def coords(seq): return ' '.join(f'{20+(x-lo[0])*scale:.3f},{20+(z-lo[1])*scale:.3f}' for x,z in seq)
    track = [(r['position'][0], r['position'][2]) for r in timeline]
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="760" height="800" viewBox="0 0 760 800">'
           '<rect width="760" height="800" fill="white"/>'
           '<text x="20" y="770">Offline reconstruction; X/Z; NOT captured gameplay</text>'
           f'<polyline points="{coords(xy)}" fill="none" stroke="#999"/>'
           f'<polyline points="{coords(track)}" fill="none" stroke="#176ac1"/></svg>\n')
    path.write_text(svg, encoding='utf-8', newline='\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, required=True)
    ap.add_argument('--course', required=True)
    ap.add_argument('--egg', required=True)
    ap.add_argument('--occurrence', type=int, default=0)
    ap.add_argument('--steps', type=int, required=True)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--observer', type=float, nargs=3)
    group.add_argument('--observer-json', type=Path)
    group.add_argument('--observer-absent', action='store_true')
    ap.add_argument('--initial-bank-flag', type=int, choices=[0], required=True)
    ap.add_argument('--initial-time', type=float, default=0.)
    ap.add_argument('--initial-active', choices=['true', 'false'])
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--svg', type=Path)
    a = ap.parse_args()
    if not 1 <= a.steps <= 1000000: ap.error('steps must be between 1 and 1000000')
    output = ignored_output(a.output)
    svg = ignored_output(a.svg) if a.svg else None
    corpus = Corpus(a.input)
    case, points, config = corpus.case(a.course, a.egg, a.occurrence)
    if a.observer_json:
        observers = json.loads(a.observer_json.read_text(encoding='utf-8'))
        if not isinstance(observers, list) or len(observers) != a.steps:
            ap.error('observer JSON must contain one XYZ array or null per step')
    else: observers = [a.observer] * a.steps
    result = diagnostic(case, points, config, observers,
                        initial_bank_flag=a.initial_bank_flag, initial_time=a.initial_time,
                        initial_active=None if a.initial_active is None else a.initial_active == 'true')
    result['inputs'] = corpus.provenance
    output.parent.mkdir(parents=True, exist_ok=True)
    tngtool.write_json(output, result)
    if svg:
        svg.parent.mkdir(parents=True, exist_ok=True)
        write_svg(svg, points, result['timeline'])
    print(json.dumps({'output': str(output), 'steps': a.steps, 'duration': result['duration'],
                      'runtime_validation': 'NOT_PERFORMED'}))


if __name__ == '__main__': main()
