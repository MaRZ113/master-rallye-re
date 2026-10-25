"""Read-only runtime-resource audit plus private offline comparison artifacts.

Does not launch the game. Output files stay inside the explicitly supplied stage.
"""
from __future__ import annotations

import argparse
import collections
import dataclasses
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.dx import parse_dx_bytes
from master_rallye.dxt import parse_dxt,decode_rgba_pixels,PNG_ROWS_FLIP_VERTICAL
from master_rallye.topology_writer import source_geometry
import vmesh_raster as raster


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(stage: Path, before: Path):
    family = stage/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
    old_family = before/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
    rows = collections.defaultdict(collections.Counter)
    same = 0
    max_move = 0.
    for frame in ('car','complete'):
        old = parse_dx_bytes((old_family/(frame+'.dx')).read_bytes())
        new = parse_dx_bytes((family/(frame+'.dx')).read_bytes())
        maps = [json.loads((s/f'source-map/source-map-{frame}.json').read_text())['records'] for s in (before,stage)]
        aa,bb = ({r['face']:r for r in mm} for mm in maps)
        if aa.keys()!=bb.keys(): raise ValueError('source face sets differ')
        for fi,a in aa.items():
            b = bb[fi]
            def mode(model, r):
                gate,selector = model.physical_draws[r['draw']].flags_0x20[:2]
                return 'opaque' if not gate else 'cutout' if selector else 'blend'
            rows[(frame,a['obj'],a['material'],a['source_role'])][mode(old,a)+' -> '+mode(new,b)]+=1
            def points(model,r):
                d=model.physical_draws[r['draw']]
                return [model.vertices.positions[i] for i in model.draw_global_indices(d)[3*r['tri']:3*r['tri']+3]]
            for p,q in zip(points(old,a),points(new,b)):
                max_move=max(max_move,max(abs(x-y) for x,y in zip(p,q)))
            same+=1
    if max_move>1e-6: raise ValueError(f'body source position regression: {max_move}')
    # Recheck final embedded wheels, not an intermediate conversion file.
    wheel=parse_dx_bytes((family/'wheel.dx').read_bytes())
    complete=parse_dx_bytes((family/'complete.dx').read_bytes())
    wg,cg=source_geometry(wheel),source_geometry(complete)
    hubs=json.loads((stage/'reports/convert-complete.json').read_text())['hubs_frame']
    wd={d.texture_slots[0].value:wg[d.draw_index] for d in wheel.physical_draws}
    wheel_error=0.
    for d in (20,21,22,23):
        g=wd[complete.physical_draws[d].texture_slots[0].value]
        if len(cg[d].vertices)!=4*len(g.vertices): raise ValueError('frontend wheel count mismatch')
        for i,h in enumerate(hubs):
            mirror=1 if h[0]<0 else -1
            for a,b in zip(g.vertices,cg[d].vertices[i*len(g.vertices):(i+1)*len(g.vertices)]):
                expected=(h[0]+mirror*a.position[0],h[1]+a.position[1],h[2]+a.position[2])
                wheel_error=max(wheel_error,max(abs(x-y) for x,y in zip(expected,b.position)))
    if wheel_error>1e-6: raise ValueError('frontend and race wheel geometry differ')
    # Verify all three static package boundaries after serialization.
    validation=json.loads((stage/'reports/validation-report.json').read_text())
    if validation['pool_alpha_flag_mismatches']: raise ValueError('alpha state mismatch')
    if validation['material_mapping_verification']['opaque_pool_triangles_with_transparent_footprint']:
        raise ValueError('opaque coverage regression')
    if any(h['visible_samples_inside_tyre'] for h in validation['material_aware_wheel_clearance']['hubs']):
        raise ValueError('sampled wheel/body penetration')
    packages=[]
    # The review archive will contain this audit. Exclude its own hash to avoid
    # a recursive manifest; check its CRC separately after final packaging.
    for p in sorted((stage/'review').glob('*-candidate.zip')):
        with zipfile.ZipFile(p) as z:
            bad=z.testzip()
            if bad:raise ValueError(f'ZIP CRC failure: {bad}')
            packages.append({'name':p.name,'bytes':p.stat().st_size,'members':len(z.namelist()),'crc':'PASS','sha256':sha(p)})
    return {'status':'PASS_OFFLINE_NOT_RUNTIME_QUALIFIED','source_face_records_compared':same,
            'maximum_source_position_delta_m':max_move,'maximum_frontend_wheel_delta_m':wheel_error,
            'surface_passes':[{'frame':f,'object':o,'material':m,'source_role':r,'transitions':dict(v)}
                              for (f,o,m,r),v in rows.items()], 'packages':packages}


def comparison(stage: Path, before: Path):
    folder=stage/'preview'
    views={'windscreen_base':(165,25,390,(0,1.25,1.02)),
           'window_edges':(90,5,300,(0,1.32,0)),
           'front_reflection_control':(145,9,150,(0,.9,.7)),
           'rear_reflection_control':(30,8,150,(0,.9,-.7))}
    html=['<h2>Surface close-ups and encoded reflection control</h2>',
          '<p>Left: V4.5. Right: V4.6. Close-ups are software previews, not game captures. ',
          'Reflection-control images show opaque environment-draw texture alpha as grayscale (black = zero). ',
          'Cutout and blend surfaces are blue: their alpha also controls coverage. This is a material diagnostic, ',
          'not a simulation of the environment stage or its final brightness.</p><table>']
    for view,(az,el,scale,centre) in views.items():
        html.append('<tr>')
        for label,base in (('vmesh45',before),('vmesh46',stage)):
            family=base/'runtime/resource-root/DataGx/Vehicles/ImprezaProto'
            items=raster.load_dx_family(family,'complete.dx',skip_draws=(20,21,22,23))
            if 'reflection_control' in view:
                model=parse_dx_bytes((family/'complete.dx').read_bytes())
                converted=[]
                for item in items:
                    draw=model.physical_draws[int(item.name.split(':')[-1])]
                    if item.texture:
                        w,h,px=item.texture
                        px=bytearray(px)
                        for i in range(0,len(px),4):
                            if item.blend or item.alpha_test: px[i:i+3]=bytes((65,110,180))
                            else:
                                value=px[i+3] if draw.unknown_0x24&4 else 0
                                px[i:i+4]=bytes((value,value,value,255))
                        item=dataclasses.replace(item,texture=(w,h,bytes(px)))
                    converted.append(item)
                items=converted
            path=folder/f'{label}_{view}.png'
            path.write_bytes(raster.png_rgb(800,420,raster.render(items,raster.Camera(az,el,scale,centre),800,420)))
            html.append(f'<td><h3>{label}: {view}</h3><img src="{path.name}"></td>')
        html.append('</tr>')
    html.append('</table>')
    index=folder/'index.html'
    text=index.read_text()
    marker='<!-- V46_DETAIL_AUDIT -->'
    text=text.split(marker)[0]+marker+'\n'+''.join(html)
    index.write_text(text,encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage',type=Path,required=True)
    ap.add_argument('--before',type=Path,required=True)
    ap.add_argument('--previews',action='store_true')
    args=ap.parse_args()
    result=audit(args.stage,args.before)
    (args.stage/'reports/final-offline-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    if args.previews: comparison(args.stage,args.before)
    print(json.dumps({k:v for k,v in result.items() if k!='surface_passes'},indent=2))


if __name__=='__main__':main()
