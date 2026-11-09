"""Focused COURSE-CAP2 native CPU and manifest contract checks."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.course_runtime import qualify,next_stage,append_native,STOCK_MENU
from course_capacity_audit import pe_image,extract


class ContractTests(unittest.TestCase):
    def test_explicit_stage_order(self):
        self.assertEqual(next_stage([40,12,39],40),{'stage_index':0,'next_race_id':12})
        self.assertIsNone(next_stage([40,12,39],39)['next_race_id'])
        with self.assertRaises(ValueError):next_stage([40,40],40)
        with self.assertRaises(ValueError):next_stage([40,39],10)


class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vehicle=ROOT.parent/'master-rallye-re-v-cap'
        cls.base=cls.vehicle/'.research-output/vehicles/v-cap3/ai-followup/runtime'
        cls.retail=ROOT.parent/'corpora/retail/MRallye.exe'
        if not (cls.base/'native-extension.bin').exists() or not cls.retail.exists():
            raise unittest.SkipTest('Private accepted V-CAP3/retail fixtures unavailable')
        from unicorn import Uc
        sys.path.insert(0,str(cls.vehicle/'tools'))
        import patch_vehicle_registry_id26 as registry
        cls.raw=cls.retail.read_bytes();cls.sections,cls.offset=pe_image(cls.raw)
        cls.offset=staticmethod(cls.offset)
        cls.rp=json.loads((cls.base/'runtime-profile.json').read_text())
        parent=bytearray(cls.raw)
        for op in json.loads((cls.base/'native-patch-manifest.json').read_text())['operations']:
            at=op['file_offset'];before=bytes.fromhex(op['expected_original_bytes']);after=bytes.fromhex(op['replacement_bytes'])
            if parent[at:at+len(before)]!=before:raise ValueError('Accepted native test fixture preimage differs')
            parent[at:at+len(before)]=after
        cls.parent=bytes(parent)
        cls.parent_blob=(cls.base/'native-extension.bin').read_bytes()
        baseline,_=extract(cls.raw)
        cls.doc={'schema':'mr-course-registry/1','courses':[{'key':'test','folder':'DataGx/course/test','model':'DataGx/course/test/test.dx'}],
                 'races':[{**r,'course':'test','icont':'DataScene/ICont/test.sfl'} for r in baseline],
                 'runtime_budget':{'max_shared_bytes':65536}}
        for i in (39,40):
            r=copy.deepcopy(cls.doc['races'][0]);r.update(id=i,scene=f'DataScene/RaceTest/Cap{i}.xml',
                title=f'Test {i}',progress_key=f'test-{i}',modes=['QuickRace'],menu={'group':0,'position':i-36,'flag_frame':0,'screenshot_pair':0})
            r['native_fields'][0]=i;cls.doc['races'].append(r)
        cls.baseline=baseline;cls.catalog=qualify(cls.doc,baseline,cls.rp)
        cls.image,cls.blob,cls.report=append_native(cls.raw,cls.parent,cls.parent_blob,cls.catalog,
            emitter=registry._CodeImage,pe_offset=cls.offset)

    def machine(self):
        from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
        from unicorn.x86_const import UC_X86_REG_ESP
        u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0,4096);u.mem_map(0x400000,0x400000)
        for r,o,n,v in self.sections:u.mem_write(0x400000+r,self.image[o:o+n])
        u.mem_map(0x10000000,(len(self.blob)+4095)//4096*4096);u.mem_write(0x10000000,self.blob)
        u.mem_map(0x2000000,0x10000);u.mem_map(0x3000000,0x10000);u.mem_map(0x30000000,4096)
        u.reg_write(UC_X86_REG_ESP,0x2008000)
        return u

    def test_actual_vehicle_count(self):
        self.assertEqual(self.catalog['layout']['vehicle_count'],35)
        doc=copy.deepcopy(self.doc);doc['vehicle_count']=33
        with self.assertRaisesRegex(ValueError,'disagrees'):qualify(doc,self.baseline,self.rp)

    def test_arbitrary_additive_menu_order(self):
        doc=copy.deepcopy(self.doc)
        doc['races'][39]['menu']['position']=4;doc['races'][40]['menu']['position']=3
        result=qualify(doc,self.baseline,self.rp)
        self.assertEqual(result['menu_groups'][0],[10,11,12,40,39])

    def test_native_explicit_schedule_lookup(self):
        from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EAX,UC_X86_REG_EDX,UC_X86_REG_ECX,UC_X86_REG_EFLAGS
        u=self.machine();sp=0x2008000;end=0x30000000
        # Execute real generated lookup, including a noncontiguous schedule.
        at=self.report['entries']['competitions']
        u.mem_write(at,struct.pack('<4I',3,40,12,39))
        for race,ordinal,nxt in [(40,0,12),(12,1,39),(39,2,0xffffffff),(10,0xffffffff,0xffffffff)]:
            u.mem_write(sp,struct.pack('<3I',end,0,race));u.reg_write(UC_X86_REG_ESP,sp)
            u.emu_start(self.report['entries']['lookup_stage'],end,count=150)
            self.assertEqual(u.reg_read(UC_X86_REG_EAX),ordinal);self.assertEqual(u.reg_read(UC_X86_REG_EDX),nxt)
            self.assertEqual(u.reg_read(UC_X86_REG_ESP),sp+12)
            self.assertEqual(bool(u.reg_read(UC_X86_REG_EFLAGS)&1),race==10)
            if race!=10:self.assertEqual(u.reg_read(UC_X86_REG_ECX),3)

    def test_private_progress_key_and_return_abi(self):
        from unicorn import UC_HOOK_CODE
        from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_ECX,UC_X86_REG_EAX
        for ident in (39,40):
            u=self.machine();sp=0x2008000;end=0x30000000;seen=[];scratch=0x3009000
            u.mem_write(sp,struct.pack('<2I',end,ident))
            def cstr(at):return bytes(u.mem_read(at,200)).split(b'\0')[0]
            def intercept(uc,at,size,user):
                nonlocal scratch
                if at not in (0x4d11d0,0x4d15c0,0x4d0580,0x4d8ec0,0x4d6650,0x5b4c00):return
                stack=uc.reg_read(UC_X86_REG_ESP);ret,arg=struct.unpack('<2I',uc.mem_read(stack,8));ecx=uc.reg_read(UC_X86_REG_ECX)
                cleanup=4
                if at in (0x4d11d0,0x4d0580):uc.mem_write(ecx,struct.pack('<I',arg));cleanup=8
                elif at==0x4d15c0:
                    previous=struct.unpack('<I',uc.mem_read(ecx,4))[0];value=cstr(previous)+cstr(arg)+b'\0'
                    uc.mem_write(scratch,value);uc.mem_write(ecx,struct.pack('<I',scratch));scratch+=512;cleanup=8
                elif at==0x4d8ec0:uc.reg_write(UC_X86_REG_EAX,0x300f000)
                elif at==0x4d6650:
                    handle=struct.unpack('<I',uc.mem_read(arg,4))[0];seen.append(cstr(handle).decode());cleanup=8
                    # Give the real native epilogue a valid x87 return value.
                    uc.mem_write(0x300e000,b'\xd9\xee\xc2\x04\x00');uc.reg_write(UC_X86_REG_EIP,0x300e000);return
                uc.reg_write(UC_X86_REG_ESP,stack+cleanup);uc.reg_write(UC_X86_REG_EIP,ret)
            u.hook_add(UC_HOOK_CODE,intercept)
            u.emu_start(self.report['entries']['get_race_best_dispatch'],end,count=1000)
            self.assertEqual(seen,[f'Progress/BestTimes/CourseRegistryV1/test-{ident}'])
            self.assertEqual(u.reg_read(UC_X86_REG_ESP),sp+8)

    def test_new_selection_mode_admission_without_substitution(self):
        from unicorn import UC_HOOK_CODE
        from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_ECX,UC_X86_REG_EAX
        for quick,split,network in [(True,False,False),(False,False,False),(True,True,False),(True,False,True)]:
            u=self.machine();sp=0x2008000;obj=0x3000000;end=0x30000000;denied=not quick or split or network;messages=[]
            u.mem_write(obj+0x10,struct.pack('<2I',0,3));u.mem_write(sp,struct.pack('<I',end));u.reg_write(UC_X86_REG_ECX,obj)
            u.mem_write(0x68f2b4,struct.pack('<I',0x300f000))
            def intercept(uc,at,size,user):
                if at not in (0x4ae700,0x4ada50,0x4addb0,0x4ae2d0,0x4ad930,0x300f000):return
                stack=uc.reg_read(UC_X86_REG_ESP);ret=struct.unpack('<I',uc.mem_read(stack,4))[0];cleanup=4
                if at in (0x4ae700,0x4ada50):value=0x300e000
                elif at==0x4addb0:value=int(quick)
                elif at==0x4ae2d0:value=int(split)
                elif at==0x4ad930:value=int(network)
                else:value=1;messages.append(at);cleanup=20
                uc.reg_write(UC_X86_REG_EAX,value);uc.reg_write(UC_X86_REG_ESP,stack+cleanup);uc.reg_write(UC_X86_REG_EIP,ret)
            u.hook_add(UC_HOOK_CODE,intercept)
            u.emu_start(self.report['entries']['admit_selection'],0x47ec84 if denied else end,count=300)
            self.assertEqual(bool(messages),denied);self.assertEqual(u.reg_read(UC_X86_REG_ESP),sp+4)
            if not denied:self.assertEqual(u.reg_read(UC_X86_REG_EAX),39)

    def test_preserved_parent_payload_and_master_progress(self):
        self.assertEqual(self.blob[:len(self.parent_blob)],self.parent_blob)
        for va,size in [(0x4b0000,133),(0x4aff80,128),(0x453bd0,307),(0x453d10,503)]:
            at=self.offset(va,size);self.assertEqual(self.image[at:at+size],self.parent[at:at+size])

    def test_shared_results_reads_private_race_progress(self):
        from capstone import Cs,CS_ARCH_X86,CS_MODE_32
        calls=[];start=0x460b50;size=1734;off=self.offset(start,size)
        for ins in Cs(CS_ARCH_X86,CS_MODE_32).disasm(self.raw[off:off+size],start):
            if ins.bytes[0]==0xe8 and ins.address+5+struct.unpack_from('<i',ins.bytes,1)[0]==0x4b0000:
                at=self.offset(ins.address,5);target=ins.address+5+struct.unpack_from('<i',self.image,at+1)[0]
                self.assertEqual(target,self.report['entries']['get_race_best_dispatch']);calls.append(ins.address)
        self.assertTrue(calls,'Shared Results has no qualified BestTime reader')

    def test_forward_reverse_all_records(self):
        from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ECX,UC_X86_REG_EAX
        u=self.machine();sp=0x2008000;obj=0x3000000;end=0x30000000
        for i,(group,local) in enumerate(self.catalog['reverse_menu']):
            u.mem_write(sp,struct.pack('<2I',end,i));u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,obj)
            u.emu_start(0x47f320,end,count=100)
            self.assertEqual(struct.unpack('<I',u.mem_read(obj+0x10,4))[0],group)
            self.assertEqual(struct.unpack('<I',u.mem_read(obj+0x14+group*4,4))[0],local)
            self.assertEqual(u.reg_read(UC_X86_REG_ESP),sp+8)
            u.mem_write(sp,struct.pack('<I',end));u.reg_write(UC_X86_REG_ESP,sp);u.reg_write(UC_X86_REG_ECX,obj)
            u.emu_start(0x47f2b0,end,count=100);self.assertEqual(u.reg_read(UC_X86_REG_EAX),i)

    def test_lifetime_count_register_and_stack(self):
        from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_ESI,UC_X86_REG_EBP,UC_X86_REG_EAX,UC_X86_REG_ECX
        for name,end,reg in [('construct',0x458d16,UC_X86_REG_ECX),('destroy',0x458e30,UC_X86_REG_EAX)]:
            u=self.machine();u.reg_write(UC_X86_REG_ESI,0x3000000);u.emu_start(self.report['entries'][name],end,count=10)
            sp=u.reg_read(UC_X86_REG_ESP)
            self.assertEqual(struct.unpack('<I',u.mem_read(sp,4))[0],41)
            self.assertEqual(u.reg_read(reg),0x3000000+0x720)
        u=self.machine();u.reg_write(UC_X86_REG_EBP,0x3000100);u.mem_write(0x30000f0,struct.pack('<I',0x3000000))
        u.emu_start(self.report['entries']['unwind'],0x6867b2,count=10)
        self.assertEqual(struct.unpack('<2I',u.mem_read(u.reg_read(UC_X86_REG_ESP),8)),(44,41))
        self.assertEqual(u.reg_read(UC_X86_REG_EAX),0x3000000)

    def test_real_initializer_temporary_ownership(self):
        from unicorn import UC_HOOK_CODE
        from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_ESI,UC_X86_REG_ECX
        u=self.machine();sp=0x2008000;obj=0x3000000;copies=[];frees=[];constructs=[]
        fields=self.catalog['races'][38]['native_fields'];args=fields[:7]+[0x3008000]+fields[7:]
        u.mem_write(sp,struct.pack('<10I',*args));u.reg_write(UC_X86_REG_ECX,obj+0x720+38*44);u.reg_write(UC_X86_REG_ESI,obj)
        def intercept(uc,at,size,user):
            if at not in (0x4d11d0,0x4d1990,0x5b4c00):return
            stack=uc.reg_read(UC_X86_REG_ESP);ret,arg=struct.unpack('<2I',uc.mem_read(stack,8))
            if at==0x4d11d0:
                constructs.append(arg);uc.mem_write(uc.reg_read(UC_X86_REG_ECX),struct.pack('<I',arg))
            elif at==0x4d1990:
                copies.append(arg);uc.mem_write(uc.reg_read(UC_X86_REG_ECX),struct.pack('<I',arg))
            else:frees.append(arg)
            uc.reg_write(UC_X86_REG_ESP,stack+(4 if at==0x5b4c00 else 8));uc.reg_write(UC_X86_REG_EIP,ret)
        u.hook_add(UC_HOOK_CODE,intercept)
        u.emu_start(self.report['entries']['initialize_additions'],0x459fdc,count=10000)
        self.assertEqual(u.reg_read(UC_X86_REG_ESP),sp+40)
        self.assertEqual(len(constructs),2);self.assertEqual(len(copies),3);self.assertEqual(copies,frees)
        for i in (38,39,40):
            row=struct.unpack('<11I',u.mem_read(obj+0x720+i*44,44));f=self.catalog['races'][i]['native_fields']
            self.assertEqual(row[1:7],tuple(f[:5]+[f[6]]));self.assertEqual(row[8:],tuple([f[5]]+f[7:]))

    def test_higher_counts_use_imm32_lifecycle(self):
        # Addressing/lifecycle evidence only, not a claim of playable capacity.
        import patch_vehicle_registry_id26 as registry
        for count in (128,255,256,257):
            doc=copy.deepcopy(self.doc)
            for i in range(41,count):
                row=copy.deepcopy(doc['races'][39]);row.update(id=i,title=f'Test {i}',progress_key=f'test-{i}',menu={'group':0,'position':i-36,'flag_frame':0,'screenshot_pair':0});row['native_fields'][0]=i;doc['races'].append(row)
            cat=qualify(doc,self.baseline,self.rp)
            _,blob,report=append_native(self.raw,self.parent,self.parent_blob,cat,emitter=registry._CodeImage,pe_offset=self.offset)
            off=report['entries']['construct']-0x10000000
            self.assertEqual(blob[off:off+5],b'\x68'+struct.pack('<I',count))

    def test_native_image_pair_is_independent_of_new_race_id(self):
        from unicorn.x86_const import UC_X86_REG_EAX,UC_X86_REG_EDI,UC_X86_REG_EBX,UC_X86_REG_EBP
        for ident in (10,39,40):
            u=self.machine();obj=0x3000000;u.mem_write(obj+0x720+ident*44+4,struct.pack('<I',ident))
            u.reg_write(UC_X86_REG_EAX,obj);u.reg_write(UC_X86_REG_EDI,ident*44);u.reg_write(UC_X86_REG_EBX,ident)
            u.emu_start(self.report['entries']['menu_image_pair'],0x47ed5a,count=30)
            self.assertEqual(u.reg_read(UC_X86_REG_EBP),ident if ident<39 else 0)


if __name__=='__main__':unittest.main()
