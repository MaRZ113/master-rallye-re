"""Build ignored native replay fixture only after strict real Kia trio audit."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import audit_trio as audit

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]
OUTPUT = PORT / '.assets/vehicles/kia-damage-replay.bin'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('captures', type=Path, nargs=3)
    args = parser.parse_args()
    result = audit.audit(args.captures)
    audit.require(result['correspondence_pass'] and result['damage_deformation_observed'],
                  'Actual coherent damage evidence is required for fixture')
    profiles = json.loads((HERE / 'kia-source-correspondence.json').read_text())['source_profiles']
    captures = [audit.read_capture(path) for path in args.captures]
    healthy = audit.join_sources(captures[0], profiles)
    output = bytearray(b'KIADMG01' + struct.pack('<I', 3))
    manifest = []
    for capture in captures:
        meta = capture['metadata']
        joined = healthy if capture is captures[0] else audit.join_sources(capture, profiles, healthy)
        original = next(path for path in args.captures if path.name == capture['path']).read_bytes()
        metadata_size, raw_size = struct.unpack_from('<II', original, 8)
        raw = original[16 + metadata_size:]
        audit.require(len(raw) == raw_size, 'Original raw length drift')
        output.extend(struct.pack('<5I', int(meta['private_tree']), meta['instance'], meta['packet'], meta['model'], 26))
        for slot, row in enumerate(joined):
            output.extend(struct.pack('<11I', slot, row['fvf'], row['stride'], row['vertices'],
                row['triangles'], row['index_format'], row['min'], row['vertex_bytes'],
                row['index_bytes'], row['material_vector'], row['material']))
            begin = row['offset']
            end = begin + row['vertex_bytes'] + row['index_bytes']
            output.extend(raw[begin:end])
        manifest.append(dict(capture=capture['path'], sha256=capture['sha256'], frame=meta['frame'],
                             private_tree=meta['private_tree'], actual_native_sources=26,
                             synthetic_source_rows=0))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(output)
    summary = dict(schema=1, filename=OUTPUT.name, bytes=len(output),
        sha256=hashlib.sha256(output).hexdigest(), fixture_format='KIADMG01',
        captures=manifest, evidence='ALL78_ROWS_ARE_ACTUAL_CAPTURED_NATIVE_BYTES',
        original_exe_sha256=audit.EXE,
        runtime_grant=False, note='Ignored proprietary native buffers; never commit fixture binary')
    (HERE / 'replay-fixture-manifest.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(summary['filename'], summary['bytes'], summary['sha256'])


if __name__ == '__main__':
    main()
