"""GPU smoke checks for the Windows viewer; generated asymmetric SDK fixture.

No retail/GT fixture is bundled. Optional stock resources are supplied by the
user. Captures prove this application's behavior, not original-game parity.
"""
from __future__ import annotations
import argparse,hashlib,json,struct,subprocess,sys
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from master_rallye.preview_scene import stage_vehicle
from master_rallye.scene_dx_writer import ScenePart,write_scene_dx
from master_rallye.topology_writer import CompiledVertex,DrawGeometry

def fixture(root,*,vertical=False):
    root.mkdir(parents=True,exist_ok=True)
    points=[(-1.,-1.,0.),(1.,-1.,0.),(1.,1.,0.),(-1.,1.,0.)]
    b=bytearray(struct.pack('<4I',0xd00d,135,1337,4))
    for p in points:b.extend(struct.pack('<3f',*p))
    b.extend(struct.pack('<3f',0,0,1)*4+b'\xff'*16+struct.pack('<I',1))
    for uv in ((0,1),(1,1),(1,0),(0,0)):b.extend(struct.pack('<2f',*uv))
    # Wire winding swaps first two corners relative to stored-global indices.
    b.extend(struct.pack('<I6H2I',6,1,0,2,2,0,3,1,1))
    b.extend(struct.pack('<7If4BI',2,0,3,0,6,1,0,1.,0,0,0,1,3)+struct.pack('<I',3))
    for s in ('asymmetric-tga','Null','Null'):
        raw=s.encode('ascii');b.extend(struct.pack('<I',len(raw))+raw)
    b.extend(struct.pack('<I2I6I',0,1,6,0,1,2,0,2,3))
    b.extend(struct.pack('<IffI3ff6f',102,.4,.2,1339,0,0,0,1.5,-1,-1,0,1,1,0))
    path=root/'asymmetric.dx';path.write_bytes(b)
    # Red on source -X, blue on source +X; no row ambiguity in a 2x1 texture.
    (root/'asymmetric-tga.dxt').write_bytes(struct.pack('<5I',0xfeed,1,0,1 if vertical else 2,2 if vertical else 1)+bytes([0,0,255,255,255,0,0,255]))
    return path


