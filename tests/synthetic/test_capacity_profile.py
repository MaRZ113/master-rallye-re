"""Native capacity experiments; CPU mocks never imply a playable roster."""
import copy
from dataclasses import replace
import struct
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from master_rallye.addon_sdk.capacity_profile import SDK33,scenario,validate_profile,save_compatibility,layout
import sdk_capacity_native as native
from tests.synthetic.test_vehicle_registry_id26_patcher import retail_layout_fixture


def fixture():
    source=retail_layout_fixture();p=native.registry.parse_pe(source);image=bytearray(source)
    def put(a,b):
        at=native.registry.va_to_file_offset(p,a,len(b));image[at:at+len(b)]=b
    for a,raw in [(0x458cf3,'6a218d4604'),(0x458e45,'6a2183c604'),(0x686795,'6a216a348b45f0'),(0x4819a4,'83fe0d7cb1')]:put(a,bytes.fromhex(raw))
    put(0x45a3e0,struct.pack('<I',layout(33)['allocation_size']))
    for a in (0x458d12,0x458e2c,0x6867b3):put(a,struct.pack('<I',layout(33)['racetest_base']))
    for a,d in native.registry.SECONDARY_INIT_LEAS:put(a+2,struct.pack('<I',d+7*52))
    for a,d in native.registry.SECONDARY_CONSUMER_DISPS:put(a+3,struct.pack('<I',d+7*52))
    for a,n in ((0x68e638,8),(0x68e63f,12),(0x480a65,13)):put(a,struct.pack('<I',n))
    for a,target,op in ((0x481e20,0x10000100,0xe9),(0x481e50,0x10000110,0xe9),(0x458d3f,0x10000020,0xe8)):
        put(a,native.i0._rel32(a,target,op))
    return source,bytes(image),bytes(512)


def records(profile):
    result=[]
    for c,ids in profile['classes'].items():
        for local,i in enumerate(ids):
            if i>=33:
                result.append(replace(native.registry.ID26_DONOR_CLEANUP,slot_id=i,vehicle_class=int(c[1:])-1,
                    local_index=local,internal_name='Landcruiser',smallcarsheet_index=9))
    return result


