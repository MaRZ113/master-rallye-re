"""Export an Evo 2 SMF (from a POD) to OBJ+MTL+PNG using the reference decoders."""
import sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','decoders'))
from evo2_formats import pod2_members,member_bytes,parse_smf,decode_classic_tiff
BS=chr(92)
def export(pod_path,model,outdir):
    d=open(pod_path,'rb').read();M={m.name.upper().replace(BS,'/'):m for m in pod2_members(d)}
    smf=parse_smf(member_bytes(d,M['MODELS/'+model.upper()+'.SMF']))
    os.makedirs(outdir,exist_ok=True);stem=model.lower();V=[];T=[];groups={};texs=set()
    for o in smf['objects']:
        if not o['visible']:continue
        base=len(V)
        for v in o['vertices_by_frame'][0]:V.append(v[:3]);T.append(v[6:8])
        groups.setdefault(o['texture'],[]).extend([(base+a,base+b,base+c) for a,b,c in o['faces']])
    with open(os.path.join(outdir,stem+'.mtl'),'w') as f:
        for t in groups:
            f.write('newmtl %s\nKd 1 1 1\n'%t);key='ART/'+t.upper().rsplit('.',1)[0]+'.TIF'
            if key in M:
                try:
                    from PIL import Image
                    info,rgba,_,_=decode_classic_tiff(member_bytes(d,M[key]))
                    im=Image.frombytes('RGBA',(info['width'],info['height']),rgba)
                    im.save(os.path.join(outdir,t.lower()+'.png'));f.write('map_Kd %s.png\n'%t.lower())
                except Exception as e:print('tex fail',t,e)
    with open(os.path.join(outdir,stem+'.obj'),'w') as f:
        f.write('mtllib %s.mtl\n'%stem)
        for v in V:f.write('v %.4f %.4f %.4f\n'%tuple(v))
        for t in T:f.write('vt %.4f %.4f\n'%(t[0],1-t[1]))
        for t,F in groups.items():
            f.write('usemtl %s\n'%t)
            for a,b,c in F:f.write('f %d/%d %d/%d %d/%d\n'%(a+1,a+1,b+1,b+1,c+1,c+1))
    return len(V),sum(len(F) for F in groups.values())
if __name__=='__main__':print(export(sys.argv[1],sys.argv[2],sys.argv[3]))
