"""Replay bounded original Dakar2 CPU material-state routines, never the game.

The original executable is owner-local and hash-pinned. Outputs contain hashes
and state observations only; no executable/shader payload is redistributed.
Requires the existing optional Unicorn Python dependency for CPU replay.
"""
from pathlib import Path
import argparse
import struct
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from master_rallye import universal_vehicle_scene as u
from master_rallye.source_adapters.dakar2 import PINS
from master_rallye.source_adapters.dakar2_disc import FileReader, xdvdfs
from master_rallye.source_adapters.dakar2_coverage import scene_coverage


def original_image(image):
    reader = FileReader(image)
    row = next(r for r in xdvdfs(reader, 0x18300000) if r['path'].lower() == 'default.xbe')
    data = reader.read(row['offset'], row['bytes'])
    if u.sha(data) != PINS['default.xbe']:
        raise ValueError('Unqualified original Xbox executable')
    base = struct.unpack_from('<I', data, 0x104)[0]
    count, table = struct.unpack_from('<II', data, 0x11c)
    if not 1 <= count <= 32:
        raise ValueError('Original XBE section budget')
    sections = [struct.unpack_from('<5I', data, table-base+i*56) for i in range(count)]
    def original(va, size):
        matches = [r for r in sections if r[1] <= va and va+size <= r[1]+r[4]]
        if len(matches) != 1:
            raise ValueError('Ambiguous original byte mapping')
        section = matches[0]; offset = section[3]+va-section[1]
        raw = data[offset:offset+size]
        if len(raw) != size:
            raise ValueError('Truncated original byte mapping')
        return raw
    return data, sections, original


def emulator(data, sections):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    cpu = Uc(UC_ARCH_X86, UC_MODE_32)
    cpu.mem_map(0x10000, 0x270000)
    for _, va, virtual_size, offset, size in sections:
        if va < 0x10000 or va+max(virtual_size, size) > 0x280000:
            raise ValueError('Original CPU mapping budget')
        cpu.mem_write(va, data[offset:offset+size])
    for va, size in [(0x400000, 0x50000), (0x500000, 0x20000),
                     (0x600000, 0x20000), (0x700000, 0x1000)]:
        cpu.mem_map(va, size)
    return cpu


