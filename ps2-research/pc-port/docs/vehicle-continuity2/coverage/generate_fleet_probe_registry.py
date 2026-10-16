"""Generate read-only fleet draw metadata; never grants replacement authority."""
from pathlib import Path
import collections
import hashlib
import json

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / 'vehicle-crew-port1/fleet/car-candidates.json'

def profiles():
    data = json.loads(SOURCE.read_text())
    families = [x for x in data['fleet'] if x.get('pc_family') and x['pc_family'].lower() != 'forklift']
    owners = collections.defaultdict(set)
    for family in families:
        for draw in family['draws']:
            owners[draw['geometry_sha256']].add(family['pc_family'])
    rows = []
    for family in families:
        for draw in family['draws']:
            rows.append(dict(family=family['pc_family'], source_path=family['pc_family'] + '/car.dx',
                             record_path=draw['record_path'], vertices=draw['vertices'], faces=draw['faces'],
                             geometry_sha256=draw['geometry_sha256'],
                             unique_across_families=len(owners[draw['geometry_sha256']]) == 1))
    return rows

def render(rows):
    lines = ['#pragma once', '#include <cstddef>',
             '// READ-ONLY SOURCE METADATA. NOT A REPLACEMENT OR OWNER CERTIFICATE.',
             'namespace gfx2::ps2port {',
             'struct FleetProbeProfile { const char* family; const char* source_path; const char* record_path; unsigned vertices, faces; const char* geometry_sha256; bool unique_across_families; };',
             'inline constexpr FleetProbeProfile kFleetProbeProfiles[]={']
    for row in rows:
        lines.append(' {' + ','.join(json.dumps(row[x]) for x in ['family', 'source_path', 'record_path']) +
                     ',%du,%du,' % (row['vertices'], row['faces']) + json.dumps(row['geometry_sha256']) +
                     ',' + str(row['unique_across_families']).lower() + '},')
    return '\n'.join(lines + ['};', 'inline constexpr std::size_t kFleetProbeProfileCount=sizeof(kFleetProbeProfiles)/sizeof(kFleetProbeProfiles[0]);', '}']) + '\n'

def main():
    rows = profiles()
    (HERE / 'fleet_probe_registry.hpp').write_text(render(rows))
    manifest = dict(schema=1, source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                    families=sorted({r['family'] for r in rows}), profiles=len(rows),
                    unique_profiles=sum(r['unique_across_families'] for r in rows),
                    policy='READ_ONLY_METADATA_NO_RUNTIME_AUTHORITY_NO_FORKLIFT')
    (HERE / 'fleet-probe-registry.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))

if __name__ == '__main__':
    main()
