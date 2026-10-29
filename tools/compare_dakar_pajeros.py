"""Private, repeatable source-geometry comparisons; no MR authoring."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye import universal_vehicle_scene as u
from master_rallye.source_scene_preview import stage_source_scene,capture_views


def geometry(scene):
    nodes={n['id']:n for n in scene['nodes']};meshes={m['id']:m for m in scene['meshes']};world={}
    def transform(key):
        if key not in world:
            n=nodes[key];world[key]=u.multiply(transform(n['parent_id']),n['local_transform'])if n['parent_id']is not None else n['local_transform']
        return world[key]
    points=[];wheels=[];body=[];parts={}
    for n in nodes.values():
        m=u.multiply(scene['coordinate_system']['source_to_normalized'],transform(n['id']))
        if n.get('role')=='wheel' and 'SPARE' not in n['name']:wheels.append(u.transform_point(m,[0,0,0]))
        if n.get('role')=='shadow':continue
        p=[u.transform_point(m,v)for mid in n['mesh_ids']for v in meshes[mid]['positions']]
        points+=p;parts[n['name']]=p
        if n.get('role')=='body':body+=p
    if len(wheels)!=4:raise ValueError('Four evidenced wheel nodes required')
    wheels.sort(key=lambda p:p[2]);front=wheels[:2];rear=wheels[2:]
    f=[sum(p[k]for p in front)/2 for k in range(3)];r=[sum(p[k]for p in rear)/2 for k in range(3)]
    wb=r[2]-f[2]
    if wb<=.01:raise ValueError('Ambiguous axle alignment')
    centre=[(f[k]+r[k])/2 for k in range(3)]
    def bounds(p):return [[min(v[k]for v in p)for k in range(3)],[max(v[k]for v in p)for k in range(3)]]
    b=bounds(points);bb=bounds(body)
    unique=sorted(set(tuple(round((p[k]-centre[k])/wb,6)for k in range(3))for p in body))
    profiles=[]
    for z in [-.5,-.25,0,.25,.5]:
        region=[p for p in unique if abs(p[2]-z)<.04]
        profiles.append({'z_per_wheelbase':z,'vertices':len(region),'bounds':bounds(region)if region else None})
    return {'wheelbase':wb,'front_track':abs(front[1][0]-front[0][0]),'rear_track':abs(rear[1][0]-rear[0][0]),
        'axle_centre':centre,'front_axle':f,'rear_axle':r,'assembly_bounds':b,'body_role_bounds':bb,
        'front_overhang':f[2]-bb[0][2],'rear_overhang':bb[1][2]-r[2],
        'height_per_wheelbase':(bb[1][1]-bb[0][1])/wb,'width_per_wheelbase':(bb[1][0]-bb[0][0])/wb,
        'normalized_body_unique_vertices':unique,'body_cross_sections':profiles,
        'parts':{name:{'vertices':len(p),'bounds':bounds(p)}for name,p in parts.items()if p},
        'mesh_count':len(scene['meshes']),'vertices':sum(len(m['positions'])for m in scene['meshes']),
        'triangles':sum(len(m['triangles'])for m in scene['meshes']),
        'mesh_position_hashes':[u.sha(u.canonical(m['positions']))for m in scene['meshes']],
        'limits':'Source rest nodes only; units not independently physical; body role includes attachments/crew. Cross-sections are envelope samples, not identified pillars.'}


def compare(inputs,output,viewer):
    output=u.output_directory(Path(output).absolute(),[Path(p).parent for p in inputs.values()])
    if output.exists():raise ValueError('Fresh comparison output required')
    output.mkdir(parents=True);scenes={};report={};previews={}
    for name,path in inputs.items():
        s=u.load_scene(path);scenes[name]=s;g=geometry(s);report[name]=g
        derived=deepcopy(s);wb=g['wheelbase'];c=g['axle_centre']
        affine=[1/wb,0.,0.,-c[0]/wb,0.,1/wb,0.,-c[1]/wb,0.,0.,1/wb,-c[2]/wb,0.,0.,0.,1.]
        derived['coordinate_system']['source_to_normalized']=u.multiply(affine,s['coordinate_system']['source_to_normalized'])
        for n in derived['nodes']:
            if n.get('role')=='shadow':n['visible']=False
        target=output/name;target.mkdir();preview=target/'aligned.mrpv'
        stage_source_scene(derived,preview,scene_root=Path(path).parent)
        data=bytearray(preview.read_bytes())
        # Equal bounds/camera across all models. Uniform wheelbase scale only;
        # no changes to source JSON or mesh arrays, no nonuniform fitting.
        struct.pack_into('<6f',data,16,-.55,-.35,-.9,.55,.85,.9);preview.write_bytes(data)
        previews[name]=capture_views(viewer,preview,target/'views',cull='source'if name=='Xbox'else'cw',
            provenance=name+'; wheelbase=1; axle-centred; static pose; source shader approximation')
        g['scene_sha256']=u.sha(Path(path).read_bytes());g['comparison_affine']=affine
    pairs={}
    names=list(report)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            x=set(map(tuple,report[a]['normalized_body_unique_vertices']));y=set(map(tuple,report[b]['normalized_body_unique_vertices']))
            pairs[a+' / '+b]={'exact_normalized_vertex_intersection':len(x&y),'a_vertices':len(x),'b_vertices':len(y),
                'shared_position_array_hashes':len(set(report[a]['mesh_position_hashes'])&set(report[b]['mesh_position_hashes'])),
                'identity':'No identity claim; vertex overlap alone is not topology or provenance evidence'}
    from PIL import Image,ImageDraw
    for view in ('front','rear','left','right','top','isometric'):
        canvas=Image.new('RGB',(1080,270),(25,28,32));draw=ImageDraw.Draw(canvas)
        for i,name in enumerate(inputs):
            with Image.open(previews[name]['views'][view])as im:
                im.thumbnail((360,240));canvas.paste(im,(i*360,25))
            draw.text((i*360+12,7),name+' | WB=1, same camera',fill='white')
        canvas.save(output/(view+'-comparison.png'))
    data={'schema':'pajero-geometry-comparison/1','models':report,'pairs':pairs,
        'alignment':'Rigid axis normalization, axle-centre translation and UNIFORM scale by measured source wheelbase; source rest stance retained, not settled ground pose',
        'runtime':'NOT TESTED','prerelease_geometry':'MISSING INPUT; perspective reference images cannot establish exact geometry'}
    (output/'measurements.json').write_bytes(u.canonical(data));return data


def historical_sheets(comparison,references,output):
    """Owner-local image references only; never infer a 3D match from pixels."""
    from PIL import Image,ImageDraw
    comparison,references,output=map(Path,(comparison,references,output))
    u.output_directory(output,[references,comparison]);output.mkdir(parents=True,exist_ok=False)
    rows=[]
    for filename in ('m_rallye_05.jpg','m_rallye_07.jpg','mr4_paj.jpg','mr_1m.jpg','mr7.jpg','m_rallye_08.jpg'):
        source=references/filename
        if not source.is_file():
            rows.append({'file':filename,'status':'MISSING INPUT'});continue
        u.unlinked(source);blob=u.read_bounded(source,32*1024*1024)
        with Image.open(source)as im:
            size=im.size;thumb=im.convert('RGB');thumb.thumbnail((720,480))
        canvas=Image.new('RGB',(1080,810),(25,28,32));draw=ImageDraw.Draw(canvas)
        draw.text((12,7),filename+' | perspective reference, capture build/camera UNKNOWN',fill='white')
        canvas.paste(thumb,(0,30))
        with Image.open(comparison/'isometric-comparison.png')as strip:canvas.paste(strip,(0,530))
        draw.text((735,55),'No projection matching',fill='white')
        draw.text((735,80),'No geometric identity claim',fill='white')
        canvas.save(output/(source.stem+'-comparison.png'))
        rows.append({'path':str(source.absolute()),'sha256':u.sha(blob),'bytes':len(blob),'dimensions':size,
                     'status':'visual reference only; original pixels retained, thumbnail uniformly resized'})
    (output/'references.json').write_bytes(u.canonical(rows));return rows


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('red','silver','xbox','output','viewer'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--references',type=Path)
    a=p.parse_args();compare({'PC RED':a.red,'PC Silver':a.silver,'Xbox':a.xbox},a.output,a.viewer)
    if a.references:historical_sheets(a.output,a.references,a.output.parent/(a.output.name+'-historical'))