def replay_upload(data, sections, original):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP
    results = []
    for definition in (0x192058, 0x192148):
        cpu = emulator(data, sections)
        def write(at, value):cpu.mem_write(at, struct.pack('<I', value))
        write(0xf0808, 0x400000); write(0x400000, 0x500000)
        write(0x400004, 0x510000); write(0x400008, 0)
        # Previous shader is non-null. Overflow helpers are forbidden, not stubbed.
        write(0x40036c, 0x400900); write(0x400808, definition)
        write(0x610000, 0x700000); write(0x610004, 0x400800)
        cpu.reg_write(UC_X86_REG_ESP, 0x610000); steps = [0]
        def hook(cpu, address, _size, _context):
            steps[0] += 1
            if address in (0xe5a50, 0xe46e0, 0xe4040):
                raise ValueError('Unexpected original pixel-upload helper dependency')
        cpu.hook_add(UC_HOOK_CODE, hook)
        cpu.emu_start(0xe6250, 0x700000, count=20000)
        if cpu.reg_read(UC_X86_REG_EIP) != 0x700000:
            raise ValueError('Original CPU pixel upload did not return within budget')
        end = struct.unpack('<I', cpu.mem_read(0x400000, 4))[0]
        if not 0x500000 <= end <= 0x501000:
            raise ValueError('Original push-buffer output budget')
        push = bytes(cpu.mem_read(0x500000, end-0x500000))
        words = list(struct.unpack('<'+str(len(push)//4)+'I', push))
        at = words.index(0x800a60)
        constants = words[at+1:at+17]
        if constants != list(struct.unpack('<16I', original(definition+40, 64))):
            raise ValueError('Original pixel upload did not preserve embedded constants')
        results.append({'definition_va': definition, 'definition_sha256': u.sha(original(definition, 240)),
                        'instruction_count': steps[0], 'push_bytes': len(push), 'push_sha256': u.sha(push),
                        'constant0_stage1_argb': constants[1], 'constant0_stage1_alpha': (constants[1]>>24)/255,
                        'constants_match_definition': True})
    return {'scope': 'Original e6250 CPU upload with explicit prior shader and buffer; no observed game/GPU state or later-update claim',
            'results': results, 'runtime': 'NOT TESTED'}


def replay_alpha(data, sections, *, reference=100):
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP
    cpu = emulator(data, sections)
    def write(at, value):cpu.mem_write(at, struct.pack('<I', value))
    def read(at):return struct.unpack('<I', cpu.mem_read(at, 4))[0]
    nodes = [(4, 0), (0, 0x08000000), (1, 0x08000000), (0, 0x08000000), (0, 0x18000000)]
    write(0x400004, len(nodes)); write(0x400050, 0x401000); write(0x18eab4, reference)
    for i, (kind, flags) in enumerate(nodes):
        at = 0x401000+i*0x290
        write(at, kind); write(at+0x18, 0x410000+i*0x100); write(at+0x28, flags)
    for state, value in [(0x3a, 0x207), (0x3d, 0), (0x3c, 0)]:
        write(0x2397f4+state*4, value)
    for i, value in enumerate((0x700000, 0x400000, 0, 0, 0)):
        write(0x610000+i*4, value)
    cpu.reg_write(UC_X86_REG_ESP, 0x610000)
    draws = []; steps = [0]
    skipped = {0x88130, 0x88450, 0x88eb0, 0x66020, 0x88170}
    def hook(cpu, address, _size, _context):
        steps[0] += 1
        if address in skipped or address == 0x8b590:
            stack = cpu.reg_read(UC_X86_REG_ESP)
            if address == 0x8b590:
                draws.append({'node': (read(stack+4)-0x410000)//0x100,
                              'enabled': read(0x2397f4+0x3c*4),
                              'comparison': read(0x2397f4+0x3a*4),
                              'reference': read(0x2397f4+0x3d*4)})
            cpu.reg_write(UC_X86_REG_EAX, 0)
            cpu.reg_write(UC_X86_REG_EIP, read(stack))
            cpu.reg_write(UC_X86_REG_ESP, stack+4)
    cpu.hook_add(UC_HOOK_CODE, hook)
    cpu.emu_start(0x46ae0, 0x700000, count=50000)
    expected = [(0, 0x207, 0), (0, 0x207, 0), (1, 0x204, reference),
                (0, 0x207, 0), (1, 0x204, reference)]
    observed = [(r['enabled'], r['comparison'], r['reference']) for r in draws]
    if (cpu.reg_read(UC_X86_REG_EIP) != 0x700000 or
            [r['node'] for r in draws] != list(range(5)) or observed != expected):
        raise ValueError('Original CPU alpha schedule differs from source rule')
    return {'draws': draws, 'instruction_count': steps[0], 'effective_reference_supplied': reference,
            'stubbed_helpers': sorted(skipped | {0x8b590}),
            'scope': 'Original46ae0/enable/disable/compare/ref CPU, synthetic nodes; matrix/draw/count helpers stubbed; not Xbox GPU equivalence'}


def run(image, scenes, output):
    image = Path(image).absolute(); scenes = [Path(p).absolute() for p in scenes]
    loaded = [u.load_scene(p) for p in scenes]
    protected = [image.parent, *[p.parent for p in scenes]]
    for scene in loaded:protected.extend(map(Path, scene['source'].get('protected_roots', [])))
    output = u.output_directory(Path(output).absolute(), protected)
    if output.exists():raise ValueError('Fresh coverage output required')
    data, sections, original = original_image(image)
    functions = {}
    for name, va, size in [('vehicle_alpha_schedule', 0x46ae0, 0x2b6),
                           ('hir_kind_copy', 0x46da0, 0x120),
                           ('alpha_compare_ref', 0x86920, 0x80),
                           ('stage_bind', 0x8aed0, 0x190),
                           ('texture_loader', 0x8ac20, 0xb0),
                           ('pixel_upload', 0xe6250, 0x1f3)]:
        functions[name] = {'va': va, 'bytes': size, 'sha256': u.sha(original(va, size))}
    report = {'schema': 'dakar2-original-coverage-probe/1', 'original_xbe_sha256': u.sha(data),
              'functions': functions, 'embedded_alpha_reference': struct.unpack('<I', original(0x18eab4, 4))[0],
              'pixel_upload': replay_upload(data, sections, original),
              'alpha_schedule': [replay_alpha(data, sections, reference=r) for r in (100, 10)],
              'runtime': 'NOT TESTED', 'native_fixture_allowed': False}
    output.mkdir(parents=True)
    for path, scene in zip(scenes, loaded):
        row = scene_coverage(scene, path.parent, incoming_enabled=False,
                             effective_reference=report['embedded_alpha_reference'])
        if row != scene_coverage(scene, path.parent, incoming_enabled=False,
                                  effective_reference=report['embedded_alpha_reference']):
            raise ValueError('Nondeterministic original coverage report')
        row['source_scene_sha256'] = u.sha(u.read_bounded(path, u.MAX_JSON_BYTES))
        (output/(scene['source']['catalog']+'-coverage.json')).write_bytes(u.canonical(row))
    (output/'original-coverage-probe.json').write_bytes(u.canonical(report))
    return {'original_xbe_sha256': u.sha(data), 'source_scenes': len(scenes),
            'cpu_uploads': 2, 'cpu_alpha_schedules': 2, 'runtime': 'NOT TESTED'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--xbox', type=Path, required=True)
    parser.add_argument('--scene', type=Path, action='append', default=[])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); print(run(args.xbox, args.scene, args.output))
