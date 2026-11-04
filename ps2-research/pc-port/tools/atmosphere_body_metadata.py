"""Author pure paint capabilities from existing PS2 source metadata, no mesh hashes.

Explicit selection is required: carshiny also contains lamps and wheel trim.
New families/materials can be added to JSON without rebuilding the Proxy.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

def canonical(s):return s.lower().replace('\\','/').split('/')[-1]
def safe(primary,secondary,role=1):
    allowed=((role==1 and secondary in ('whitepaint-tga','silverpaint-tga')) or (role==2 and secondary=='perspex-tga') or (role==3 and secondary in ('whitepaint-tga','silverpaint-tga','perspex-tga')) or (role==4 and secondary=='perspex-tga' and any(t in primary for t in ('wheelcover-tga','wheelcoverside-tga'))))
    exclusions=('glass','wheel','tread','tyre','tire','light','lamp','glow','brake','helmet','sticker','driver')
    return allowed and not any(t in primary for t in exclusions if not (role==3 and t=='sticker') and not (role==4 and t=='wheel'))
def fixed(s,n):
    if not s or len(s)>=n or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in s):raise ValueError('unsafe text')
    return s.encode()+bytes(n-len(s))
def export(selection,folder,output):
    rows=set();evidence=[]
    for family,selected in selection.items():
        names={item if isinstance(item,str) else item['primary']:1 if isinstance(item,str) else {'paint':1,'opaque_trim':2,'opaque_panel':3,'opaque_cover':4}[item['role']] for item in selected}
        path=folder/(family.upper()+'-CAR-FLEET.ps2model');data=path.read_bytes()
        if data[:8]!=b'PS2MDL02':raise ValueError('asset format')
        version,meta,meshes,vertices,indices,textures=struct.unpack_from('<6I',data,8)
        if version!=2:raise ValueError('asset version')
        source=json.loads(data[64:64+meta]);at=64+meta+28*meshes+36*vertices+4*indices;digests=[]
        for _ in range(textures):
            w,h,size=struct.unpack_from('<3I',data,at);at+=12
            if size!=w*h*4 or at+size>len(data):raise ValueError('texture bounds')
            digests.append(hashlib.sha256(data[at:at+size]).hexdigest());at+=size
        if at!=len(data) or len(source['meshes'])!=meshes:raise ValueError('source mesh metadata')
        bindings=[]
        for i,m in enumerate(source['meshes']):
            binary=struct.unpack_from('<7I',data,64+meta+i*28)
            if binary[1]!=m['mode'] or list(binary[2:5])!=m['texture_indices']:raise ValueError('source binding disagrees with binary')
            slots={t['slot']:canonical(t['name']) for t in m['source_texture_slots']}
            primary=slots.get(0,'null');secondary=slots.get(1,'null');digest=digests[m['texture_indices'][0]]
            bindings.append((primary,secondary,digest,m['mode']))
        found=set()
        for primary,secondary,digest,mode in bindings:
            if primary not in names:continue
            role=names[primary]
            if not safe(primary,secondary,role) or mode!=3:raise ValueError('selected non-paint material '+primary)
            # Same PS2 pixels in another shiny role would make a texture-scoped
            # capability ambiguous; keep only native binding support in that case.
            ps2=digest if all((p,s)==(primary,secondary) for p,s,d,m in bindings if d==digest and m==3) else '0'*64
            rows.add((family.lower(),primary,secondary,ps2,role));found.add(primary)
        if found!=set(names):raise ValueError('missing selected binding '+str(set(names)-found))
        evidence.append({'asset':str(path),'sha256':hashlib.sha256(data).hexdigest(),'selected_materials':sorted(found)})
    payload=b''.join(fixed(f,32)+fixed(p,96)+fixed(s,96)+fixed(h,65)+struct.pack('<I',role) for f,p,s,h,role in sorted(rows))
    data=struct.pack('<4sII',b'BLM2',2,len(rows))+hashlib.sha256(payload).hexdigest().encode()+payload
    output.mkdir(parents=True,exist_ok=False);(output/'body.blm').write_bytes(data)
    report={'format':'BLM2','records':len(rows),'sha256':hashlib.sha256(data).hexdigest(),'source_evidence':evidence,'geometry_hashes':False,'runtime_owner_pass_required':True}
    (output/'provenance.json').write_text(json.dumps(report,indent=2)+'\n');return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--selection',type=Path,required=True);p.add_argument('--assets',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(export(json.loads(a.selection.read_text()),a.assets,a.output),indent=2))
