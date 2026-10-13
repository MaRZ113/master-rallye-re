#!/usr/bin/env python3
"""Package only bounded HUD1.1/rigid1.3 review sources; never build or deploy."""
from pathlib import Path
import hashlib
import importlib.util
import json

PORT = Path(__file__).resolve().parents[1]
ROOT = PORT.parents[1]

def main():
    spec = importlib.util.spec_from_file_location('handoff_helpers', PORT / 'overlay/package_reflection_handoff.py')
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    files = [Path(__file__), PORT / 'overlay/package_reflection_handoff.py',
             PORT / 'HUD11-RIGID13-HANDOFF.md']
    for phase in ('hud-port1.1', 'rigid-port1.3'):
        folder = PORT / 'docs' / phase
        if not (folder / 'final-report.md').is_file():
            raise RuntimeError(f'Missing phase closeout: {phase}')
        files.extend(p for p in sorted(folder.rglob('*')) if p.is_file() and p.suffix in ('.md', '.json', '.py', '.x32dbg'))
    # Explicit dependency closure for the existing read-only current-session join.
    for relative in ('tools/rigid_lifecycle_probe.py', 'docs/hud-port1/live-semantic-probe.py',
                     'docs/hud-port1/live-semantic-tests.py', 'docs/hud-port0/source-evidence.json',
                     'docs/hud-port1/semantic-evidence.json'):
        files.append(PORT / relative)
    members = {helper.relative_name(p): helper.read_required(p) for p in files}
    members['HANDOFF.md'] = (
        '# HUD-PORT1.1 / RIGID-PORT1.3 bounded decision handoff\n\n'
        'Review sources, compact instruction evidence and synthetic tests only. No DLL, game asset, '
        'full decompilation or raw process capture is included. Neither a HUD replacement nor a '
        'private physical object is enabled by this archive.\n\n'
        'Run phase *tests.py files with Python from the extracted repository layout. '
        'Synthetic tests require no game data. Live observation requires the exact original PC EXE, '
        'a fresh matching F10 capture and explicit user debugger participation. See phase runtime recipes. '
        'Frozen renderer and existing PS2 implementation were not modified. '
        'No rebuild is required for these external diagnostic sources.\n'
    ).encode()
    members['SHA256SUMS.txt'] = ''.join(f'{helper.sha256(data)}  {name}\n' for name, data in sorted(members.items())).encode()
    content = helper.archive_bytes(members)
    helper.verify_archive(content, members)
    if content != helper.archive_bytes(members):
        raise RuntimeError('Non-deterministic archive regeneration')
    output = PORT / 'dist/PS2-HUD-PORT1.1-RIGID-PORT1.3-handoff.zip'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    output.with_suffix('.zip.sha256').write_text(f'{digest}  {output.name}\n', encoding='utf-8')
    print(json.dumps({'path': str(output), 'sha256': digest, 'members': len(members),
                      'bytes': len(content), 'crc_sha256_determinism': 'PASS'}, sort_keys=True))

if __name__ == '__main__':
    main()
