"""Opt-in translation of opaque islands in GT4 RGB/alpha/environment passes.

An RGB pass may blend windows and solid trim from one texture. Only triangles
whose complete filtered UV footprint has unity opacity become opaque. A separate
alpha-only pass supplies reflection weights, never window opacity. Unsupported
or ambiguous correspondence fails closed.
"""
from collections import defaultdict
from .gt4_mr_materials import oriented_triangle_key,covered_uv_footprint


def opaque_layered_surfaces(draws,selections):
    selected={}
    for item in selections:
        if set(item)!={'shape','packets','role'} or not item['role']:raise ValueError('Layered surface needs explicit source role')
        for packet in item['packets']:
            key=item['shape'],packet
            if key in selected:raise ValueError('Duplicate layered selector')
            selected[key]=item['role']
    alpha=defaultdict(list);environment=defaultdict(list)
    for no,d in enumerate(draws):
        if d.get('component','body')!='body':continue
        s=d['state']
        target=alpha if s['fbmask']==0xffffff and not s['depth_write'] and not d['gif']['blend'] and not d['issues'] and d['texture'] else environment if d['issues']==['runtime-generated external texture / texgen unavailable'] and d['gif']['blend'] and s['blend'][:4]==[0,2,1,1] and not s['depth_write'] and not s['date'] and not s['fbmask'] and not s['alpha_test'] else None
        if target is not None:
            for tri in d['triangles']:target[oriented_triangle_key(d,tri)].append((no,d,tri))
    output=[];seen=set()
    for d in draws:
        key=d['source_shape'],d['packet']
        if d.get('component','body')!='body' or key not in selected:output.append(d);continue
        seen.add(key);s=d['state'];tex=d['texture']
        if d['issues'] or not d['gif']['blend'] or s['blend'][:4]!=[0,1,0,1] or not s['depth_write'] or s['fbmask']!=0xff000000 or s['date'] or s['alpha_test'] or not tex or tex['registers']['tfx']!=0 or not tex['registers']['tcc']:raise ValueError('Unqualified layered RGB source')
        opaque=[];rest=[];partners=[];gains=set()
        for tri in d['triangles']:
            probe={**d,'triangles':[tri],'state':{**s,'alpha_test':True,'alpha_func':4,'alpha_ref':128}}
            if not covered_uv_footprint(probe):rest.append(tri);continue
            k=oriented_triangle_key(d,tri);ap=alpha[k];ep=environment[k]
            if len(ap)!=1 or len(ep)!=1:raise ValueError('Layered triangle lacks unique alpha/environment partners')
            ano,a,at=ap[0];eno,e,et=ep[0]
            if any((d['vertices'][i]['rgba_ps2'] or [128]*4)[3]!=128 for i in tri):raise ValueError('Layered opacity needs unity vertex alpha')
            lookup={tuple(a['vertices'][i]['position']):a['vertices'][i] for i in at}
            if any((a['vertices'][i]['rgba_ps2'] or [128]*4)[3]!=128 for i in at):raise ValueError('Layered alpha needs unity source vertex alpha')
            if any(tuple(d['vertices'][i]['uv'])!=tuple(lookup[tuple(d['vertices'][i]['position'])]['uv']) for i in tri):raise ValueError('Layered alpha UV differs')
            ar=a['texture']['registers'];br=tex['registers']
            if a['state']['alpha_test'] or a['state']['date'] or any(ar[f]!=br[f] for f in ('width','height','tfx','tcc')):raise ValueError('Layered alpha format differs')
            for axis,size in enumerate((tex['width'],tex['height'])):
                fields=('wrap_s','min_u','max_u') if axis==0 else ('wrap_t','min_v','max_v')
                # Repeat and full-image clamp are equivalent strictly inside
                # the half-texel boundary; prove this for the entire triangle.
                if any(ar[f]!=br[f] for f in fields) and (ar[fields[0]] not in (0,1,2) or br[fields[0]] not in (0,1,2) or ar[fields[1]]!=0 or br[fields[1]]!=0 or ar[fields[2]]!=size-1 or br[fields[2]]!=size-1 or any(not .5/size<=d['vertices'][i]['uv'][axis]<=1-.5/size for i in tri)):raise ValueError('Layered alpha addressing differs on used footprint')
            colours={tuple(e['vertices'][i]['rgba_ps2'] or [128]*4)[:3] for i in et}
            if len(colours)!=1:raise ValueError('Layered environment gain is not constant')
            gains.update(colours);partners.append((ano,eno,a));opaque.append(tri)
        if rest:output.append({**d,'triangles':rest,'_mr_uv_vertices':sorted({i for t in d['triangles'] for i in t})})
        if opaque:
            if len(gains)!=1 or len({bytes(a['texture']['rgba_ps2'][3::4]) for _,_,a in partners})!=1:raise ValueError('Layered alpha/gain varies across partners')
            rgba=bytearray(tex['rgba_ps2']);rgba[3::4]=partners[0][2]['texture']['rgba_ps2'][3::4]
            info={'gain_rgb':[x/128 for x in next(iter(gains))],'coverage':'opaque_uv_footprint','layered_role':selected[key],
                  'source_alpha_packets':sorted({a for a,_,_ in partners}),'source_environment_packets':sorted({e for _,e,_ in partners}),
                  'rule':'unity source-opacity footprint plus matching alpha-only and generated-environment triangles',
                  'approximation':'MR helper replaces GT4 generated environment; translucent residual remains separate'}
            output.append({**d,'triangles':opaque,'texture':{**tex,'rgba_ps2':bytes(rgba)},'gif':{**d['gif'],'blend':False},'_mr_paint_reflection':info,'_mr_uv_vertices':sorted({i for t in d['triangles'] for i in t})})
    if seen!=set(selected):raise ValueError('Layered source selection absent')
    return output
