"""Optional planar UV clamp subdivision, preserving original surface coverage.

Partition triangles at clamp planes before saturating UVs. Unlike clamping
original vertices, this retains the source interpolation within each addressed
region. Positions/normals are interpolated; source RGBA is quantized to bytes.
No triangles outside the texture rectangle are discarded.
"""
import math

def refine(draw,*,triangle_budget=200000):
    if type(triangle_budget)is not int or not 1<=triangle_budget<=200000:raise ValueError('Clamp triangle budget bounds')
    tex=draw['texture']
    if tex is None:return draw,{'changed':False}
    reg=tex['registers'];planes=[];ranges={}
    for axis,size in enumerate((tex['width'],tex['height'])):
        mode=reg['wrap_s'if axis==0 else'wrap_t']
        if mode==0:continue
        if mode not in (1,2):raise ValueError('Clamp subdivision cannot infer region-repeat addressing')
        lo=reg['min_u'if axis==0 else'min_v']if mode==2 else 0
        hi=reg['max_u'if axis==0 else'max_v']if mode==2 else size-1
        if not 0<=lo<=hi<size:raise ValueError('Clamp subdivision region outside texture')
        ranges[axis]=(lo/size,(hi+1)/size);planes.extend((axis,b)for b in ranges[axis])
    if not planes:return draw,{'changed':False}
    if '_mr_uv_vertices'in draw or any(v.get('morph_target')for v in draw['vertices']):raise ValueError('Clamp subdivision requires separately qualified morph/UV ownership')
    source=draw['vertices'];out=[];triangles=[];lookup={};splits=0
    for tri in draw['triangles']:
        if len(tri)!=3 or any(type(i)is not int or not 0<=i<len(source)for i in tri):raise ValueError('Clamp triangle index outside source')
    for v in source:
        for key,count in (('position',3),('normal',3),('uv',2),('rgba_ps2',4)):
            value=v.get(key)
            if value is not None and (len(value)!=count or not all(math.isfinite(x)for x in value)):raise ValueError('Clamp invalid source attribute')
    def interpolate(a,b,t,axis,boundary):
        v=dict(a)
        for key in ('position','normal','uv','rgba_ps2'):
            x,y=a.get(key),b.get(key)
            if x is None and y is None:v[key]=None;continue
            if key=='rgba_ps2':x=x or (128,128,128,128);y=y or (128,128,128,128)
            if x is None or y is None:raise ValueError('Clamp subdivision mixed source attributes')
            values=tuple(p+(q-p)*t for p,q in zip(x,y))
            v[key]=values
        uv=list(v['uv']);uv[axis]=boundary;v['uv']=tuple(uv)
        return v
    def split(poly,axis,boundary):
        values=[v['uv'][axis]for v in poly]
        if min(values)>=boundary-1e-12 or max(values)<=boundary+1e-12:return [poly]
        low=[];high=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            av,bv=a['uv'][axis]-boundary,b['uv'][axis]-boundary
            if av<=0:low.append(a)
            if av>=0:high.append(a)
            if av*bv<0:
                p=interpolate(a,b,-av/(bv-av),axis,boundary);low.append(p);high.append(p)
        return [p for p in (low,high)if len(p)>=3]
    def index(v):
        uv=list(v['uv'])
        for axis,(lo,hi)in ranges.items():uv[axis]=min(hi,max(lo,uv[axis]))
        n=dict(v);n['uv']=tuple(uv)
        if n.get('rgba_ps2')is not None:n['rgba_ps2']=tuple(max(0,min(255,round(p)))for p in n['rgba_ps2'])
        # Packet identity is retained even for coincident vertices in separate
        # source packets. Other metadata remains on each derived vertex.
        key=tuple(tuple(n[k])if n.get(k)is not None else None for k in ('position','normal','uv','rgba_ps2'))+(n.get('packet_offset'),)
        if key not in lookup:lookup[key]=len(out);out.append(n)
        return lookup[key]
    if len(draw['triangles'])>triangle_budget:raise ValueError('Clamp source triangle budget')
    for tri in draw['triangles']:
        poly=[source[i]for i in tri]
        if any(v['uv']is None or not all(math.isfinite(x)for x in v['uv'])for v in poly):raise ValueError('Clamp subdivision needs finite source UVs')
        polygons=[poly]
        for axis,boundary in planes:polygons=[p for old in polygons for p in split(old,axis,boundary)]
        splits+=len(polygons)-1
        for p in polygons:
            ids=[index(v)for v in p]
            for i in range(1,len(ids)-1):
                t=(ids[0],ids[i],ids[i+1])
                triangles.append(t)
        if len(triangles)>triangle_budget or len(out)>600000:raise ValueError('Clamp derived geometry budget')
    result=dict(draw);result['vertices']=out;result['triangles']=triangles
    return result,{'changed':True,'source_triangles':len(draw['triangles']),'derived_triangles':len(triangles),'partitions':splits,'uv_clamp_ranges':ranges,'source_texture_resolution_unchanged':True,'surface':'Original triangle planes and boundary retained; no outside geometry discarded','rgba_boundary':'New vertex RGBA rounded to nearest byte; max local rounding error half a source-byte unit','lighting_boundary':'Interpolated normals retain direction/length; fixed-function per-vertex lighting may differ slightly at added vertices.'}
