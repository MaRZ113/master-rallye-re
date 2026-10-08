"""Read-only X/Z source maps; original geometry stays in ignored dressing1 data."""
import argparse
import html
import json
from pathlib import Path
import dressing_runtime as d
import geometry_delta as g

COLORS={'turkey3-shrub':'#71de87','turkey3-hut':'#ffb46b','turkey3-boat':'#b39bff','italys1-pinus':'#71de87'}


def write_maps(a,b,cards,output):
    output=d.local_output(output)
    selected={c['source_id']:c for c in cards}
    panels=[('Course context',g.bounds(a.positions+b.positions),None)]
    for card in cards:
        box=card['shape']['bounds'];lo,hi=box['min'][:],box['max'][:]
        margin=max(15.,max(hi[0]-lo[0],hi[2]-lo[2])*.15)
        for i in (0,2):lo[i]-=margin;hi[i]+=margin
        panels.append((card['candidate_id'],{'min':lo,'max':hi},card))
    height=110+((len(panels)+1)//2)*470
    pieces=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}">',
        '<rect width="100%" height="100%" fill="#101a24"/>',
        '<g fill="white" font-family="sans-serif" font-size="18">',
        '<text x="25" y="27">DRESSING1 | Authored source groups | X right, Z up</text>',
        '<text x="25" y="52">X/Z projection collapses height; no live LOD, object counts or runtime pose proof.</text>',
        '<text x="25" y="77">Gray: nearby PS2 source. Cyan: puddles. Orange outline: PC family draws. Number: edge component.</text></g>']
    for pi,(title,box,card) in enumerate(panels):
        x,y=25+(pi%2)*600,110+(pi//2)*470;lo,hi=box['min'],box['max']
        scale=min(545/max(hi[0]-lo[0],1),370/max(hi[2]-lo[2],1))
        def pos(p):return (x+15+(p[0]-lo[0])*scale,y+70+(hi[2]-p[2])*scale)
        def coords(points):return ' '.join('%.2f,%.2f'%pos(p) for p in points)
        def inside(face):
            bb=g.bounds(face.points)
            return bb['min'][0]<=hi[0] and bb['max'][0]>=lo[0] and bb['min'][2]<=hi[2] and bb['max'][2]>=lo[2]
        pieces.append(f'<rect x="{x}" y="{y}" width="575" height="455" fill="none" stroke="#405263"/>')
        pieces.append(f'<text x="{x+10}" y="{y+24}" fill="white" font-family="sans-serif" font-size="16">{html.escape(title)}</text>')
        if card:
            chain=' / '.join('tag'+str(n['tag'])+'@'+str(n['offset']) for n in card['hierarchy'])
            pieces.append(f'<text x="{x+10}" y="{y+46}" fill="#b9c8d5" font-family="sans-serif" font-size="10">{chain}</text>')
        clip='panel'+str(pi)
        pieces.append(f'<defs><clipPath id="{clip}"><rect x="{x+5}" y="{y+62}" width="565" height="380"/></clipPath></defs><g clip-path="url(#{clip})">')
        for face in a.faces:
            if not inside(face):continue
            color='#2a3a49'
            if g.w.shader_contract(a.groups[face.group]['material'])['water_mode'] is not None:color='#37bfd8'
            if face.group in selected:color=COLORS[selected[face.group]['candidate_id']]
            pieces.append('<polygon points="%s" fill="%s" fill-opacity=".45" stroke="%s" stroke-width=".35"/>'%(coords(face.points),color,color))
        pcgroups={v['source_id'] for c in cards for v in c['pc_family_draws']}
        for face in b.faces:
            if face.group in pcgroups and inside(face):
                pieces.append('<polygon points="%s" fill="none" stroke="#ffcd83" stroke-width=".6"/>'%coords(face.points))
        for c in cards:
            for index,comp in enumerate(next(x for x in c['decomposition'] if x['method']=='coordinate_edge')['components']):
                bb=comp['bounds'];center=tuple((bb['min'][i]+bb['max'][i])/2 for i in range(3))
                if not lo[0]<=center[0]<=hi[0] or not lo[2]<=center[2]<=hi[2]:continue
                px,py=pos(center)
                pieces.append(f'<text x="{px:.2f}" y="{py:.2f}" fill="white" font-family="sans-serif" font-size="10">{index+1}</text>')
        pieces.append('</g>')
        pieces.append(f'<text x="{x+10}" y="{y+449}" fill="#b9c8d5" font-family="sans-serif" font-size="10">Source bounds X {lo[0]:.1f}..{hi[0]:.1f}, Z {lo[2]:.1f}..{hi[2]:.1f}; Y retained in JSON.</text>')
    pieces.append('</svg>')
    output.write_text('\n'.join(pieces)+'\n',encoding='utf-8',newline='\n')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inventory',type=Path,required=True);ap.add_argument('--ps2-root',type=Path,required=True)
    ap.add_argument('--pc-root',type=Path,required=True);ap.add_argument('--sdk',type=Path,required=True)
    ap.add_argument('--output-directory',type=Path,required=True)
    args=ap.parse_args();data=json.loads(args.inventory.read_text(encoding='utf-8'))
    for course in ('TURKEY3','ITALY_S1'):
        a,b,_=g.load_pair(args.ps2_root,args.pc_root,args.sdk,course)
        output=args.output_directory/(course+'.svg')
        write_maps(a,b,[c for c in data['candidates'] if c['course']==course],output)
        print(d.local_output(output))


if __name__=='__main__':main()
