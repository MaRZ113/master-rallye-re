"""Bake clamp addressing into guarded power-of-two textures for MR wrap slots.

Repeat axes and wrapped UVs remain untouched. Clamp axes get edge extension
over the actual draw UV interval and an affine UV transform. No per-vertex
clamping distorts interpolated coordinates or seals geometry.
"""
from __future__ import annotations
import math

def guarded_clamp(width,height,rgba,registers,uvs,*,compact=False):
    if type(compact)is not bool:raise ValueError('compact clamp must be boolean')
    if len(rgba)!=width*height*4 or not uvs:raise ValueError('invalid clamp source')
    dimensions=[];offsets=[];maps=[]
    for axis,size in enumerate((width,height)):
        mode=registers['wrap_s' if axis==0 else 'wrap_t']
        if mode==0:dimensions.append(size);offsets.append(0);maps.append(list(range(size)));continue
        if mode not in (1,2):raise ValueError('region repeat requires separate qualification')
        low=min(v[axis] for v in uvs);high=max(v[axis] for v in uvs)
        if not math.isfinite(low+high):raise ValueError('nonfinite UV interval')
        lo=registers['min_u' if axis==0 else 'min_v'] if mode==2 else 0
        hi=registers['max_u' if axis==0 else 'max_v'] if mode==2 else size-1
        if not 0<=lo<=hi<size:raise ValueError('region clamp outside decoded image')
        if compact:
            # Only after planar clamp subdivision: keep the addressed source
            # texels at original density and an explicit bilinear guard. Region
            # Clamp may make part of the original atlas unreachable. Cropping
            # that part is lossless for this addressed draw, not downsampling.
            if low<lo/size-1e-9 or high>(hi+1)/size+1e-9:raise ValueError('Compact clamp requires subdivided bounded UVs')
            first=min(hi,max(lo,math.floor(low*size-.5)))-1
            last=min(hi,max(lo,math.ceil(high*size-.5)))+1
            extent=1
            while extent<last-first+1:extent*=2
            offset=-first
            dimensions.append(extent);offsets.append(offset)
            maps.append([min(hi,max(lo,x-offset)) for x in range(extent)])
            continue
        # Size in texels, not whole copies of the source image. The old rule
        # allocated at least four source widths even for UVs in [0, 1]. With
        # two clamped axes this consumed 16x the native texture-cache budget.
        # One extra texel beyond the draw interval covers bilinear footprints;
        # centre the source where possible for larger, symmetric mip guards.
        before=max(1,math.ceil(-low*size)+1)
        after=max(1,math.ceil((high-1)*size)+1)
        extent=1
        while extent<size+before+after:extent*=2
        if extent>size*16:raise ValueError('clamp guard expansion budget')
        offset=max(before,min((extent-size)//2,extent-size-after))
        dimensions.append(extent);offsets.append(offset)
        maps.append([min(hi,max(lo,x-offset)) for x in range(extent)])
    w,h=dimensions
    if w*h>4*1024*1024:raise ValueError('clamp texture pixel budget')
    out=bytearray(w*h*4)
    for y,sy in enumerate(maps[1]):
        row=bytearray()
        for sx in maps[0]:row.extend(rgba[(sy*width+sx)*4:(sy*width+sx)*4+4])
        out[y*w*4:(y+1)*w*4]=row
    converted=[((uv[0]*width+offsets[0])/w,(uv[1]*height+offsets[1])/h) for uv in uvs]
    return w,h,bytes(out),converted,{'source_dimensions':[width,height],'output_dimensions':[w,h],'guard_offsets':offsets,
        'rule':'texel-bounded affine UV remap plus clamped edge extension; repeat axes unchanged',
        'source_resolution_preserved':True,
        **({'compact_after_subdivision':True,'filter_boundary':'Bilinear source sampling retained; generated native mip/quality behavior requires owner comparison.'} if compact else {})}
