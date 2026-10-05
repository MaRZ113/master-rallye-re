"""Bounded native UI/list/localization tests; no human interaction or game execution."""
from __future__ import annotations
import argparse
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import r_ui1_opponents as u
import r_ai2_emulate as five
from r_ai2_emulate import BoundedMachine

PREFIX = 'Frontend/QuickModeSelect/'


class UI(BoundedMachine):
    def __init__(self, program, api, monitor, start, *, index=0, mode=1, language=0, control=0, committed=1):
        super().__init__(program, api, monitor, start)
        self.nodes = {}; self.paths = {}; self.writes = []; self.saved_to_native = []
        self.policy_calls = 0; self.localized_calls = []
        self.broker = {PREFIX+'Mode':mode, PREFIX+'NumOpponents':index,
                       PREFIX+'RaceDifficulty':0, PREFIX+'CountdownDifficulty':0,
                       'Frontend/QuickRace/Mode':mode+1, 'Frontend/QuickRace/NumOpponents':committed}
        self.obj = self.alloc(bytes(0x30)); self.put('ECX', self.obj)
        self.write(self.obj+0x10, mode)
        self.write(self.obj+0x18, self.cstring(PREFIX+'NumOpponentsList'))
        self.write(self.obj+0x1C, self.cstring(PREFIX+'NumOpponents'))
        self.write(self.obj+0x20, self.cstring(PREFIX+'NumOpponentsText'))
        self.local = self.alloc(struct.pack('<II', 0x690BE0, language))
        self.control = control

    def execute_bounded(self, boundary, pop=0):
        # A full screen constructor performs many linear scans of the authored
        # localization tables; unlike a single getter this needs >30k steps.
        while self.emu.getExecutionAddress().getOffset() != self.stop:
            pc=self.emu.getExecutionAddress().getOffset();self.visited.add(pc)
            if not boundary(pc) and not self.emu.step(self.monitor):
                raise ValueError(f'Native UI failed at {pc:#x}: {self.emu.getLastError()}')
            self.steps+=1
            if self.steps>300000:raise ValueError(f'Bounded UI instruction budget at {pc:#x}')
        if any(self.reg(name)!=value for name,value in self.saved.items()):
            raise ValueError('Native UI callee-saved register mismatch')
        if self.reg('ESP')!=self.stack+4+pop or self.read(0)!=0:
            raise ValueError(f'Native UI stack/SEH restoration mismatch: ESP={self.reg("ESP"):#x}, expected={self.stack+4+pop:#x}, FS={self.read(0):#x}')
        self.guards()

    def native_list(self, values):
        array = self.alloc(b''.join(struct.pack('<I', self.cstring(v)) for v in values))
        return self.alloc(struct.pack('<IIII', 0, array, array+len(values)*4, array+len(values)*4))

    def list_text(self, ptr):
        return [self.text(self.read(pos)) for pos in range(self.read(ptr+4), self.read(ptr+8), 4)]

    def boundary(self, pc):
        sp = self.reg('ESP')
        if pc == 0x485CF0: self.ret(self.local)
        elif pc == 0x485BB0:
            self.localized_calls.append((self.read(sp+4), self.read(sp+8)))
            return False  # native table lookup executes, including all six languages
        elif pc in (0x4D0580, 0x4D11D0, 0x4D1240):
            dst = self.reg('ECX'); src = self.read(sp+4)
            if pc == 0x4D1240: src = self.read(src)
            self.write(dst, self.cstring(self.text(src)) if src else 0)
            self.ret(dst, 4)  # typed enString copy boundary; native list growth executes
        elif pc == 0x4D8EC0:
            path = self.text(self.read(self.read(sp+4)))
            node = self.nodes.get(path)
            if node is None:
                node = self.alloc(bytes(16)); self.nodes[path] = node; self.paths[node] = path
            self.ret(node, 4)
        elif pc in (0x4D6760, 0x4D6520, 0x4D6EA0):
            self.ret(self.broker.get(self.paths[self.reg('ECX')], 0))
        elif pc in (0x4D8000, 0x4D7AA0, 0x4D8880, 0x4D8720, 0x4D85F0):
            path = self.paths[self.reg('ECX')]; value = self.read(sp+4)
            if pc in (0x4D8720, 0x4D85F0): value = self.text(self.read(value))
            self.broker[path] = value; self.writes.append((path, value)); self.ret(None, 4)
        elif pc == 0x461EA0:
            # Only the unrelated Mode list uses this one-element insert overload;
            # Opponents uses actual407B30 for every append/growth operation.
            ptr = self.reg('ECX'); pos = self.read(sp+4); value = self.read(self.read(sp+8))
            begin, end = self.read(ptr+4), self.read(ptr+8)
            if pos != end: raise ValueError('Unexpected non-append Mode insert')
            values = [self.read(p) for p in range(begin,end,4)] if begin else []
            values.append(self.cstring(self.text(value)))
            array = self.alloc(b''.join(struct.pack('<I',v) for v in values)); size=len(values)*4
            self.write(ptr+4,array); self.write(ptr+8,array+size); self.write(ptr+12,array+size); self.ret(array+size-4,8)
        elif pc in (0x45D610,): self.ret(self.reg('ECX'), 4)
        elif pc in (0x47A540, 0x47A120): self.ret()  # full constructor cases separate from init/arrow cases
        elif pc in (0x4AE700,): self.ret(self.obj)
        elif pc == 0x4AE090: self.ret(self.broker['Frontend/QuickRace/Mode'])
        elif pc == 0x4AE150: self.ret(self.broker['Frontend/QuickRace/NumOpponents'])
        elif pc == 0x4AE120:
            self.broker['Frontend/QuickRace/NumOpponents'] = self.read(sp+4); self.ret(None, 4)
        elif pc in (0x4AE1B0, 0x4AE210): self.ret(0)
        elif pc == 0x4ADFB0: self.ret(0, 4)
        elif pc == 0x4AE030: self.ret(10)
        elif pc in (0x450480, 0x450470): self.ret(self.obj)
        elif pc in (0x522D80,): self.ret(self.obj)
        elif pc == 0x5229B0:
            self.saved_to_native.append((self.text(self.read(self.read(sp+4))), self.read(sp+8)))
            self.ret(None, 8)
        elif pc in (0x4F6310, 0x525A80): self.ret(self.obj)
        elif pc == 0x4F6070: self.ret(None, 8)
        elif pc == 0x525800: self.ret(6)
        elif pc == 0x525820: self.ret(self.control)
        elif pc == 0x525970: self.ret(None, 4)
        elif pc == 0x4F68F0: self.ret(self.obj, 4)
        elif pc == 0x4F6680: self.ret()
        else: return self.heap_boundary(pc)
        return True


