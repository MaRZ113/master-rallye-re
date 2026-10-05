"""Exact build-specific native registry tests using Ghidra, with typed boundaries."""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path('tools').resolve()))
sys.path.insert(0,str(Path('tools/scanner').resolve()))
from r_ai2_emulate import BoundedMachine
import pyghidra
import argparse
from research_build_profiles import identify,MERC_SHA256
parser=argparse.ArgumentParser(description='Bounded native exact Mercedes registry conversion tests; no game runtime')
parser.add_argument('--install',type=Path,required=True)
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--project',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
a=parser.parse_args()
from r_ai1_mixed_class import ignored_output
output=ignored_output(a.output)
profile=identify(a.source.read_bytes())
if profile['sha256']!=MERC_SHA256:raise ValueError('Exact Mercedes source required')
project=a.project.resolve()
if not project.is_relative_to(Path('research-output/r-observatory-modded-builds').resolve()):raise ValueError('Ghidra project must stay in ignored phase area without dot path elements')
pyghidra.start(install_dir=a.install)
ctx=pyghidra.open_program(a.source,project_location=project,project_name='MercAudit',analyze=False)
api=ctx.__enter__();g=api.getCurrentProgram();tx=g.startTransaction('unsaved native registry verification')
try:
 assert str(g.getExecutableSHA256())=='1fb0a1f1ba02cd05fa25f0c94558cf1b281fd12affcdc37bb3c1ca538e6c65af'
 rows=[]
 for id in range(27):
  cls,local=(0,7) if id==26 else (0,id) if id<7 else (1,id-7) if id<14 else (2,id-14)
  m=BoundedMachine(g,api,pyghidra.task_monitor(),0x481e50,(id,));owner=m.alloc(bytes(0x100));m.put('ECX',owner)
  def boundary(pc):
   sp=m.reg('ESP')
   if pc==0x4d0580:m.write(m.reg('ECX'),m.read(sp+4));m.ret(m.reg('ECX'),4)
   elif pc==0x4d8ec0:m.ret(0x730000)
   elif pc==0x4d8000:m.ret(None,8)
   elif pc==0x5b4c00:m.ret()
   else:return False
   return True
  try:
   m.execute_bounded(boundary,4)
   assert m.read(owner+0x10)==cls and m.read(owner+0x14+4*cls)==local
   rows.append(dict(id=id,**{'class':cls},local_index=local,native_reverse=True))
   m.emu.writeRegister('EIP',0x481e20);m.write(m.stack,m.stop);m.put('ESP',m.stack);m.put('ECX',owner)
   m.execute_bounded(lambda pc:False)
   assert m.reg('EAX')==id;rows[-1]['native_forward']=True
  finally:m.emu.dispose()
 m=BoundedMachine(g,api,pyghidra.task_monitor(),0x68e2a0);owner=m.alloc(bytes(0xc34));m.put('ESI',owner);m.saved['ESI']=owner;m.put('ECX',owner)
 calls=[]
 def init_boundary(pc):
  sp=m.reg('ESP')
  if pc==0x4d11d0:m.write(m.reg('ECX'),m.read(sp+4));m.ret(m.reg('ECX'),4)
  elif pc==0x45a0b0:
   args=[m.read(sp+4*i) for i in range(1,13)]
   calls.append(dict(record_offset=m.reg('ECX')-owner,args=args,family=m.text(args[7])))
   m.ret(None,48)
  elif pc==0x4598d0:m.ret()
  else:return False
  return True
 try:m.execute_bounded(init_boundary)
 finally:m.emu.dispose()
 assert [(r['record_offset'],r['args'][0],r['args'][1],r['family']) for r in calls]==[(0x518,25,2,'Trooper'),(0x54c,26,0,'Mercedes')]
 out=dict(status='NATIVE_STATIC_PASS',runtime_game_test=False,round_trips=rows,initializers=calls,cases_passed=56,failed=0,skipped=0,boundaries=['typed Broker/string operations','record initializer captured at native entry, not invoked','secondary RaceTest constructor'])
 output.write_text(json.dumps(out,indent=2)+'\n')
 print('Native registry:',out['cases_passed'],'passed, 0 failed, 0 skipped')
finally:g.endTransaction(tx,False);ctx.__exit__(None,None,None)
