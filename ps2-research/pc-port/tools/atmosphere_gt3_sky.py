"""Source-bound GT3 reverse-course sky projection to a private MR cylindrical pair.
Uses the installed GTPS2ModelTool texture decoder, plus a bounded VIF/shape parser.
No source assets or original game data are written. This is an authored projection,
not a claim that Master Rallye renders the GT3 sky geometry identically.
"""
from pathlib import Path
import argparse, gzip, hashlib, json, struct, subprocess, sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]

def sha(b):return hashlib.sha256(b).hexdigest()
def word(b,o):return struct.unpack_from('<I',b,o)[0]
def shapes(b):
    if b[:4]!=b'GTM1':raise ValueError('not GTM1')
    models,n,_,nt=struct.unpack_from('<4H',b,16);mt,st=struct.unpack_from('<2I',b,32)
    if not 1<=n<=32 or models!=n or nt!=n:raise ValueError('unsupported sky set layout')
    for i in range(n):
        mo=word(b,mt+4*i)
        # Source BBoxRender(count8), jump7, SetTexTable(i), CallShape(i), Enable.
        if b[mo:mo+2]!=bytes((10,8)) or b[mo+98:mo+105]!=bytes((7,0,43,i,4,i,11)):
            raise ValueError('unknown sky shape/texture binding')
        off=word(b,st+4*i);_,_,packets,nv,nt=struct.unpack_from('<BBHHH',b,off+8)
        total_v=total_t=0
        for j in range(packets):
            rel,qwords,packed=struct.unpack_from('<IHH',b,off+16+j*8)
            if packed&511!=1:raise ValueError('unexpected texture within single-texture sky set')
            at=off+rel;end=at+qwords*16;parts={}
            while at<end:
                addr,num,op=struct.unpack_from('<HBB',b,at);op&=127;at+=4;size=0
                if addr==0xc0c0:size=12
                elif op in (0x30,0x31):size=16
                elif op==0x20:size=4
                elif op&0x60==0x60:
                    if op&3==3 or not num:raise ValueError('unsupported UNPACK')
                    size=num*((op>>2&3)+1)*(4>>(op&3));parts[(addr,op&0x6f)]=(num,b[at:at+size])
                elif op not in (0,1,2,3,4,5,6,7,0x10,0x11,0x13,0x14,0x15,0x17):raise ValueError('unknown VIF')
                at=(at+size+3)&~3
            if at!=end:raise ValueError('VIF payload outside packet')
            v=np.frombuffer(parts[(0xc000,0x68)][1],'<f4').reshape(-1,3).copy()
            uv=np.frombuffer(parts[(0xc040,0x64)][1],'<f4').reshape(-1,2).copy()
            colors=np.frombuffer(parts[(0xc080,0x6e)][1],'u1').reshape(-1,4).copy()
            resets=parts[(0xc040,0x62)][1];lengths=[(x+6)//3 for x in resets[1:]]
            if len(v)!=len(uv) or len(v)!=len(colors) or sum(lengths)!=len(v) or resets[0]!=len(lengths):raise ValueError('inconsistent strips')
            start=0;tri=[]
            for length in lengths:
                for k in range(length-2):tri.append((start+k,start+k+1,start+k+2) if not k%2 else (start+k+2,start+k+1,start+k))
                start+=length
            total_v+=len(v);total_t+=len(tri)
            yield i,v,uv,colors,np.asarray(tri)
        if total_v!=nv or total_t!=nt:raise ValueError('shape declaration mismatch')

def project(b,textures,width=512,height=192):
    # One native MR cylinder turn is U=2. Runtime CustomSkyUScale=.5 removes the
    # otherwise duplicated panorama. Stored MR row0 is the horizon, not zenith.
    u=(np.arange(width)+.5)/width;v=(np.arange(height)+.5)/height
    theta=(1.5-2*u)*np.pi;elev=np.arctan(np.maximum(0,(v-.003)/.995))
    dirs=np.stack(np.broadcast_arrays(np.cos(elev)[:,None]*np.cos(theta)[None,:],np.sin(elev)[:,None],np.cos(elev)[:,None]*np.sin(theta)[None,:]),axis=-1).reshape(-1,3)
    distances=np.full(len(dirs),np.inf);rgb=np.zeros((len(dirs),3),np.float64)
    triangles=0
    for tex,vertices,uv,colors,faces in shapes(b):
        rgba=np.asarray(textures[tex].convert('RGBA'))
        if not rgba[:,:,3].max():continue # native fully transparent helper surface
        if rgba[:,:,3].min()!=255:raise ValueError('unsupported partially transparent GT3 sky surface')
        image=rgba[:,:,:3];h,w=image.shape[:2]
        for face in faces:
            triangles+=1;a,c,d=vertices[face].astype(float);edge1=c-a;edge2=d-a
            cross=np.cross(dirs,edge2);det=cross@edge1;valid=np.abs(det)>1e-10
            inv=np.divide(1,det,out=np.zeros_like(det),where=valid);tvec=-a
            p=(cross@tvec)*inv;qvec=np.cross(tvec,edge1);q=(dirs@qvec)*inv;t=float(edge2@qvec)*inv
            hit=valid&(p>=-1e-6)&(q>=-1e-6)&(p+q<=1.000001)&(t>1e-6)&(t<distances)
            ids=np.flatnonzero(hit)
            if not len(ids):continue
            weights=np.stack((1-p[ids]-q[ids],p[ids],q[ids]),axis=1)
            coords=weights@uv[face];x=np.clip(coords[:,0]*(w-1),0,w-1);y=np.clip(coords[:,1]*(h-1),0,h-1)
            xi=x.astype(int);yi=y.astype(int);xn=np.minimum(xi+1,w-1);yn=np.minimum(yi+1,h-1);fx=(x-xi)[:,None];fy=(y-yi)[:,None]
            sample=(image[yi,xi]*(1-fx)+image[yi,xn]*fx)*(1-fy)+(image[yn,xi]*(1-fx)+image[yn,xn]*fx)*fy
            prelight=np.clip((weights@colors[face,:3])/128,0,2)
            rgb[ids]=sample*prelight;distances[ids]=t[ids]
    coverage=np.isfinite(distances).reshape(height,width)
    if coverage.mean()<.99:raise ValueError(f'incomplete sky ray coverage {coverage.mean()}')
    rgb=np.clip(rgb.reshape(height,width,3),0,255)
    # The native cap maps one texture row across its entire face. Fade the top
    # 15% to its azimuthal mean to avoid cap stripes, retaining source palette.
    for y in range(height):
        blend=np.clip((y/height-.85)/.15,0,1);rgb[y]=rgb[y]*(1-blend)+rgb[y].mean(axis=0)*blend
    return Image.fromarray(np.rint(rgb).astype('uint8')),{'ray_coverage':float(coverage.mean()),'source_triangles':triangles}

def export_pair(image,native,out):
    # Load the local SDK only in the standalone authoring path, not when tests
    # import the independent VIF decoder alongside another selected Course SDK.
    sys.path.insert(0,str(ROOT/'src'))
    from master_rallye.dxt import parse_dxt
    out.mkdir(parents=True,exist_ok=True);rgb=np.asarray(image.resize((256,256),Image.Resampling.LANCZOS)).copy()
    # Make the cylinder's wrap endpoints agree exactly (one bilinear seam).
    seam=np.rint((rgb[:,0].astype(float)+rgb[:,-1])/2).astype('uint8');rgb[:,0]=seam;rgb[:,-1]=seam
    fog=np.median(rgb[:6],axis=(0,1)).astype(int).tolist();rows=[]
    for layer,name in enumerate(('clouds','layer')):
        source=native/('cloud3-tga.dxt' if not layer else 'layer3-tga.dxt');t=parse_dxt(source)
        color=rgb if not layer else np.broadcast_to(np.rint(rgb.mean(axis=1,keepdims=True)).astype('uint8'),rgb.shape)
        # A smooth palette-matched haze overlay, not a second copy of the GT3
        # cloud silhouettes. Retain the native alpha mask byte-for-byte.
        bgra=np.empty((256,256,4),'uint8');bgra[:,:,:3]=color[:,:,::-1];bgra[:,:,3]=np.frombuffer(t.bgra,'uint8').reshape(256,256,4)[:,:,3]
        payload=t.header+bgra.tobytes();(out/(name+'.dxt')).write_bytes(payload);Image.fromarray(bgra[:,:,[2,1,0,3]]).save(out/(name+'.png'))
        rows.append({'name':name,'sha256':sha(payload),'alpha_sha256':sha(bgra[:,:,3].tobytes()),'native_alpha_sha256':sha(t.bgra[3::4]),'horizontal_edge_delta_max':int(np.abs(bgra[:,0,:3].astype(int)-bgra[:,-1,:3]).max())})
    return {'fog_rgb':fog,'custom_sky_u_scale':.5,'resources':rows,'layer_policy':'native-alpha-preserving palette haze; no duplicated GT3 silhouettes'}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--courses',type=Path,required=True);ap.add_argument('--decoder',type=Path,required=True);ap.add_argument('--native',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve()
    if out.exists():raise ValueError('fresh output required')
    for source in (a.courses.resolve(),a.native.resolve()):
        if out==source or source in out.parents or out in source.parents:raise ValueError('source/output overlap')
    out.mkdir(parents=True);reports=[]
    for course in ('r_deepforest','r_grandvalley'):
        source=a.courses/(course+'.gz');compressed=source.read_bytes();raw=gzip.decompress(compressed);start,end=struct.unpack_from('<2I',raw,0x54)
        model=raw[start:end]
        if not 0<start<end<=len(raw) or model[:4]!=b'GTM1':raise ValueError('invalid GT3 sky member')
        path=out/(course+'.sky.gtm1');path.write_bytes(model)
        textures=[];tex_sources=[];table=word(model,44)
        for i in range(struct.unpack_from('<H',model,22)[0]):
            at=word(model,table+4*i);size=word(model,at+12);member=model[at:at+size]
            if member[:4]!=b'Tex1' or len(member)!=size or struct.unpack_from('<H',member,20)[0]!=1:raise ValueError('invalid single-texture member')
            tp=out/(course+f'-texture{i}.tex1');tp.write_bytes(member)
            run=subprocess.run([str(a.decoder.resolve()),'dump','-i',str(tp)],cwd=out,capture_output=True,text=True)
            (out/(course+f'-texture{i}-decoder.log')).write_text(run.stdout+run.stderr)
            if run.returncode:raise ValueError('standalone Tex1 decoder failed')
            textures.append(Image.open(tp.with_suffix('.png')).convert('RGBA'))
            tex_sources.append({'offset_in_gtm1':at,'size':size,'sha256':sha(member)})
        pano,detail=project(model,textures);pano.save(out/(course+'-panorama.png'))
        report={'course':course,'source':str(source.resolve()),'compressed_sha256':sha(compressed),'decompressed_sha256':sha(raw),'sky_member_offset':start,'sky_member_end':end,'gtm1_sha256':sha(model),'source_binding':'course header +0x54/+0x58; GTM1 BBox->SetTexTable->CallShape; VIF strip/UV/color validation','projection':'authored MR cylinder-compatible upper sky; not GT3 runtime parity','tex1_members':tex_sources,'textures':[{'index':i,'size':list(t.size),'rgba_sha256':sha(t.tobytes())} for i,t in enumerate(textures)],**detail,**export_pair(pano,a.native,out/'sets'/course)}
        reports.append(report)
    (out/'provenance.json').write_text(json.dumps({'schema':1,'status':'SOURCE_DECODED_DERIVED_PROJECTION_RUNTIME_PENDING','decoder':str(a.decoder.resolve()),'decoder_sha256':sha(a.decoder.read_bytes()),'courses':reports},indent=2)+'\n')
    print(json.dumps([{'course':r['course'],'coverage':r['ray_coverage'],'fog':r['fog_rgb']} for r in reports]))
if __name__=='__main__':main()