def test_case(program, api, monitor, kind, index=0, mode=1, language=0, direction=1, committed=1):
    start = {'list':0x479BB0, 'arrows':0x47A120, 'input':0x454610,
             'publish':0x47A8C0, 'entry':0x47A540, 'localization':0x485BB0, 'hook':u.HOOK}[kind]
    m = UI(program, api, monitor, start, index=index, mode=mode, language=language,
           control=2 if direction == -1 else 3, committed=committed)
    if kind == 'localization':
        m.write(m.stack+4,64); m.write(m.stack+8,index); m.put('ECX',m.local)
    if kind == 'input':
        m.broker[PREFIX+'NumOpponentsList'] = m.native_list(u.LABELS)
    if kind == 'hook':
        ptr=m.native_list(u.LABELS[:3]);m.saved['EBX']=ptr;m.put('EBX',ptr)
        temp=m.cstring('THREE');m.write(m.stack+0x14,temp)
        m.write(m.stack+0x28,0x12345678);m.stop=u.CONTINUE
        registers={'EAX':0xA1A2A3A4,'ECX':0xB1B2B3B4,'EDX':temp}
        for name,value in registers.items():m.put(name,value)
        flags={name:(index>>n)&1 for n,name in enumerate(('CF','PF','AF','ZF','SF','OF'))}
        for name,value in flags.items():m.put(name,value)
        registers['ESP']=m.stack
    if kind in ('arrows', 'entry'):
        # This is the actual root entry; boundary stubs suppress constructor calls only.
        original = m.boundary
        def boundary(pc):
            return False if pc == start else original(pc)
    else: boundary = m.boundary
    try:
        m.execute_bounded(boundary, -4 if kind == 'hook' else 8 if kind == 'localization' else 4 if kind in ('list','input') else 0)
        if kind == 'list':
            ptr = m.broker[PREFIX+'NumOpponentsList']; values = m.list_text(ptr)
            rows = u.localization(SOURCE)[language]['labels']
            expected = [bytes.fromhex(r['raw_text_hex']).decode('cp1252') for r in rows]
            if values != expected or [p for p in m.localized_calls if p[0] == 64] != [(64,n) for n in range(7)]:
                raise ValueError('Native construction did not append exact seven localized labels once')
        elif kind == 'localization':
            expected = bytes.fromhex(u.localization(SOURCE)[language]['labels'][index]['raw_text_hex']).decode('cp1252')
            if m.text(m.reg('EAX')) != expected: raise ValueError('Native locale mismatch')
        elif kind == 'arrows':
            if m.broker[PREFIX+'LeftArrow2-3'] != int(mode == 1 and index > 0) or m.broker[PREFIX+'RightArrow2-3'] != int(mode == 1 and index < 6):
                raise ValueError('Opponent arrow max/min mismatch')
            if m.broker[PREFIX+'RightArrow2-2'] != int(mode == 1):
                raise ValueError('Unrelated difficulty arrow changed')
        elif kind == 'input':
            expected = u.navigate(index,direction)
            if m.broker[PREFIX+'NumOpponents'] != expected or m.broker['UI/Control'] != 0:
                raise ValueError('Native control bounds/consumption mismatch')
            if index != expected and m.broker[PREFIX+'NumOpponentsText'] != u.LABELS[expected]:
                raise ValueError('Native selected text refresh mismatch')
        elif kind == 'publish':
            expected = index+1 if mode == 1 else committed
            if m.broker['Frontend/QuickRace/NumOpponents'] != expected or m.saved_to_native != [('PlayerState',3)]:
                raise ValueError('Native index+1 publication/save changed')
        elif kind == 'entry':
            expected = committed or 1
            if m.broker[PREFIX+'NumOpponents'] != expected-1:
                raise ValueError('Entry reload/reset mismatch')
        elif kind == 'hook':
            if m.list_text(ptr)!=list(u.LABELS):
                raise ValueError('Hook did not extend the original list')
            if any(m.reg(name)!=value for name,value in {**registers,**flags}.items()) or m.read(m.stack+0x28)!=m.saved['ESI']:
                raise ValueError('Live hook register/flags or displaced MOV preservation failed')
        return dict(kind=kind, index=index, mode=mode, language=language, direction=direction,
                    committed_count=committed, steps=m.steps, redzones_intact=True)
    finally: m.emu.dispose()


