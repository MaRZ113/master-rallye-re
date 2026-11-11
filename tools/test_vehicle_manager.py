"""Vehicle Manager end-to-end: identity apply, remove/order/package edit, restore, stock (offline, no game)."""
import hashlib, json, os, shutil, struct, sys
from pathlib import Path
import argparse
BASE = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser(description='Vehicle Manager end-to-end check on a private copy of a roster host (never the source).')
ap.add_argument('--source-host', type=Path, required=True)
ap.add_argument('--work-host', type=Path, required=True)
args = ap.parse_args()
sys.path.insert(0, str(BASE / 'tools'))
from vehicle_manager import Manager, parse_variants
from roster_loader_profile import strip_v2, parse_roster, class_map, read_profile_masks

src, host = args.source_host.resolve(), args.work_host.resolve()
assert src != host
if host.exists():
    shutil.rmtree(host)
for p in src.rglob('*'):
    rel = p.relative_to(src); dst = host / rel
    if p.is_dir():
        dst.mkdir(parents=True, exist_ok=True)
    elif rel.as_posix() == 'Data.sma':
        os.link(p, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, dst)
sha = lambda b: hashlib.sha256(b).hexdigest()
active = host / 'MRMods/Vehicles/active'
original = (active / 'roster.mrvr').read_bytes()
original_variants = (active / 'variants.ini').read_text()
m = Manager(host)
print('import', m.import_base(names=BASE / 'docs/vehicle-manager/presentation-fix-01.json'))
print('packages', [(p['file'], p['enabled']) for p in m.list_packages()])
print('plan', m.plan())

# 1. Unchanged selection -> identical roster
r = m.apply()
assert (active / 'roster.mrvr').read_bytes() == original, 'unchanged apply must reproduce the roster byte-exactly'
print('identity apply OK', r['loader_profile']['checks'])

# 2. Remove Rav4 (31), move ForesterSTI (30) to the T2 top, drop Tata DEMO
m.remove(31); m.set_order('T2', [30]); m.uninstall('tata-demo.mrcar')
r = m.apply()
roster = (active / 'roster.mrvr').read_bytes()
count, classes = class_map(parse_roster(strip_v2(roster)))
assert 31 not in classes and classes[30] == 1, classes
assert 31 not in read_profile_masks(roster)
vs = (active / 'resources/DataScene/FrontendScreens/VehicleSelect.xml').read_text(encoding='latin-1')
assert 'T2_Car13' not in vs and 'T2_Car12' in vs, 'one T2 widget fewer'
assert not any(v['base'] == 'Tata' for v in parse_variants(active / 'variants.ini'))
assert not (active / 'resources/DataGx/Vehicles/HeritageTata').exists()
print('edit apply OK', r['classes']['T2'])

# 3. Restore everything -> identical roster again
m.restore(31); m.set_order('T2', m.native()['classes']['T2']); m.install(m.packages / 'tata-demo.mrcar')
m.apply()
assert (active / 'roster.mrvr').read_bytes() == original
print('restore apply OK; variants', [v['folder'] for v in parse_variants(active / 'variants.ini')])

# 4. Stock and back
print(m.stock()); assert not active.exists()
m.apply(); assert (active / 'roster.mrvr').read_bytes() == original
print('ALL OK')
