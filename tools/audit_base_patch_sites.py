"""Static map of every known in-memory patch site of the integration base.

Owners: renderer d3d8 (source-declared sites), unified dinput8 loader
(Randomizer G1 plan, Ghost/difficulty plan, Extra Options customization,
Menu Builder), the bound vehicle runtime (SDK native-patch-manifest) and the
planned CLASS-T4 layer. Every site's original bytes are read from the retail
PE; when a source declares expected bytes they must match. Overlapping byte
ranges between owners are reported. This is a static range/preimage audit,
not proof of runtime install order or semantic compatibility.
"""
from __future__ import annotations
import argparse, hashlib, json, re, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'ps2-research/pc-port/.staging/ps2-enabled'
RENDERER = STAGE / 'modernization/renderer'
PORT = STAGE / 'ps2-research/pc-port/renderer'
NATIVE = ROOT / 'src/native/rmod1'
BASE = 0x400000


class Image:
    def __init__(self, raw):
        self.raw = raw
        pe = struct.unpack_from('<I', raw, 0x3c)[0]
        count, opt = struct.unpack_from('<H', raw, pe + 6)[0], struct.unpack_from('<H', raw, pe + 20)[0]
        self.sections = [struct.unpack_from('<IIII', raw, pe + 24 + opt + 40 * i + 8)[1:4] for i in range(count)]
        self.sections = [(va, size, off) for va, size, off in self.sections]

    def read(self, va, n):
        rva = va - BASE
        for sva, size, off in self.sections:
            if sva <= rva and rva + n <= sva + size:
                return self.raw[off + rva - sva:off + rva - sva + n]
        raise ValueError(f'unmapped {va:#x}/{n}')


def site(image, owner, name, va, n, expected=None, optional=False):
    actual = image.read(va, n)
    status = 'OK' if expected is None or actual == bytes.fromhex(expected) else 'PREIMAGE_MISMATCH'
    return {'owner': owner, 'name': name, 'va': va, 'size': n, 'original_hex': actual.hex(),
            'expected_hex': expected, 'status': status, 'optional': optional}


def call_bytes(va, target): return (b'\xe8' + struct.pack('<i', target - va - 5)).hex()


def renderer_sites(img):
    rows = [site(img, 'renderer', n, va, size, exp) for n, va, size, exp in [
        ('sky-read', 0x4b123c, 5, 'e81f550200'), ('sky-used', 0x4b1374, 5, 'e8e7530200'),
        ('opaque-queue-flush', 0x56bab8, 5, 'e8536dffff'), ('FOV-submit', 0x6532dd, 5, 'e89e63ebff'),
        ('camera-completion', 0x5b0166, 5, 'e8152f0a00'), ('attract-loading', 0x464f69, 5, '68841f6b00'),
        ('menu-freeze', 0x5b015c, 2, '7511'), ('UI-packet', 0x56d110, 6, '81ec08010000')]]
    src = (RENDERER / 'src/race_observer.cpp').read_text()
    for kind, n, va, target in re.findall(r'(call|virtual)_site\((\d+),(0x[0-9a-f]+),(0x[0-9a-f]+),', src):
        va, target = int(va, 16), int(target, 16)
        exp = call_bytes(va, target) if kind == 'call' else struct.pack('<I', target).hex()
        rows.append(site(img, 'renderer', 'race-observer-' + n, va, len(bytes.fromhex(exp)), exp))
    pause = (PORT / 'pause_settings.hpp').read_text()
    for name, va, target in re.findall(r'CallSite k\w+\{"([^"]+)",(0x[0-9a-f]+),(0x[0-9a-f]+)\}', pause):
        va, target = int(va, 16), int(target, 16)
        rows.append(site(img, 'renderer', 'pause-' + name, va, 5, call_bytes(va, target)))
    audio = (PORT / 'ps2_audio_options.hpp').read_text()
    for name, va, size, before in re.findall(r'BytePatch k\w+\{"([^"]+)",(0x[0-9a-f]+),(\d),\{([^}]*)\}', audio):
        size = int(size); exp = bytes(int(x, 16) for x in before.split(',')[:size]).hex()
        rows.append(site(img, 'renderer', 'audio-' + name, int(va, 16), size, exp))
    rows.append(site(img, 'renderer', 'broker-null-stringlist', 0x60201e, 6))
    rows.append(site(img, 'renderer', 'broker-null-xmldata', 0x602153, 7))
    return rows


