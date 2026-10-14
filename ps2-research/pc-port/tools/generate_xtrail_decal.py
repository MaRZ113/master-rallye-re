"""Source normals and UV guards only; no original mesh/texture arrays."""
from pathlib import Path
import importlib.util,json,struct,sys
PORT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(PORT.parents[1]/'ps2-research/tools'),r'D:/Game/Master Rallye/master-rallye-re-course/src']
from master_rallye.dx import parse_dx
from tngtool import file_hash

def render():
    evidence=json.loads((PORT/'docs/xtrail-fidelity/wheel-glass/source-evidence.json').read_text())
    car=next(x for x in evidence['models'] if x['kind']=='CAR')
    row=next(x for x in car['draws'] if x['source_draw']==13)
    path=Path(r'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Xtrail/car.dx')
    if file_hash(path)!=car['pc_sha256']:raise ValueError('Canonical PC source changed')
    model=parse_dx(path);draw=model.physical_draws[13]
    spec=importlib.util.spec_from_file_location('wheelglass',PORT/'docs/xtrail-fidelity/wheel-glass/audit.py')
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    table={r['pc_xyz_sha256']:r for r in car['decal_normal_augmentation']['entries']}
    for i in range(draw.vertex_base,draw.vertex_base+draw.local_vertex_max+1):
        key=a.digest_values([model.vertices.positions[i]])
        if key not in table:raise ValueError('Unknown source vertex')
        table[key]['uv_bits']=[struct.unpack('<I',struct.pack('<f',v))[0] for v in model.uv_sets[0].values[i]]
        color=bytes(model.vertices.colors[i*4:i*4+4])
        if color[0]!=color[1] or color[1]!=color[2] or color[3]!=255:raise ValueError('Non-gray source color; channel order unproved')
        table[key]['diffuse']=struct.unpack('<I',color)[0]
    lines=['#pragma once','// Exact original PC normal values checked against original PS2 root.14.',
        '// Position hashes are not geometry arrays; current UV/diffuse must also match.',
        '#include <array>','#include <cstdint>','namespace gfx2::ps2port {',
        'struct XtrailDecalNormal {const char* position_sha;std::array<uint32_t,3> normal_bits;std::array<uint32_t,2> uv_bits;uint32_t diffuse;};',
        'inline constexpr char kXtrailDecalGeometrySha[]="'+row['geometry_sha256']+'";',
        'inline constexpr XtrailDecalNormal kXtrailDecalNormals[]={']
    for key,r in sorted(table.items()):
        bits=[struct.unpack('<I',struct.pack('<f',v))[0] for v in r['normal']]
        lines.append('    {"%s",{%s},{%s},0x%08xu},'%(key,','.join(f'0x{x:08x}u' for x in bits),','.join(f'0x{x:08x}u' for x in r['uv_bits']),r['diffuse']))
    lines+=['};','} // namespace gfx2::ps2port','']
    return '\n'.join(lines)

if __name__=='__main__':(PORT/'renderer/xtrail_decal_registry.hpp').write_text(render(),encoding='utf-8',newline='\n')