def main():
    global SOURCE
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('install','project','source','candidate','output'): p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args(); SOURCE=a.source.read_bytes(); u.build(SOURCE); u.verify(a.candidate.read_bytes())
    import pyghidra
    pyghidra.start(install_dir=a.install)
    from java.lang import Object
    from ghidra.program.flatapi import FlatProgramAPI
    project=pyghidra.open_project(a.project,'MasterRallye'); consumer=Object(); program=None; transaction=None
    try:
        program=project.getProjectData().getFile('/MRallye.exe').getReadOnlyDomainObject(consumer,-1,pyghidra.task_monitor())
        if str(program.getExecutableSHA256()) != u.RETAIL_SHA256: raise ValueError('Wrong pristine program')
        api=FlatProgramAPI(program); monitor=pyghidra.task_monitor(); transaction=program.startTransaction('R-UI1 unsaved native tests')
        for row in u.ranges():
            if row['va'] is None: continue
            addr=api.toAddr(row['va']); memory=program.getMemory(); data=row['replacement']
            if not memory.contains(addr):
                memory.createInitializedBlock('UI1_'+str(addr),addr,len(data),0,monitor,False).setExecute(True)
            api.clearListing(addr,addr.add(len(data)-1));memory.setBytes(addr,data);api.disassemble(addr)
        rows=[]
        for flags in (0,21,42):rows.append(test_case(program,api,monitor,'hook',index=flags))
        for language in range(6):
            for index in range(7): rows.append(test_case(program,api,monitor,'localization',index=index,language=language))
            rows.append(test_case(program,api,monitor,'list',language=language))
        for index in range(7):
            for mode in range(3): rows.append(test_case(program,api,monitor,'arrows',index=index,mode=mode))
            for direction in (-1,1): rows.append(test_case(program,api,monitor,'input',index=index,direction=direction))
            rows.append(test_case(program,api,monitor,'publish',index=index))
        for mode in (0,2): rows.append(test_case(program,api,monitor,'publish',index=6,mode=mode,committed=3))
        for committed in range(8): rows.append(test_case(program,api,monitor,'entry',committed=committed))
        # Unpatched native47B780 must read visible count directly. Only counts1..4
        # are tested as setup; higher menu selections are never race-capacity proof.
        old_expected=five.c.effective_opponents
        try:
            five.c.effective_opponents=lambda **state:state['opponents']
            setup=[five.setup(program,api,monitor,dict(opponents=n,mode=2,split=False,ghost=0,player=0,track=10)) for n in range(1,5)]
        finally: five.c.effective_opponents=old_expected
        report=dict(status='STATIC_NATIVE_R_UI1_MATCH_ONLY',passed=len(rows)+len(setup),failed=0,skipped=0,
                    runtime_full_pass=False,source_sha256=u.RETAIL_SHA256,candidate_sha256=u.CANDIDATE_SHA256,
                    project_saved=False,rows=rows,setup=setup,
                    limits='Actual native locale/list growth/navigation/arrows/index publication; typed string/Broker/heap/save/input-controller boundaries. No visible layout or race behavior proof.')
        out=u.ignored_output(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
        print(report['status'], report['passed'],'cases')
    finally:
        if program is not None:
            if transaction is not None: program.endTransaction(transaction,False)
            program.release(consumer)
        project.close()


if __name__ == '__main__': main()
