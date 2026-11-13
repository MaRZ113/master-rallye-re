"""Brake Glow-ON module of the Vehicle SDK: author, fit, check, preview and install per-car brake lamps.

Commands (Python 3.11, Vehicle SDK via --sdk, e.g. ../master-rallye-re-vehicles):

  autospec  --host H --family F --out F.brake_lamps.json        default description from the OFF lenses
  check     --host H --spec S [--report R.json] [--heat H.png]   fit + penetration report (before/after heat map)
  preview   --host H --spec S --out A.png                        native D3D9 A/B sheet, BrakeGlow=0 and 1
  build     --source-host H --output-host O --spec S [S ...]     fresh sibling host with the compiled cars

The source host is never modified. ``build`` hardlinks Data.sma, copies everything else, then writes the
compiled car.dx, lamp textures, the MR-ADDON-LAMPS 3 registry and catalog hashes into MRMods/Vehicles/active
(and manager/base when present).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

FORESTER_PS2 = {'asset': '.assets/vehicles/FORESTER-CAR-SOURCE.ps2vehicle', 'core': 'root.15.0.0', 'glow': 'root.15.0.1'}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def resources(host: Path):
    from vehicle_presentation_fix import Resources
    return Resources(host)


def registry_rows(host: Path):
    p = host / 'MRMods/Vehicles/active/addon-brake-lamps.tsv'
    return p.read_text().splitlines()[1:] if p.is_file() else []


def ps2_assets(host: Path):
    on = next((host / p for p in ('PS2Vehicles/PS2BrakeOn.gxi', 'PS2Vehicles/PS2KiaBrakeOn.gxi') if (host / p).is_file()), None)
    glow = host / 'PS2Grass/PS2BrakeGlow.gxi'
    if on is None or not glow.is_file():
        raise SystemExit('host lacks PS2BrakeOn/PS2KiaBrakeOn.gxi or PS2BrakeGlow.gxi')
    return {'on': on.read_bytes(), 'glow': glow.read_bytes()}


def compile_one(host: Path, spec: dict):
    from brake_lamps import compile as C
    from brake_lamps.spec import normalise
    spec = normalise(spec)
    r = resources(host)
    fam = spec['family']
    raw = r.read(f'DataGx/Vehicles/{fam}/car.dx')
    donor = r.read('DataGx/Vehicles/Chevyblazer/car.dx')
    glow = r.read('DataGx/Vehicles/Chevyblazer/breaklightsonglow-tga.dxt')
    return raw, C.compile_car(raw, spec, donor_dx=donor, existing_rows=registry_rows(host), glow_texture=glow)


def cmd_autospec(a):
    from brake_lamps import autospec
    from brake_lamps.spec import dump
    raw = resources(a.host).read(f'DataGx/Vehicles/{a.family}/car.dx')
    spec = autospec.default_spec(raw, a.family, existing_rows=registry_rows(a.host), ps2_sources=FORESTER_PS2 if a.family == 'ForesterSTI' else None)
    dump(spec, a.out)
    print(a.out)


def check_report(host: Path, spec: dict, heat: Path | None):
    from brake_lamps import carmodel, report
    from brake_lamps.build import Frame
    raw, compiled = compile_one(host, spec)
    before = carmodel.load(raw, spec['family'])
    after = carmodel.load(compiled.car_dx, spec['family'])
    lamp_draws = {d.index for d in before.draws if d.role in ('on_core', 'on_glow')}
    if heat:
        rows = []
        for f in compiled.lamps:
            old_core = before.mesh('on_core'); old_glow = before.mesh('on_glow')
            # Existing layers of the same side/set, selected by proximity to this lens.
            from brake_lamps.geometry import Mesh
            def near(mesh):
                if not len(mesh.triangles):
                    return mesh
                c = mesh.corners().mean(axis=1)
                keep = (abs(c - f.frame.origin).max(axis=1) < max(float(abs(f.lens.positions - f.frame.origin).max()) * 2.5, .05))
                return Mesh(mesh.positions, mesh.triangles[keep])
            occ = compiled_occ = None
            from brake_lamps.geometry import merge
            occ = merge(d.mesh for d in before.draws if d.role in ('body', 'off_glass_on') and not d.alpha and d.index not in lamp_draws)
            pts = [m.positions[np.unique(m.triangles)] for m in (near(old_glow), near(old_core), f.glow.mesh()) if len(m.triangles)]
            q = f.frame.local(np.vstack(pts))[:, :2]
            bounds = (q.min(0), q.max(0))
            rows.append((f'{spec["family"]}\n{f.id} ({f.body})', [
                report.heat_panel([('halo', near(old_glow)), ('core', near(old_core))], occ, f.frame, title='before', bounds=bounds),
                report.heat_panel([('halo', f.glow.mesh()), ('core', f.core.mesh())], occ, f.frame, title='after', bounds=bounds)]))
        report.heat_sheet(rows, heat)
    return compiled


def cmd_check(a):
    from brake_lamps.spec import load
    out = []
    for s in a.spec:
        spec = load(s)
        heat = Path(a.heat_dir) / f'{spec["family"]}-heat.png' if a.heat_dir else None
        compiled = check_report(a.host, spec, heat)
        out.append(compiled.report)
        ok = all(l['fit_ok'] for l in compiled.report['lamps'])
        print(spec['family'], 'OK' if ok else 'BURIED', [(l['id'], l['offset_mm'], l['core']['normal_hidden'], l['halo']['normal_hidden']) for l in compiled.report['lamps']])
    if a.report:
        Path(a.report).write_text(json.dumps(out, indent=1) + '\n')


def ab_sheet(host: Path, spec: dict, out: Path, *, views=None):
    from PIL import Image, ImageDraw
    from brake_lamps import preview, carmodel
    raw, compiled = compile_one(host, spec)
    fam = spec['family']
    r = resources(host)
    rt = lambda n: r.read(f'DataGx/Vehicles/{fam}/{n}')
    assets = ps2_assets(host)
    car = carmodel.load(raw, fam)
    views = views or (('rear', (0, 0, -1)), ('yaw 30', (.5, 0, -.866)), ('high 25', (0, .42, -.906)))
    suppress_before, suppress_after = body_suppress(raw, registry_rows(host), fam), body_suppress(compiled.car_dx, compiled.rows, fam)
    W, H = 300, 225
    cols = (('BEFORE  BrakeGlow=0', raw, 'pc', suppress_before), ('AFTER  BrakeGlow=0', compiled.car_dx, 'pc', suppress_after),
            ('BEFORE  BrakeGlow=1', raw, 'ps2', suppress_before), ('AFTER  BrakeGlow=1', compiled.car_dx, 'ps2', suppress_after))
    sheet = Image.new('RGB', (W * len(cols) + 90, H * len(views) + 22), (16, 16, 18))
    d = ImageDraw.Draw(sheet)
    for x, c in enumerate(cols):
        d.text((90 + x * W + 6, 5), c[0], fill=(240, 240, 240))
    tmp = out.with_name('_tile.png')
    for y, (vname, dirn) in enumerate(views):
        d.text((6, 22 + y * H + H // 2), f'{fam}\n{vname}', fill=(240, 200, 120))
        cam = preview.lens_camera(car, +1, dirn, width=W, height=H)
        for x, (_, src, mode, sup) in enumerate(cols):
            preview.capture(preview.stage(src, rt, mode, ps2_assets=assets, suppress=sup), cam, tmp)
            sheet.paste(Image.open(tmp), (90 + x * W, 22 + y * H))
    tmp.unlink(missing_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return compiled


def body_suppress(raw: bytes, rows, family):
    """Draw indices of the PS2_BODY_ONLY set: the preview shows the PC body (car.dx), so its PC set is presented."""
    from master_rallye.dx import parse_dx_bytes
    from brake_lamps.compile import draw_identity
    want = {tuple(r.split()[2:6]) for r in rows if r.split()[0] == family and r.split()[-1] == 'PS2_BODY_ONLY'}
    if not want:
        return set()
    m = parse_dx_bytes(raw)
    return {d.draw_index for d in m.physical_draws if (str(d.local_vertex_max + 1), str(d.triangle_count), *draw_identity(m, d)) in want}


def cmd_preview(a):
    from brake_lamps.spec import load
    for s in a.spec:
        spec = load(s)
        out = Path(a.out_dir) / f'{spec["family"]}-ab.png'
        ab_sheet(a.host, spec, out)
        print(out)


def cmd_build(a):
    from brake_lamps.spec import load
    source, output = a.source_host.resolve(), a.output_host.resolve()
    if output.exists() or output == source or source in output.parents:
        raise SystemExit('choose a fresh sibling output host')
    specs = [load(s) for s in a.spec]
    results = [(spec, *compile_one(source, spec)) for spec in specs]
    output.mkdir(parents=True)
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
    r = resources(source)
    report = {'schema': 'mr-brake-lamps-build/1', 'source_host': str(source), 'gameplay_tested': False, 'cars': []}
    for root in (output / 'MRMods/Vehicles/active', output / 'MRMods/Vehicles/manager/base'):
        registry = root / 'addon-brake-lamps.tsv'
        if not registry.is_file():
            continue
        lines = registry.read_text().splitlines()
        if lines[0] not in ('MR-ADDON-LAMPS 1', 'MR-ADDON-LAMPS 2', 'MR-ADDON-LAMPS 3'):
            raise SystemExit(f'unknown registry {lines[0]}')
        rows = [l + (' ANY_MODEL' if lines[0].endswith(' 1') else '') for l in lines[1:] if l.strip()]
        families = {spec['family'] for spec in specs}
        rows = [l for l in rows if l.split()[0] not in families]
        for spec, raw, c in results:
            fam = spec['family']
            base = root / 'resources/DataGx/Vehicles' / fam
            base.mkdir(parents=True, exist_ok=True)
            (base / 'car.dx').write_bytes(c.car_dx)
            (base / 'breaklightson-tga.dxt').write_bytes(r.read('DataGx/Vehicles/Chevyblazer/breaklightson-tga.dxt'))
            for name, data in c.textures.items():
                (base / name).write_bytes(data)
            rows += c.rows
        registry.write_text('MR-ADDON-LAMPS 3\n' + '\n'.join(rows) + '\n', encoding='ascii')
        cat = root / 'catalog.json'
        if cat.is_file():
            data = json.loads(cat.read_text())
            data['resources'] = [{'path': f.relative_to(root / 'resources').as_posix(), 'size': f.stat().st_size, 'sha256': sha(f.read_bytes())}
                                 for f in sorted((root / 'resources').rglob('*')) if f.is_file()]
            cat.write_text(json.dumps(data, indent=1) + '\n')
    for spec, raw, c in results:
        report['cars'].append({**c.report, 'spec': spec})
    (output / 'brake-lamps-build.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps([{'family': c['family'], 'rows': c['rows'], 'fit_ok': [l['fit_ok'] for l in c['lamps']]} for c in report['cars']], indent=1))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--sdk', type=Path, default=TOOLS.parents[1] / 'master-rallye-re-vehicles')
    sub = p.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('autospec'); s.add_argument('--host', type=Path, required=True); s.add_argument('--family', required=True); s.add_argument('--out', type=Path, required=True)
    s = sub.add_parser('check'); s.add_argument('--host', type=Path, required=True); s.add_argument('--spec', nargs='+', required=True); s.add_argument('--report'); s.add_argument('--heat-dir')
    s = sub.add_parser('preview'); s.add_argument('--host', type=Path, required=True); s.add_argument('--spec', nargs='+', required=True); s.add_argument('--out-dir', required=True)
    s = sub.add_parser('build'); s.add_argument('--source-host', type=Path, required=True); s.add_argument('--output-host', type=Path, required=True); s.add_argument('--spec', nargs='+', required=True)
    a = p.parse_args()
    sys.path.insert(0, str(a.sdk.resolve() / 'src'))
    {'autospec': cmd_autospec, 'check': cmd_check, 'preview': cmd_preview, 'build': cmd_build}[a.cmd](a)


if __name__ == '__main__':
    main()