class ProfileTests(unittest.TestCase):
    def test_save_catalog_rejects_rebinding_and_reads_high_ids_without_rewriting(self):
        from master_rallye.addon_sdk.roster_identity import catalog,preflight_player_state,preserve_reservations
        old=catalog([{'physical_id':i,'family':'Car'+str(i),'vehicle_class':'T2'} for i in (31,127,128,255,256)])
        new=copy.deepcopy(old);new['entries'].append({'physical_id':512,'family':'NewCar','vehicle_class':'T3'})
        for i in (31,127,128,255,256):
            raw=('<Game><Broker><Value Name="Frontend/QuickRace/Car0" Type="Int" Value="'+str(i)+'" /></Broker></Game>').encode()
            result=preflight_player_state(raw,old,new)
            self.assertEqual(result['selected_physical_ids']['Frontend/QuickRace/Car0'],i)
            self.assertFalse(result['save_bytes_modified']);self.assertFalse(result['runtime_qualified'])
        changed=copy.deepcopy(new);changed['entries'][0]['family']='DifferentCar'
        with self.assertRaisesRegex(ValueError,'rebound'):preserve_reservations(old,changed)
        new['entries'][0]['retired']=True
        with self.assertRaisesRegex(ValueError,'retired'):preflight_player_state(b'<Game><Broker><Value Name="MasterRallye/Car0/CarID" Type="Int" Value="31" /></Broker></Game>',old,new)
        report=preflight_player_state(b'<Game><Broker><Value Name="MasterRallye/GameSaved" Type="Bool" Value="True" /></Broker></Game>',old,new)
        self.assertTrue(report['status'].startswith('BLOCKED_ACTIVE'))
        for values in ('<Value Name="MasterRallye/Car0/CarID" Type="Int" Value="31"/><Value Name="MasterRallye/Car0/CarClass" Type="Int" Value="2"/>',
                       '<Value Name="RallyeCup/CurrentClass" Type="Int" Value="3"/>',
                       '<Value Name="MasterRallye/PlayerT1Car0" Type="Int" Value="31"/>'):
            with self.assertRaisesRegex(ValueError,'class|CarClass'):preflight_player_state(('<Game><Broker>'+values+'</Broker></Game>').encode(),old,old)

    def test_configurations_no_arbitrary_64_128_256_ceiling(self):
        for n,d in [(33,(8,12,13)),(64,(16,24,24)),(128,(32,48,48)),(256,(64,96,96)),(512,(128,192,192)),(1024,(256,384,384))]:
            p=scenario(n,d);self.assertEqual(p['layout']['record_count'],n)
            self.assertEqual(p['layout']['allocation_size'],4+52*n+39*44)
            self.assertEqual(p['profile_sha256'],validate_profile(p)['profile_sha256'])
            self.assertFalse(p['runtime_qualified'])
    def test_rejects_bad_ids_counts_and_implicit_reordering(self):
        for v in (True,-1,32,0x80000000):
            with self.assertRaises(ValueError):scenario(v,(8,12,13))
        p=scenario(64,(16,24,24));p['classes']['T1'][0],p['classes']['T1'][1]=1,0
        with self.assertRaises(ValueError):validate_profile(p)
        p=scenario(64,(16,24,24));p['classes']['T2'][-1]=p['classes']['T1'][-1]
        with self.assertRaises(ValueError):validate_profile(p)
    def test_budget_and_native_class_gates(self):
        p=scenario(1024,(256,384,384));p['memory_budget_bytes']=65536
        with self.assertRaisesRegex(ValueError,'budget'):validate_profile(p)
        p=scenario(64,(16,24,24));i=p['classes']['T1'].pop();p['classes']['T4']=[i]
        self.assertFalse(validate_profile(p)['runtime_installable'])
        with self.assertRaisesRegex(ValueError,'three classes'):native.extend_capacity_profile(*fixture(),p,records(p))
    def test_save_mapping_is_checked_without_touching_save_bytes(self):
        a=scenario(33,(8,12,13));b=scenario(256,(64,96,96))
        self.assertTrue(save_compatibility(a,b)['physical_ids_preserved'])
        self.assertFalse(save_compatibility(a,b)['active_championship_migration_qualified'])


