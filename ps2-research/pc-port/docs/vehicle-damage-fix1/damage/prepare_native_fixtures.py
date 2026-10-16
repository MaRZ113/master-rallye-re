"""Ignored source/capture-derived replay fixtures; unobserved damaged slots stay synthetic healthy controls."""
from pathlib import Path
import collections, hashlib, importlib.util, json, struct
HERE=Path(__file__).resolve().parent
PORT=HERE.parents[2]

def main():
    spec=importlib.util.spec_from_file_location('damage_source',HERE/'generate_correspondence.py')
    s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
    raw=s.PC.read_bytes()
    if s.sha(raw)!=s.EXPECTED_PC:raise ValueError('PC source drift')
    pc=s.parse_dx(s.PC)
    profiles=json.loads((HERE/'deformation-correspondence-summary.json').read_text())['profiles']
    baseline=[]
    for p in profiles:
        draw=next(d for d in pc.physical_draws if d.local_vertex_max+1==p['native_vertices'] and d.index_count//3==p['native_triangles'])
        first=draw.vertex_base;count=draw.local_vertex_max+1
        vertex=b''.join(struct.pack('<3fI2f',*pc.vertices.positions[i],0xffffffff,*pc.uv_sets[0].values[i]) for i in range(first,first+count))
        ids=[i-first for i in pc.draw_global_indices(draw)]
        for k in range(0,len(ids),3):ids[k],ids[k+1]=ids[k+1],ids[k]
        baseline.append((0x142,24,count,len(ids)//3,vertex,struct.pack('<%dI'%len(ids),*ids)))
    files=sorted(Path(r'D:/Game/Master Rallye Pristine/MRRRenderer/logs').glob('race-damage-47284-*.jsonl'))
    if len(files)!=3:raise ValueError('Pinned runtime trio missing')
    states=[baseline];used=[]
    for file in files[1:]:
        rows=[json.loads(line) for line in file.read_text().splitlines()]
        state=list(baseline);observed=[]
        for j in rows:
            if j['type']!='race_damage_draw' or j.get('packet')!=46152728 or not j.get('mirror_complete'):continue
            for slot,p in enumerate(profiles):
                if j['vertices']==p['native_vertices'] and j['triangles']==p['native_triangles']:
                    vertices=bytes.fromhex(j['vertex_hex']);data=bytes.fromhex(j['index_hex']);width=2 if j['index_format']==101 else 4
                    ids=[i[0]-j['min'] for i in struct.iter_unpack('<H' if width==2 else '<I',data)]
                    state[slot]=(j['fvf'],j['stride'],j['vertices'],j['triangles'],vertices,struct.pack('<%dI'%len(ids),*ids));observed.append(slot)
        states.append(state);used.append({'file':file.name,'sha256':s.sha(file.read_bytes()),'observed_slots':observed,'unobserved_slots':'SYNTHETIC_ORIGINAL_HEALTHY_CONTROL'})
    data=b'PS2DMG01'+struct.pack('<I',len(states))
    for state in states:
        for fvf,stride,vertices,triangles,v,i in state:data+=struct.pack('<6I',fvf,stride,vertices,triangles,len(v),len(i))+v+i
    path=PORT/'.assets/vehicles/xtrail-damage-fixtures.bin';path.write_bytes(data)
    report={'path':str(path),'sha256':s.sha(data),'states':3,'sources_per_state':13,'provenance':used,'runtime_complete_state_claim':False}
    (HERE/'fixture-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
