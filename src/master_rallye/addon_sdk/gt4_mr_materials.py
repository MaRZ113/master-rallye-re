"""Conservative GS environment-pair admission for the native MR helper family.

No shape IDs or numeric material names. Pair exact triangle geometry and admit
only opaque, hole-free coverage with a provably passing DATE condition. The
user-selected MR environment image is an explicit renderer approximation.
"""
from collections import defaultdict
import math
from .gt4_materials import alpha_compare


def geometry_key(draw):
    return tuple(sorted(tuple(sorted(tuple(draw['vertices'][i]['position']) for i in tri)) for tri in draw['triangles']))


def environment_pairs(draws):
    base=defaultdict(list)
    for index,d in enumerate(draws):
        if not d['issues']:base[geometry_key(d)].append(index)
    admitted={};consumed={}
    for index,d in enumerate(draws):
        if d['issues']!=['runtime-generated external texture / texgen unavailable']:continue
        st=d['state']
        if st['blend'][:4]!=[0,2,1,1] or st['fbmask']&0xffffff or not d['gif']['blend']:continue
        candidates=base[geometry_key(d)]
        if len(candidates)!=1:continue
        target=candidates[0];b=draws[target];s=b['state'];tex=b['texture']
        if target in admitted or b['gif']['blend'] or not s['depth_write'] or s['fbmask'] or s['date'] or not tex:continue
        if tex['registers']['tfx']!=0 or not tex['registers']['tcc']:continue
        used={i for tri in b['triangles'] for i in tri}
        if any(b['vertices'][i]['normal'] is None or (b['vertices'][i]['rgba_ps2'] or [128]*4)[3]!=128 for i in used):continue
        alphas=set(tex['rgba_ps2'][3::4])
        if not all(not s['alpha_test'] or alpha_compare(a,s['alpha_func'],s['alpha_ref']) for a in alphas):continue
        if st['date'] and any(int(a>=128)!=st['datm'] for a in alphas):continue
        # MR COLOROP18: base RGB + base alpha * helper RGB. Source GS uses
        # Cd + Ad/128 * generated-environment RGB, including vertex RGB gain.
        colours={tuple(d['vertices'][i]['rgba_ps2'] or [128]*4)[:3] for tri in d['triangles'] for i in tri}
        if len(colours)!=1:continue
        gain=next(iter(colours))
        admitted[target]={'source_environment_packet':index,'gain_rgb':[v/128 for v in gain],
            'rule':'exact triangle pair; source coverage and DATE pass for all texels; preserve source base alpha as reflection weight',
            'approximation':'user-supplied MR normal-coordinate helper replaces GT4 runtime-generated environment; no GT4 lighting/texgen parity claim'}
        consumed[index]=target
    return admitted,consumed


def oriented_triangle_key(draw,tri):
    ps=tuple(tuple(draw['vertices'][i]['position']) for i in tri)
    return min(ps,ps[1:]+ps[:1],ps[2:]+ps[:2])


def _box_touches_triangle(tri,lo,hi):
    # Separating-axis test, including the rectangle axes. Boundary contact is
    # included: acceptance must cover bilinear filtering at triangle edges.
    axes=[(1.,0.),(0.,1.)]
    for a,b in zip(tri,tri[1:]+tri[:1]):axes.append((a[1]-b[1],b[0]-a[0]))
    corners=((lo[0],lo[1]),(lo[0],hi[1]),(hi[0],lo[1]),(hi[0],hi[1]))
    for x,y in axes:
        p=[x*u+y*v for u,v in tri];q=[x*u+y*v for u,v in corners]
        if max(p)<min(q)-1e-12 or max(q)<min(p)-1e-12:return False
    return True