class NativeCoreTests(unittest.TestCase):
    def build(self,n=256,d=(64,96,96)):
        p=scenario(n,d);src,parent,extension=fixture()
        image,blob,report=native.extend_capacity_profile(src,parent,extension,p,records(p))
        self.assertEqual(extension,blob[:len(extension)]);self.assertEqual(len(image),len(parent))
        self.assertFalse(report['runtime_installable']);self.assertGreaterEqual(report['private_allocation_size'],524288)
        for op in report['operations']:
            a=op['file_offset'];old=bytes.fromhex(op['original_bytes'])
            self.assertEqual(parent[a:a+len(old)],old)
        return p,image,blob,report
    def test_all_required_layout_owners_are_patched_together(self):
        p,image,blob,r=self.build()
        self.assertEqual(sum(x['name'].startswith('racetest_init_') for x in r['operations']),39)
        self.assertEqual(sum(x['name'].startswith('racetest_consumer_') for x in r['operations']),11)
        at=r['entries']['descriptor']-0x10000000
        self.assertEqual(struct.unpack_from('<4s6I',blob,at),(b'MRVC',1,44,256,52,3,0x45a3c0))
    def test_parent_preimage_failure_is_atomic(self):
        p=scenario(64,(16,24,24));src,parent,ext=fixture();bad=bytearray(parent);pe=native.registry.parse_pe(src)
        bad[native.registry.va_to_file_offset(pe,0x458cf3,1)]^=1;before=bytes(bad)
        with self.assertRaisesRegex(ValueError,'preimage'):native.extend_capacity_profile(src,bad,ext,p,records(p))
        self.assertEqual(bytes(bad),before)
    def test_sdk33_and_wide_boundary_native_helpers(self):
        try:
            from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
            from unicorn.x86_const import UC_X86_REG_EAX as EAX,UC_X86_REG_ECX as ECX,UC_X86_REG_EDX as EDX,UC_X86_REG_ESP as ESP,UC_X86_REG_ESI as ESI,UC_X86_REG_EBP as EBP,UC_X86_REG_EIP as EIP
        except ImportError:self.skipTest('Optional Unicorn is unavailable')
        for n,d in [(33,(8,12,13)),(64,(16,24,24)),(127,(31,48,48)),(128,(32,48,48)),(255,(63,96,96)),(256,(64,96,96)),(512,(128,192,192))]:
            p,image,blob,r=self.build(n,d)
            def machine():
                u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x400000)
                pe=native.registry.parse_pe(image)
                for s in pe['sections']:
                    u.mem_write(0x400000+s['rva'],image[s['raw_offset']:s['raw_offset']+s['raw_size']])
                u.mem_map(0x10000000,r['private_allocation_size']);u.mem_write(0x10000000,blob)
                u.mem_map(0x1000000,0x20000);u.mem_map(0x2000000,0x20000)
                u.reg_write(ESP,0x100fff0);u.mem_write(0x100fff0,struct.pack('<I',0x1001000));u.reg_write(ECX,0x2000000)
                return u
            def run(u,start,stop=0x1001000):
                u.emu_start(start,stop,count=200000)
                self.assertEqual(u.reg_read(EIP),stop)
            for c,ids in enumerate(p['classes'].values()):
                u=machine()
                for local,i in enumerate(ids):
                    u.reg_write(ESP,0x100fff0);u.reg_write(ECX,0x2000000)
                    u.mem_write(0x2000010,struct.pack('<I',c));u.mem_write(0x2000014+c*4,struct.pack('<I',local))
                    run(u,0x481e20);self.assertEqual(u.reg_read(EAX),i);self.assertEqual(u.reg_read(ESP),0x100fff4)
                    u.reg_write(ESP,0x100fff0);u.mem_write(0x100fff4,struct.pack('<I',i));run(u,0x481e50,0x481e89)
                    self.assertEqual(struct.unpack('<I',u.mem_read(0x2000010,4))[0],c)
                    self.assertEqual(struct.unpack('<I',u.mem_read(0x2000014+c*4,4))[0],local)
                    self.assertEqual(u.reg_read(ESP),0x100ffec)
            for c,local in ((3,0),(0,len(p['classes']['T1'])),(0,0xffffffff),(0xffffffff,0)):
                u=machine();u.mem_write(0x2000010,struct.pack('<I',c));u.mem_write(0x2000014,struct.pack('<I',local));run(u,r['entries']['forward'])
                self.assertEqual(u.reg_read(EAX),0xffffffff)
            # All three lifetime routes execute real widened native operands.
            for name,stop in [('construct_count',0x458cf8),('destruct_count',0x458e4a),('unwind_count',0x68679c)]:
                u=machine();u.reg_write(ESI,0x2000000);u.reg_write(EBP,0x2000100);run(u,r['entries'][name],stop)
                sp=u.reg_read(ESP);self.assertEqual(struct.unpack('<I',u.mem_read(sp+(4 if name=='unwind_count' else 0),4))[0],n)
            # Initializer calls are mocked, but stack cleanup and every written
            # record destination/32-bit ID are exercised by emitted x86 code.
            u=machine();seen=[];parent=0x10000020
            def callback(uc,at,size,user):
                if at not in (parent,native.registry.STRING_CONSTRUCTOR_VA,native.registry.VEHICLE_INITIALIZER_VA):return
                sp=uc.reg_read(ESP);ret=struct.unpack('<I',uc.mem_read(sp,4))[0]
                cleanup=0 if at==parent else 4 if at==native.registry.STRING_CONSTRUCTOR_VA else 48
                if at==native.registry.VEHICLE_INITIALIZER_VA:
                    i=struct.unpack('<I',uc.mem_read(sp+4,4))[0];seen.append(i)
                    self.assertEqual(uc.reg_read(ECX),0x2000000+4+i*52)
                uc.reg_write(ESP,sp+4+cleanup);uc.reg_write(EIP,ret)
            u.hook_add(UC_HOOK_CODE,callback);run(u,r['entries']['init'])
            self.assertEqual(seen,list(range(33,n)));self.assertEqual(u.reg_read(ESP),0x100fff4)


if __name__=='__main__':unittest.main()
