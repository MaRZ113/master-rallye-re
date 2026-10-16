"""One bounded current-instance query; read/query rights, no writes or polling."""
import argparse,json,pathlib,struct,sys,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'ps2-research/pc-port/tools'))
from rigid_lifecycle_probe import WindowsReadOnlyProcess

def main():
 a=argparse.ArgumentParser();a.add_argument('--pid',type=int,required=True);a.add_argument('--instance',type=lambda s:int(s,0),required=True);a.add_argument('--capture',type=pathlib.Path,required=True);a.add_argument('--output',type=pathlib.Path,required=True);args=a.parse_args()
 # Source records must be the user's CURRENT process/session, not historical pointers.
 rows=[json.loads(l) for l in args.capture.open()];r=next(x for x in rows if x.get('type')=='race_damage_draw' and not x['owner_context'] and x['instance']==args.instance)
 if not args.capture.name.startswith('race-damage-'+str(args.pid)+'-'):raise ValueError('capture/PID mismatch')
 q=WindowsReadOnlyProcess(args.pid)
 def u(a):return struct.unpack('<I',q.read(a,4))[0]
 try:
  i=r['instance'];packet=u(i+0xb0);model=u(i+0x8c)
  if packet!=r['packet'] or model!=r['model'] or u(packet+0x74)!=i:raise ValueError('Current owner no longer matches capture')
  private=u(i+0x90);normal=u(model+0x18)
  result={'pid':args.pid,'exe':q.identity,'source_capture':args.capture.name,'capture_sha256':hashlib.sha256(args.capture.read_bytes()).hexdigest(),'instance':i,'packet':packet,'model':model,'instance_plus90':private,'model_plus18':normal,'lists':[]}
  for label,l in [('private',private),('model',normal)]:
   if not l:result['lists'].append({'kind':label,'list':0});continue
   sentinel=u(l);node=u(sentinel+4);nodes=[]
   for n in range(32):
    if not node:break
    if any(x['pointer']==node for x in nodes):raise ValueError('cycle')
    v,child,nxt=struct.unpack('<3I',q.read(node,12));nodes.append({'pointer':node,'vtable':v,'child':child,'next':nxt});node=nxt
   result['lists'].append({'kind':label,'list':l,'sentinel':sentinel,'roots':nodes,'terminated':not node})
  captured={x['mesh'] for x in rows if x.get('type')=='race_damage_draw' and x['instance']==i}
  for l in result['lists']:
   if not l.get('roots'):continue
   root=l['roots'][0]['pointer'];node=u(root+4);children=[]
   for n in range(32):
    if not node:break
    if any(x['pointer']==node for x in children):raise ValueError('child cycle')
    vt,ch,nxt=struct.unpack('<3I',q.read(node,12));children.append({'pointer':node,'vtable':vt,'child':ch,'next':nxt});node=nxt
   l['children']=children;l['children_terminated']=not node
   owned={x['pointer'] for x in children};l['captured_mesh_count']=len(captured);l['captured_meshes_top_level_present']=len(owned&captured);l['captured_meshes_missing']=[hex(x) for x in sorted(captured-owned)]
  if u(i+0x90)!=private or u(i+0x8c)!=model or u(packet+0x74)!=i:raise ValueError('owner changed during bounded read')
  result['bytes_read']=q.bytes_read
  args.output.write_text(json.dumps(result,indent=2)+'\n')
 finally:q.close()
if __name__=='__main__':main()