def depth_fixture(root):
    """Stress sorting: one decal draw spans a front overlay and a far quad.

    Transparent texels must not erase a later glass draw when native instance
    ZWrite is enabled. This is synthetic, not a claim about native queue order.
    """
    template=fixture(root).read_bytes()
    def quad(x,z):return [(x-1.,-1.,z),(x+1.,-1.,z),(x+1.,1.,z),(x-1.,1.,z)]
    def geometry(points,tris):
        return DrawGeometry(tuple(CompiledVertex(p,(0.,0.,1.),b'\xff'*4,((.5,.5),)) for p in points),tuple(tris))
    triangles=((0,1,2),(0,2,3))
    overlay=geometry(quad(0,.1)+quad(4,-4),triangles+((4,5,6),(4,6,7)))
    glass=geometry(quad(0,0),triangles)
    for stem,pixel in [('empty-tga',bytes((255,255,255,0))),('glass-tga',bytes((255,0,0,128)))]:
        (root/(stem+'.dxt')).write_bytes(struct.pack('<5I',0xfeed,1,0,1,1)+pixel)
    paths={}
    for corrected in (False,True):
        path=root/('cutout.dx' if corrected else 'blended.dx')
        path.write_bytes(write_scene_dx(template,[ScenePart(overlay,('empty-tga','Null','Null'),alpha=True,alpha_test=corrected),
            ScenePart(glass,('glass-tga','Null','Null'),alpha=True)]));paths[corrected]=path
    return paths

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--viewer',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--stock',type=Path);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True);source=fixture(a.output/'synthetic');scene=a.output/'synthetic.mrpv';stage_vehicle(source,scene)
    capture=a.output/'asymmetric-front.bmp'
    subprocess.run([str(a.viewer.resolve()),'--scene',str(scene.resolve()),'--capture',str(capture.resolve()),'--preset','1'],check=True,timeout=30)
    image=Image.open(capture).convert('RGB');w,h=image.size
    red=[];blue=[]
    for x in range(w):
        r,g,b=image.getpixel((x,h//2))
        if r>220 and b<35 and g<35:red.append(x)
        if b>220 and r<35 and g<35:blue.append(x)
    if not red or not blue or sum(red)/len(red)>=sum(blue)/len(blue):raise AssertionError('right-handed camera regression: source -X red must appear left of source +X blue')
    report={'status':'PASS_NATIVE_GPU_SMOKE','handedness':'source -X/red left, +X/blue right; no horizontal mirror',
            'synthetic_capture_sha256':hashlib.sha256(capture.read_bytes()).hexdigest(),'captures':[],'runtime_game_parity':False}
    # A single outward +Z quad must disappear from behind with the calibrated
    # cull state. NONE used to conceal incorrect race-wheel template sides.
    def coloured_pixels(path):
        return sum((r>220 and g<35 and b<35) or (b>220 and r<35 and g<35)
                   for r,g,b in Image.open(path).convert('RGB').getdata())
    culling={}
    for preset,mode in ((1,'cw'),(2,'cw'),(1,'ccw'),(2,'ccw'),(2,'none')):
        target=a.output/f'cull-{preset}-{mode}.bmp'
        subprocess.run([str(a.viewer.resolve()),'--scene',str(scene.resolve()),'--capture',str(target.resolve()),
                        '--preset',str(preset),'--cull',mode],check=True,timeout=30)
        culling[f'{preset}-{mode}']=coloured_pixels(target)
    if not (culling['1-cw']>100 and culling['2-cw']==0 and culling['1-ccw']==0
            and culling['2-ccw']>100 and culling['2-none']>100):
        raise AssertionError(f'outside/backface culling regression: {culling}')
    report['culling']={'status':'PASS_FRONT_BACK_AND_DIAGNOSTIC_NONE','coloured_pixels':culling}
    vertical=fixture(a.output/'synthetic-vertical',vertical=True);vscene=a.output/'vertical.mrpv';stage_vehicle(vertical,vscene)
    target=a.output/'asymmetric-vertical.bmp'
    subprocess.run([str(a.viewer.resolve()),'--scene',str(vscene.resolve()),'--capture',str(target.resolve()),'--preset','1'],check=True,timeout=30)
    image=Image.open(target).convert('RGB');w,h=image.size;red=[];blue=[]
    for y in range(h):
        r,g,b=image.getpixel((w//2,y))
        if r>220 and b<35 and g<35:red.append(y)
        if b>220 and r<35 and g<35:blue.append(y)
    if not red or not blue or sum(red)/len(red)>=sum(blue)/len(blue):raise AssertionError('raw DXT row regression: row0/red must appear above row1/blue')
    report['vertical_orientation']='PASS_GPU: stored row0/red above row1/blue with original source UVs'
    depth={}
    for corrected,path in depth_fixture(a.output/'depth-fixture').items():
        scene_path=a.output/f'depth-{int(corrected)}.mrpv';stage_vehicle(path,scene_path)
        for policy in ('instance-on','shader'):
            target=a.output/f'depth-{int(corrected)}-{policy}.bmp'
            subprocess.run([str(a.viewer.resolve()),'--scene',str(scene_path.resolve()),'--capture',str(target.resolve()),
                '--preset','1','--depth-write',policy],check=True,timeout=30)
            depth[f'{int(corrected)}-{policy}']=sum(b>200 and r<130 and g<140 for r,g,b in Image.open(target).convert('RGB').getdata())
    if not (depth['0-shader']>20 and depth['0-instance-on']<depth['0-shader']*.01
            and depth['1-instance-on']==depth['0-shader']==depth['1-shader']):
        raise AssertionError(f'transparent depth ownership regression: {depth}')
    report['transparent_depth']={'status':'PASS_NATIVE_INSTANCE_DEPTH_STRESS','blue_glass_pixels':depth,
        'boundary':'synthetic sort stress, not original-game queue parity'}
    if a.stock:
        stage_vehicle(a.stock/'complete.dx',a.output/'stock.mrpv')
        for model,preset,brake,env in [('frontend',4,False,True),('frontend',4,False,False),('race',2,False,True),('race',2,True,True),('wheel',4,False,True)]:
            name=f'{model}-{preset}-brake{int(brake)}-env{int(env)}.bmp';target=a.output/name
            args=[str(a.viewer.resolve()),'--scene',str((a.output/'stock.mrpv').resolve()),'--model',model,'--preset',str(preset),'--capture',str(target.resolve())]
            if brake:args+=['--brake']
            if not env:args+=['--no-reflections']
            subprocess.run(args,check=True,timeout=30)
            report['captures'].append({'file':name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
        front=Image.open(a.output/'frontend-4-brake0-env1.bmp');off=Image.open(a.output/'frontend-4-brake0-env0.bmp')
        if front.tobytes()==off.tobytes():raise AssertionError('reflection toggle produced no visible difference on stock input')
        normal=Image.open(a.output/'race-2-brake0-env1.bmp');lit=Image.open(a.output/'race-2-brake1-env1.bmp')
        if normal.tobytes()==lit.tobytes():raise AssertionError('brake switch produced no visible difference on stock input')
        report.update(reflection_toggle='PASS',brake_toggle='PASS')
    (a.output/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
