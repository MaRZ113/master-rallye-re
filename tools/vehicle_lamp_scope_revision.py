"""Restore independent addon lamps while preserving the owner-tested fix02 host.

Creates a fresh sibling candidate; never updates either input host in place.
Only the immutable Data.sma archive is hardlinked. All mutable files are copied.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
from vehicle_presentation_fix import Resources, sha

NATIVE = ('ImprezaProto', 'LancerEvo4', 'Evo2FourRunner')


def finalize(output):
    root = Path(__file__).resolve().parents[1]
    (output/'READ_ME.md').write_text((root/'docs/vehicle-manager/LAMPS_FIX_03.md').read_text())
    launcher = output.parent / ('Launch-'+output.name.removeprefix('host-')+'.cmd')
    launcher.write_text('@echo off\nrem Preserve PS2Port.ini; no glow preset is written.\npushd "%~dp0'+output.name+'"\nif errorlevel 1 exit /b 1\nstart "" "MRallye.exe"\npopd\n', encoding='ascii')
    sources = ('tools/vehicle_lamp_scope_revision.py', 'tools/vehicle_lamp_authoring.py',
               'tools/verify_vehicle_lamps.py', 'tools/test_vehicle_lamp_native.py',
               'tests/addon_lamp_registry_tests.cpp', 'tests/addon_lamp_native_tests.cpp',
               'docs/vehicle-manager/LAMPS_FIX_03.md')
    binaries = ('MRallye.exe', 'dinput8.dll', 'd3d8.dll',
                'MRMods/Vehicles/active/roster.mrvr', 'MRMods/Vehicles/active/catalog.json',
                'MRMods/Vehicles/active/addon-brake-lamps.tsv', 'PS2Port.ini')
    manifest = {'schema': 'mr-lamp-scope-build/1', 'gameplay_tested': False,
                'parent_owner_acceptance': 'fix02 lamps and Mercedes glass',
                'binary_policy': 'EXE, DLLs and native MRVR transaction copied byte-identically from fix02',
                'abi_unchanged': ['MRVR v1', 'RVP1', 'MRVC v1', 'MR-ADDON-LAMPS 1'],
                'source_files': [{'path': s, 'sha256': sha((root/s).read_bytes())} for s in sources],
                'candidate_files': [{'path': s, 'sha256': sha((output/s).read_bytes())} for s in binaries],
                'launcher': {'path': str(launcher), 'sha256': sha(launcher.read_bytes()), 'writes_config': False}}
    (output/'source-build-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')


def build(source, original, output):
    source, original, output = (p.resolve() for p in (source, original, output))
    if output.exists() or any(p == output or p in output.parents or output in p.parents for p in (source, original)):
        raise ValueError('Choose a fresh sibling output directory')
    active_rel = Path('MRMods/Vehicles/active')
    original_resources = Resources(original)
    restorations = {}
    for family in NATIVE:
        for name in ('car.dx', 'breaklightson-tga.dxt', 'breaklightsonglow-tga.dxt'):
            rel = f'DataGx/Vehicles/{family}/{name}'
            try:
                restorations[rel] = original_resources.read(rel)
            except KeyError:
                if name == 'car.dx':
                    raise
                restorations[rel] = None
    for p in source.rglob('*'):
        rel = p.relative_to(source)
        if 'active.prev' in rel.parts or 'logs' in rel.parts:
            continue
        dst = output / rel
        if p.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if rel == Path('Data.sma'):
                os.link(p, dst)
            else:
                shutil.copy2(p, dst)
    active = output / active_rel
    for rel, data in restorations.items():
        p = active / 'resources' / rel
        if data is None:
            if p.exists():
                p.unlink()
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
    registry = active / 'addon-brake-lamps.tsv'
    lines = registry.read_text().splitlines()
    assert lines[0] == 'MR-ADDON-LAMPS 1'
    retained = [line for line in lines[1:] if line.split()[0] not in NATIVE]
    assert len(lines[1:]) - len(retained) == 2 * len(NATIVE)
    registry.write_text(lines[0]+'\n'+'\n'.join(retained)+'\n', encoding='ascii')
    historical = output / 'provenance/lamps-fix-02'
    historical.mkdir(parents=True, exist_ok=True)
    for name in ('source-build-manifest.json', 'vehicle-lamp-report.json', 'vehicle-lamp-validation.json', 'READ_ME.md'):
        p = output / name
        if p.is_file():
            shutil.move(str(p), str(historical / name))
    report = json.loads((historical / 'vehicle-lamp-report.json').read_text())
    report['families'] = [r for r in report['families'] if r['family'] not in NATIVE]
    report.update(preserve_native_families=list(NATIVE), registry_rows=len(retained), gameplay_tested=False,
                  accepted_parent_host=str(source), accepted_parent_owner_confirmed=['glass breakage', 'brake lamps'],
                  restoration_source=str(original))
    (output / 'vehicle-lamp-report.json').write_text(json.dumps(report, indent=2)+'\n')
    catalog = json.loads((active / 'catalog.json').read_text())
    catalog.update(label='Roster V4 lamps fix 03 - demo scope',
                   active_derivation={'tool': 'tools/vehicle_lamp_scope_revision.py', 'source_host': str(source),
                                      'original_lamps_host': str(original), 'native_transaction_unchanged': True})
    catalog['resources'] = [{'path': p.relative_to(active/'resources').as_posix(), 'size': p.stat().st_size,
                             'sha256': sha(p.read_bytes())} for p in sorted((active/'resources').rglob('*')) if p.is_file()]
    (active / 'catalog.json').write_text(json.dumps(catalog, indent=2)+'\n')
    # Compare every inherited file, including configuration and user saves.
    changed = {active_rel/'resources'/rel for rel in restorations}
    changed |= {active_rel/'catalog.json', active_rel/'addon-brake-lamps.tsv',
                Path('source-build-manifest.json'), Path('vehicle-lamp-report.json'),
                Path('vehicle-lamp-validation.json'), Path('READ_ME.md')}
    preserved = 0
    for p in source.rglob('*'):
        rel = p.relative_to(source)
        if not p.is_file() or rel in changed or 'active.prev' in rel.parts or 'logs' in rel.parts:
            continue
        if rel == Path('Data.sma'):
            assert os.path.samefile(p, output/rel)
        else:
            assert sha(p.read_bytes()) == sha((output/rel).read_bytes()), str(rel)
        preserved += 1
    effective = Resources(output)
    for rel, data in restorations.items():
        if data is not None:
            assert effective.read(rel) == data
        else:
            try:
                effective.read(rel)
            except KeyError:
                pass
            else:
                raise AssertionError('Unexpected inherited texture: '+rel)
    result = {'schema': 'mr-lamp-scope-revision/1', 'status': 'OFFLINE_VALIDATED', 'gameplay_tested': False,
              'source_host': str(source), 'restoration_source': str(original), 'native_families': list(NATIVE),
              'demo_lamp_layers': len(retained), 'other_files_identical': preserved,
              'restored_files': {rel: sha(data) if data is not None else None for rel, data in restorations.items()},
              'roster_sha256': sha((active/'roster.mrvr').read_bytes()),
              'renderer_sha256': sha((output/'d3d8.dll').read_bytes()),
              'config': {'file': 'PS2Port.ini', 'section': 'Vehicles', 'key': 'BrakeGlow',
                         '0': 'Native lamps', '1': 'PS2 lamps for registered demo roles', 'restart_required': True}}
    (output / 'lamp-scope-validation.json').write_text(json.dumps(result, indent=2)+'\n')
    finalize(output)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-host', type=Path, required=True)
    p.add_argument('--original-host', type=Path, required=True)
    p.add_argument('--output-host', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(build(a.source_host, a.original_host, a.output_host), indent=2))
