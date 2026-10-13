"""Verify and package the full-coverage source/test release, never private assets."""
from pathlib import Path
import importlib.util
import json
import subprocess

PORT = Path(__file__).resolve().parents[1]
ROOT = PORT.parents[1]


def main():
    spec = importlib.util.spec_from_file_location('verified_handoff', PORT/'overlay/package_reflection_handoff.py')
    h = importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
    report = json.loads((PORT/'dist/current/build-report.json').read_text())
    lock = json.loads((PORT/'overlay/baseline-lock.json').read_text())
    h.verify_build_inputs(report, lock)
    members = {}
    allowed = {'.py', '.cpp', '.hpp', '.json', '.md', '.patch', '.x32dbg', '.ini'}
    for name in ('renderer', 'tests', 'tools', 'overlay', 'docs'):
        for path in sorted((PORT/name).rglob('*')):
            if path.is_file() and path.suffix in allowed and '__pycache__' not in path.parts:
                members[h.relative_name(path)] = h.read_required(path)
    for name in ('.gitignore', '.gitattributes', 'PS2Port.ini.example'):
        path = PORT/name;members[h.relative_name(path)] = h.read_required(path)
    for path in sorted((ROOT/'ps2-research/tools').glob('*.py')):
        members[h.relative_name(path)] = h.read_required(path)
    for folder in ('rigid1', 'grass1', 'grass2', 'water1', 'refl1', 'geom1', 'cdelta1'):
        for path in sorted((ROOT/'ps2-research'/folder).glob('*.json')):
            if path.stat().st_size < 1024*1024:
                members[h.relative_name(path)] = h.read_required(path)
    members['build-report.json'] = (PORT/'dist/current/build-report.json').read_bytes()
    members['release-provenance.json'] = json.dumps({
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'frozen_renderer_tree': report['renderer_tree'],
        'build_report_source_head': report['current_head'],
        'source_and_patch_hashes_verified_against_build': True,
        'original_assets_packaged': False,
    }, indent=2).encode()
    for variant in ('baseline', 'ps2-enabled'):
        members[f'artifacts/{variant}/d3d8.dll'] = h.verified_dll(report, variant)
    members['HANDOFF.md'] = (PORT/'docs/full-coverage/handoff.md').read_bytes()
    members['SHA256SUMS.txt'] = ''.join(f'{h.sha256(v)}  {k}\n' for k, v in sorted(members.items())).encode()
    data = h.archive_bytes(members);h.verify_archive(data, members)
    if data != h.archive_bytes(members):
        raise RuntimeError('Archive determinism failed')
    output = PORT/'dist/PS2-VISUAL-PARITY-FULL-COVERAGE-handoff.zip'
    output.write_bytes(data)
    output.with_suffix('.zip.sha256').write_text(f'{h.sha256(data)}  {output.name}\n')
    print(json.dumps({'path': str(output), 'sha256': h.sha256(data), 'bytes': len(data),
                      'members': len(members), 'crc_sha256_determinism': 'PASS'}))


if __name__ == '__main__':
    main()
