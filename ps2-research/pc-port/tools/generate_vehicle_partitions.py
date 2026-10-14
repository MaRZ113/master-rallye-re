"""Generate exact per-face material lookup from independently audited metadata."""
from pathlib import Path
import hashlib
import json

PORT=Path(__file__).resolve().parents[1]
SOURCE=PORT/'docs/vehicle-model-port1/race-partitions/partition-evidence.json'
OUTPUT=PORT/'renderer/vehicle_partition_registry.hpp'

def render(data):
    lines=['#pragma once','// Generated from original source identities; hashes only, no game meshes.',
           '#include "vehicle_partition.hpp"','namespace gfx2::ps2port {']
    records=[]
    for vehicle in data['vehicles']:
        for draw in vehicle['draws']:
            n=len(records)
            if not draw['unique_geometry_vehicle_family']:raise ValueError('Ambiguous source owner')
            fs=draw['face_hash_categories']
            if sum(f['multiplicity'] for f in fs.values())!=draw['index_count']//3:
                raise ValueError('Incomplete source face multiplicities')
            digest=hashlib.sha256(''.join(h*f['multiplicity'] for h,f in sorted(fs.items())).encode()).hexdigest()
            if digest!=draw['geometry_sha256']:raise ValueError('Source multiset digest mismatch')
            lines.append(f'inline constexpr PartitionFace kPartitionFaces{n}[]={{')
            for h,f in sorted(fs.items()):
                if len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('Invalid digest')
                lines.append('    {"%s",%du,%s},' % (h,f['multiplicity'],str(f['category']=='carshiny').lower()))
            lines.append('};')
            records.append((vehicle['pc_family'],digest,draw['vertex_count'],draw['index_count']//3,len(fs)))
    lines.append('inline constexpr PartitionMaterial kVehiclePartitionMaterials[]={')
    for n,(name,h,v,t,f) in enumerate(records):
        lines.append(f'    {{"{name}","{h}",{v}u,{t}u,kPartitionFaces{n},{f}u}},')
    lines.extend(['};','} // namespace gfx2::ps2port',''])
    return '\n'.join(lines)

if __name__=='__main__':
    OUTPUT.write_text(render(json.loads(SOURCE.read_text())),encoding='utf-8',newline='\n')
    frontend=json.loads((PORT/'docs/vehicle-model-port1/frontend-identity/source-and-live-evidence.json').read_text())
    source=next(r for r in frontend['source_inventory']['complete_resources'] if r['path']=='Forester/complete.dx')
    lines=['#pragma once','// Original PC COMPLETE source hashes; no native addresses or draw ordinals.',
        '#include <cstdint>','namespace gfx2::ps2port {',
        'struct FrontendSource { const char* hash; uint32_t vertices,triangles; };',
        'inline constexpr FrontendSource kForesterCompleteSources[]={']
    for d in source['draws']:
        if not d['unique_to_complete_resource']:raise ValueError('Ambiguous frontend source')
        lines.append('    {"%s",%du,%du},' % (d['geometry_sha256'],d['vertices'],d['triangles']))
    lines+=['};','} // namespace gfx2::ps2port','']
    (PORT/'renderer/frontend_source_registry.hpp').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
