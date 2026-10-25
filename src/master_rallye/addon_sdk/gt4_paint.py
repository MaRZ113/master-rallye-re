"""Explicit paint roles over source-qualified GT4 environment geometry.

Partition existing triangles by coverage instead of dropping an entire paint
packet when one UV island needs a cutout. No triangles or UVs are invented.
The bounded MR fallback raises reflection alpha only on residual cutout
triangles; opaque triangles retain the original per-texel reflection weight.
"""
from collections import defaultdict
from .gt4_mr_materials import oriented_triangle_key,covered_uv_footprint
from .gt4_materials import alpha_compare


def prepare_paint(draws,selections,*,cutout_floor=129):
    if not isinstance(selections,list) or type(cutout_floor) is not int or not 129<=cutout_floor<=255:
        raise ValueError('invalid paint coverage policy')
    selected={}
    for item in selections:
        if set(item)!={'shape','packets','role'} or type(item['shape']) is not int or item['shape']<0 or not isinstance(item['role'],str) or not item['role']:
            raise ValueError('paint role needs explicit source shape, packets and label')
        if not isinstance(item['packets'],list) or any(type(i) is not int or i<0 for i in item['packets']):raise ValueError('invalid paint packet selection')
        for packet in item['packets']:
            key=item['shape'],packet
            if key in selected:raise ValueError('duplicate paint selector')
            selected[key]=item['role']
    env=defaultdict(list)
    for no,d in enumerate(draws):
        s=d['state']
        if d.get('component','body')!='body' or d['issues']!=['runtime-generated external texture / texgen unavailable']:continue
        if not d['gif']['blend'] or s['blend'][:4]!=[0,2,1,1] or s['fbmask']&0xffffff or s['depth_write'] or s['alpha_test']:continue
        # One source environment packet may batch several separate surfaces
        # with different gains. Match the actually used triangle vertices.
        for t in d['triangles']:
            colours={tuple(d['vertices'][i]['rgba_ps2'] or [128]*4)[:3] for i in t}
            if len(colours)==1:env[oriented_triangle_key(d,t)].append((no,next(iter(colours))))
    seen=set();plans={};consumed=defaultdict(set)
    for no,d in enumerate(draws):
        key=d['source_shape'],d['packet']
        if d.get('component','body')!='body' or key not in selected:continue
        if key in seen:raise ValueError('ambiguous paint source instance')
        seen.add(key);s=d['state'];tex=d['texture'];used={i for t in d['triangles'] for i in t}
        if d['issues'] or d['gif']['blend'] or not s['depth_write'] or s['fbmask'] or s['date'] or not tex:raise ValueError('paint selector is not an opaque source base pass')
        if not tex['registers']['tcc'] or tex['registers']['tfx']!=0 or any(d['vertices'][i]['normal'] is None or (d['vertices'][i]['rgba_ps2'] or [128]*4)[3]!=128 for i in used):raise ValueError('unsupported paint texture/vertex semantics')
        matches=[env.get(oriented_triangle_key(d,t),[]) for t in d['triangles']]
        if not matches or any(len(x)!=1 for x in matches):raise ValueError('paint lacks complete unambiguous source environment geometry')
        packets=sorted({x[0][0] for x in matches});colours={x[0][1] for x in matches}
        states=[draws[i]['state'] for i in packets]
        if len(colours)!=1 or len({(x['date'],x['datm']) for x in states})!=1:raise ValueError('inconsistent source paint environment state')
        e=states[0];alphas=tex['rgba_ps2'][3::4]
        covered=[not s['alpha_test'] or alpha_compare(a,s['alpha_func'],s['alpha_ref']) for a in alphas]
        if not any(c and a>0 and (not e['date'] or int(a>=128)==e['datm']) for a,c in zip(alphas,covered)):raise ValueError('paint environment is inactive')
        info={'source_environment_packets':packets,'gain_rgb':[x/128 for x in next(iter(colours))],
            'date':e['date'],'datm':e['datm'],'paint_role':selected[key],
            'rule':'explicit exterior paint role plus complete oriented source environment correspondence',
            'approximation':'MR environment helper; residual cutout coverage uses an explicit reflection-alpha floor'}
        opaque=[];cutout=[]
        for tri in d['triangles']:
            probe={**d,'triangles':[tri]}
            try:covered_tri=covered_uv_footprint(probe)
            except ValueError:covered_tri=False
            if not covered_tri and e['date']:
                # Opaque triangles can preserve zero environment weight without
                # losing coverage. Cutouts need a separate proof that DATE does
                # not reject covered texels in their actual filtered footprint.
                pixels=bytearray(tex['rgba_ps2'])
                for i,(a,c) in enumerate(zip(alphas,covered)):pixels[4*i+3]=128 if not c or int(a>=128)==e['datm'] else 0
                probe={**probe,'texture':{**tex,'rgba_ps2':bytes(pixels)},'state':{**s,'alpha_test':True,'alpha_func':6,'alpha_ref':0}}
                if not covered_uv_footprint(probe):raise ValueError('paint cutout DATE excludes covered footprint; finer source role required')
            (opaque if covered_tri else cutout).append(tri)
        plans[no]=[(ts,{**info,'coverage':'opaque_uv_footprint' if mode=='opaque' else 'paint_cutout_floor',
            **({'alpha_floor':cutout_floor} if mode=='cutout' else {}),'partition':mode}) for mode,ts in [('opaque',opaque),('cutout',cutout)] if ts]
        for i in packets:consumed[i].add(no)
    if seen!=set(selected):raise ValueError('paint selector does not exist in selected source model/LOD')
    expanded=[]
    for no,d in enumerate(draws):
        if no in plans:
            uv_vertices=sorted({i for t in d['triangles'] for i in t})
            for triangles,info in plans[no]:expanded.append({**d,'triangles':triangles,'_mr_paint_reflection':info,'_mr_source_draw':no,'_mr_uv_vertices':uv_vertices})
        else:expanded.append({**d,**({'_mr_paint_consumed':sorted(consumed[no])} if no in consumed else {})})
    return expanded