def loader_sites(img, core):
    sys.path.insert(0, str(ROOT / 'tools'))
    from r_mod1_native_plan import build_plan, public_plan
    plan = public_plan(build_plan(img.raw, core, checkpoint='g1'))
    rows = [site(img, 'loader:randomizer', r['id'], BASE + r['rva'], len(bytes.fromhex(r['expected_original_hex'])), r['expected_original_hex'])
            for r in plan['operations']]
    ghost = (NATIVE / 'extra_ghost_plan.hpp').read_text()
    rows += [site(img, 'loader:ghost', n, int(va, 16), len(bytes.fromhex(b)), b)
             for n, va, b in re.findall(r'\{"([^"]+)", \d+u, (0x[0-9a-f]+)u, "([0-9a-f]+)"', ghost)]
    extra = (NATIVE / 'extra_options_runtime.cpp').read_text()
    c = {k: int(v, 16) for k, v in re.findall(r'(k\w+)=(0x[0-9a-f]+)', extra)}
    for slot, target in [('kGeneralInitSlot', 'kGeneralInit'), ('kGeneralTickSlot', 'kGeneralTick'),
                         ('kSelectInitSlot', 'kSelectInit'), ('kSelectTickSlot', 'kSelectTick')]:
        rows.append(site(img, 'loader:extra-options', slot, c[slot], 4, struct.pack('<I', c[target]).hex()))
    for call, target in [('kGeneralCommandCall', 'kCommand'), ('kWheelCall', 'kWheel'), ('kSelectScrollCall', 'kSelectScroll')]:
        rows.append(site(img, 'loader:extra-options', call, c[call], 5, call_bytes(c[call], c[target])))
    rows += [site(img, 'loader:menu-builder', 'vfs-createfile', 0x64d573, 6, 'ff15e0f16800'),
             site(img, 'loader:menu-builder', 'screen-name', 0x45d865, 5, call_bytes(0x45d865, 0x449cf0)),
             site(img, 'loader:menu-builder', 'host-init-slot', 0x690540, 4, struct.pack('<I', 0x462ab0).hex())]
    return rows


def sdk_sites(img, manifest):
    m = json.loads(Path(manifest).read_text())
    return [site(img, 'vehicles:sdk-runtime', r['name'], BASE + r['rva'], len(bytes.fromhex(r['expected_original_bytes'])), r['expected_original_bytes'])
            for r in m['operations'] if r.get('rva') is not None]


def t4_sites(img, source=ROOT.parent / 'master-rallye-re-vclass/tools/sdk_capacity_native.py'):
    """Planned CLASS-T4 retail sites, parsed from the T4 branch source (not imported)."""
    if not source.is_file():
        return []
    text = source.read_text(encoding='utf-8')
    block = text[text.index('T4_DISPLACEMENTS = ('):text.index('T4_CTOR_TAIL')]
    rows = [site(img, 'planned:class-t4', f'object-size-{va:x}', va, 1, '34')
            for va in (int(v, 16) for v in re.findall(r'0x[0-9A-F]{6}', text[text.index('T4_ALLOCATIONS'):text.index('# (instruction VA')]))]
    for va, pos in re.findall(r'\((0x[0-9A-F]+), (\d)\)', block):
        va = int(va, 16)
        if va < 0x68e000:   # cave sites belong to the SDK runtime and are checked there
            rows.append(site(img, 'planned:class-t4', f'field-{va:x}', va + int(pos), 1))
    rows.append(site(img, 'planned:class-t4', 'class-list-hook', 0x481152, 5))
    return rows


def overlaps(rows):
    out = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if a['owner'] == b['owner']: continue
            lo, hi = max(a['va'], b['va']), min(a['va'] + a['size'], b['va'] + b['size'])
            if lo < hi:
                out.append({'a': f"{a['owner']}/{a['name']}", 'b': f"{b['owner']}/{b['name']}", 'va': f'{lo:#x}', 'bytes': hi - lo})
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--retail', type=Path, default=ROOT.parent / 'corpora/retail/MRallye.exe')
    p.add_argument('--core', type=Path, required=True, help='MRallyeRandomizerRuntime.dll of the loader build')
    p.add_argument('--sdk-manifest', type=Path, required=True, help='native-patch-manifest.json of the bound vehicle runtime')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    img = Image(a.retail.read_bytes())
    rows = renderer_sites(img) + loader_sites(img, a.core.read_bytes()) + sdk_sites(img, a.sdk_manifest) + t4_sites(img)
    counts = {}
    for r in rows: counts[r['owner']] = counts.get(r['owner'], 0) + 1
    report = {'schema': 'mr-base-patch-sites/1', 'exe_sha256': hashlib.sha256(img.raw).hexdigest(), 'counts': counts,
              'preimage_mismatches': [r for r in rows if r['status'] != 'OK'], 'overlaps': overlaps(rows), 'sites': rows}
    a.output.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps({'counts': counts, 'mismatches': len(report['preimage_mismatches']), 'overlaps': report['overlaps']}, indent=1))


if __name__ == '__main__':
    main()
