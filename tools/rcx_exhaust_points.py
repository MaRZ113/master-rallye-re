"""RCX exhaust points: the `exhaust_flash` part of every RCX car archive marks the pipe outlet.

Prints/returns, per archive, the flash centre and size in the RCX source frame (+X left, +Y down, -Z front, metres),
the brakelight l/r centres (same frame) and the flash orientation (its MSH matrix rows), so a model frame can be
fitted from the lamps. Source archives are read only.
"""
from __future__ import annotations
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from master_rallye.source_adapters.rcx_formats import read_rcx,parse_msh,parse_qto,apply

SRC=Path(r'E:/RallyWorkshop_Sources/sources/Rally Championship Xtreme/Data/Cars')


def part_box(files,msh,name):
    if name+'.qto' not in files or name not in msh:return None
    d=parse_qto(files[name+'.qto']);pts=[apply(msh[name]['matrix'],v[0]) for v in d['vertices']]
    if not pts:return None
    lo=[min(p[k] for p in pts) for k in range(3)];hi=[max(p[k] for p in pts) for k in range(3)]
    return {'centre':[(lo[k]+hi[k])/2 for k in range(3)],'lo':lo,'hi':hi,'vertices':len(pts)}


def exhaust_points(path):
    files=read_rcx(Path(path).read_bytes());msh=parse_msh(files[next(k for k in files if k.endswith('.msh'))])
    out={'archive':Path(path).name,'flash':part_box(files,msh,'exhaust_flash'),
         'brake_l':part_box(files,msh,'brakelight l'),'brake_r':part_box(files,msh,'brakelight r'),
         'bumper_back':part_box(files,msh,'bumper back'),'body':part_box(files,msh,'body')}
    if 'exhaust_flash' in msh:out['flash_matrix']=list(msh['exhaust_flash']['matrix'])
    if 'steam_pivot' in msh:out['steam_pivot']=list(msh['steam_pivot']['matrix'][12:15])
    return out




def mr_points(rows,rigs_text,cars,archives):
    """Exhaust outlets in the installed MR model frame (+X left, +Y up, +Z front). RCX -> MR is (x, -y, -z) plus
    a per-car offset; the offset is fitted so the RCX brakelight parts land on the rig's blight OFF lens bounds
    (same geometry): x/y come out within a few mm, z absorbs the per-build axle centring."""
    offs={};cur=None
    for line in rigs_text.splitlines():
        t=line.split()
        if t and t[0]=='car':cur=t[1]
        elif t and t[0]=='off' and cur and cur not in offs:offs[cur]=(list(map(float,t[2:5])),list(map(float,t[5:8])))
    out={};by_arc={r['archive']:r for r in rows}
    for key,arc in archives.items():
        name=cars[key][0];r=by_arc.get(arc)
        if not r or not r['flash'] or name not in offs:continue
        mr=lambda c:(c[0],-c[1],-c[2])
        corners=[mr(r[s][e]) for s in ('brake_l','brake_r') for e in ('lo','hi')]
        lo=[min(c[i] for c in corners) for i in range(3)];hi=[max(c[i] for c in corners) for i in range(3)]
        olo,ohi=offs[name];t=[((olo[i]+ohi[i])-(lo[i]+hi[i]))/2 for i in range(3)]
        e=mr(r['flash']['centre']);fit=max(abs((olo[i]-lo[i])-t[i]) for i in range(3))
        out[name]={'archive':arc,'exhaust':[e[i]+t[i] for i in range(3)],'offset':t,'fit_error_m':fit}
    return out


def rig_text(points):
    lines=['# FX-EXHAUST1 exhaust outlets (tools/rcx_exhaust_points.py), MR model frame: +X left, +Y up, +Z front, metres.',
           '# exhaust x y z  dx dy dz  radius   (direction = outflow, normalised by the reader; RCX exhaust_flash marker, identity rotation = straight back)']
    for name,p in sorted(points.items()):
        x,y,z=p['exhaust'];lines+=['car '+name,'exhaust %.3f %.3f %.3f 0 -0.15 -1 0.030'%(x,y,z)]
    return '\n'.join(lines)+'\n'


def main(argv):
    import argparse
    from master_rallye.rcx_classic_pilot import CARS,ARCHIVES
    a=argparse.ArgumentParser();a.add_argument('--rigs');a.add_argument('--out');a.add_argument('--report');x=a.parse_args(argv)
    rows=[exhaust_points(p) for p in sorted(SRC.glob('*.rcx')) if '_arcade' not in p.stem.lower()]
    if x.report:Path(x.report).write_text(json.dumps(rows,indent=1),encoding='utf-8')
    if x.rigs:
        pts=mr_points(rows,Path(x.rigs).read_text(encoding='utf-8'),CARS,ARCHIVES)
        for n,p in sorted(pts.items()):print(n,[round(v,3) for v in p['exhaust']],'fit %.3f m'%p['fit_error_m'])
        if x.out:Path(x.out).write_text(rig_text(pts),encoding='utf-8',newline='\n')


if __name__=='__main__':main(sys.argv[1:])
