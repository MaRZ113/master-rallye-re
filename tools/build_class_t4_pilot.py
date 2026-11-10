"""CLASS-T4 pilot: accepted 33-record V-DEF4.1 roster + Dakar 2 vehicles in a new T4 tab.

Inputs are the owner-accepted V-DEF4.1 roster configuration (unchanged) and one
or more projects made by create_dakar2_classic_pilot.py. Writes only a fresh
private output; the original executable and accepted builds are not touched.
"""
import argparse, copy, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tools')]
from master_rallye import universal_vehicle_scene as uvs
from master_rallye.addon_sdk.project import build_project
from master_rallye.workshop.service import WorkshopProject


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-config', required=True, help='accepted 33-record roster-config.json')
    p.add_argument('--pilot', required=True, action='append', help='dakar2 classic pilot output (first one is the Workshop host)')
    p.add_argument('--retail-sma', required=True); p.add_argument('--retail-root', required=True)
    p.add_argument('--output', required=True); p.add_argument('--label', default='T4 (RAID)')
    p.add_argument('--game-exe', help='retail MRallye.exe of the launch host (default: the SDK default)')
    a = p.parse_args()
    output = Path(a.output).absolute()
    if output.exists():
        raise SystemExit('fresh output required')
    output.mkdir(parents=True)
    config = json.loads(Path(a.base_config).read_text())
    if config.get('experimental_record_count') != 33 or len(config['projects']) != 5:
        raise SystemExit('base must be the accepted 33-record roster')
    config = copy.deepcopy(config)
    t4 = []
    pilots = [json.loads((Path(x) / 'pilot-report.json').read_text()) for x in a.pilot]
    for n, pilot in enumerate(pilots):
        physical = 33 + n; author = Path(pilot['author'])
        build = output / f'author-build-{physical}'
        build_project(author, ROOT / 'research/vehicles/sdk/capabilities/retail-2001.json', build,
                      retail_data_sma=Path(a.retail_sma), retail_data_root=Path(a.retail_root))
        modes = json.loads((author / 'addon.json').read_text())['ai_eligibility']
        # T4 vehicles race in the T3 record class; AI insertion is not qualified for them yet.
        ai = {m: {'enabled': False, 'reason': 'CLASS-T4 pilot: player-only vehicle; opponents come from the T3 pool.'} for m in modes}
        config['projects'].append({'project': str(author), 'build': str(build), 'physical_id': physical, 'vehicle_class': 'T4', 'ai_eligibility': ai})
        t4.append(physical)
        spec = json.loads((author / 'vehicle-project.json').read_text()); folder = Path(spec['source_vehicle_dir'])
        if not folder.is_absolute():
            folder = (author / folder).resolve()
        family = pilot['family']
        config.setdefault('wheel_profiles', []).append({'runtime_family': family,
            'resource_keys': ['Vehicles/' + family + '/wheel-source' + str(i) for i in range(4)],
            'resource_sha256': [uvs.sha((folder / ('wheel-source' + str(i) + '.dx')).read_bytes()) for i in range(4)]})
    config['experimental_record_count'] = 33 + len(t4)
    if config['experimental_record_count'] not in (34, 35):
        raise SystemExit('the native profile currently admits one or two T4 vehicles (34/35 records)')
    config['selection_order']['T4'] = t4
    config['t4_label'] = a.label
    if a.game_exe:
        config['retail_exe'] = str(Path(a.game_exe).absolute())
    roster = output / 'roster'; roster.mkdir()
    (roster / 'roster-config.json').write_bytes(uvs.canonical(config))
    host = WorkshopProject(Path(pilots[0]['workshop']))
    host.configure_build({'roster_candidate': str(roster), 'retail_sma': str(Path(a.retail_sma).absolute()), 'retail_root': str(Path(a.retail_root).absolute())})
    host.camera_reset_original(); host.camera_mode_update(2, {})
    host.marker_update([.85, .12, .1]); host.shadow_update('auto')
    state = host.vehicle_state(); state['ai_eligibility'] = config['projects'][-len(t4)]['ai_eligibility']; host._vehicle_commit(state)
    report = host.build(output / 'builds/first', sdk_root=ROOT)
    (output / 'build-report.json').write_bytes(uvs.canonical(json.loads(json.dumps(report, default=str))))
    print(json.dumps({'output': str(output), 'launcher': str(output / 'builds/first/candidate/Launch-SDK-Roster.cmd')}, indent=1))


if __name__ == '__main__':
    main()