def covered_uv_footprint(draw,*,budget=2000000):
    """Conservative source-coverage proof over every bilinear texel footprint.

    UVs are neither clamped per vertex nor sampled on a sparse diagnostic grid.
    Unsupported region-repeat or excessive work rejects admission safely.
    """
    tex=draw['texture'];reg=tex['registers'];w,h=tex['width'],tex['height'];alpha=tex['rgba_ps2'][3::4];s=draw['state']
    passed=[not s['alpha_test'] or alpha_compare(a if reg['tcc'] else 128,s['alpha_func'],s['alpha_ref']) for a in alpha]
    if all(passed):return True
    def address(n,size,axis):
        mode=reg['wrap_s' if axis==0 else 'wrap_t']
        if mode==0:return n%size
        if mode==1:return min(size-1,max(0,n))
        if mode==2:return min(reg['max_u' if axis==0 else 'max_v'],max(reg['min_u' if axis==0 else 'min_v'],n))
        raise ValueError('region repeat is not qualified for coverage proof')
    visited=0
    for indices in draw['triangles']:
        uv=[draw['vertices'][i]['uv'] for i in indices]
        if any(p is None or not all(math.isfinite(v) for v in p) for p in uv):return False
        tri=tuple((p[0]*w,p[1]*h) for p in uv)
        x0=math.floor(min(p[0] for p in tri)-.5);x1=math.floor(max(p[0] for p in tri)+.5)
        y0=math.floor(min(p[1] for p in tri)-.5);y1=math.floor(max(p[1] for p in tri)+.5)
        visited+=(x1-x0+1)*(y1-y0+1)
        if visited>budget:return False
        for y in range(y0,y1+1):
            for x in range(x0,x1+1):
                if not passed[address(y,h,1)*w+address(x,w,0)] and _box_touches_triangle(tri,(x-.5,y-.5),(x+1.5,y+1.5)):
                    return False
    return True


def qualified_environment_pairs(draws):
    """Opt-in GT4 body interpretation, preserving the legacy strict rule.

    Match oriented triangles across packet boundaries. Coverage and DATE are
    independent proofs; source alpha is reflection weight, not an opacity guess.
    No numeric material names, paint-colour heuristics or vehicle IDs are used.
    """
    admitted,consumed=environment_pairs(draws);env=defaultdict(list)
    for no,d in enumerate(draws):
        s=d['state']
        if d.get('component','body')!='body' or d['issues']!=['runtime-generated external texture / texgen unavailable']:continue
        if not d['gif']['blend'] or s['blend'][:4]!=[0,2,1,1] or s['fbmask']&0xffffff or s['depth_write'] or s['alpha_test']:continue
        colours={tuple(d['vertices'][i]['rgba_ps2'] or [128]*4)[:3] for t in d['triangles'] for i in t}
        if len(colours)!=1:continue
        for tri in d['triangles']:env[oriented_triangle_key(d,tri)].append((no,next(iter(colours))))
    for no,b in enumerate(draws):
        s=b['state'];tex=b['texture']
        if no in admitted or b.get('component','body')!='body' or b['issues'] or b['gif']['blend'] or not s['depth_write'] or s['fbmask'] or s['date'] or not tex:continue
        reg=tex['registers'];used={i for t in b['triangles'] for i in t}
        if reg['tfx']!=0 or not reg['tcc'] or any(b['vertices'][i]['normal'] is None or (b['vertices'][i]['rgba_ps2'] or [128]*4)[3]!=128 for i in used):continue
        matches=[env.get(oriented_triangle_key(b,t),[]) for t in b['triangles']]
        if not matches or any(len(v)!=1 for v in matches):continue
        colours={v[0][1] for v in matches};packets=sorted({v[0][0] for v in matches})
        if len(colours)!=1:continue
        states=[draws[i]['state'] for i in packets]
        if len({(v['date'],v['datm']) for v in states})!=1:continue
        e=states[0];alphas=tex['rgba_ps2'][3::4]
        coverage=[not s['alpha_test'] or alpha_compare(a,s['alpha_func'],s['alpha_ref']) for a in alphas]
        weights=[min(255,a*255//128) if c and (not e['date'] or int(a>=128)==e['datm']) else 0 for a,c in zip(alphas,coverage)]
        if not any(weights):continue
        try:opaque=covered_uv_footprint(b)
        except ValueError:opaque=False
        # MR GREATER128 can preserve both a cutout and the exact reflection
        # weight only when every covered texel's weight is itself >128.
        cutout=not opaque and all((v>128)==c for v,c in zip(weights,coverage))
        if not opaque and not cutout:continue
        admitted[no]={'source_environment_packets':packets,'gain_rgb':[v/128 for v in next(iter(colours))],
            'coverage':'opaque_uv_footprint' if opaque else 'exact_GREATER128_cutout',
            'date':e['date'],'datm':e['datm'],
            'rule':'complete oriented triangle correspondence; source coverage proof; per-texel DATE gates reflection only',
            'approximation':'MR normal-coordinate helper replaces GT4 generated environment; source UVs/RGB retained'}
        for index in packets:consumed[index]=sorted(set(([consumed[index]] if isinstance(consumed.get(index),int) else consumed.get(index,[]))+[no]))
    return admitted,consumed
