"""Execute R-AI1.2 native builders/bridge and Master save/load in unsaved Ghidra."""
from __future__ import annotations
import argparse
import itertools
import json
import struct
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import r_ai1_2_randomizer as r
from r_ai2_emulate import BoundedMachine


def install(program,api,monitor,source,patched):
    memory=program.getMemory()
    # One temporary block covers only original .text padding, not .rdata/IAT.
    if not memory.contains(api.toAddr(r.BASE)):
        block=memory.createInitializedBlock("R_AI12_TEMP",api.toAddr(0x68E300),0xD00,0,monitor,False)
        block.setExecute(True)
    for row in r.ranges(True):
        if row["va"] is None:continue
        address=api.toAddr(row["va"]);code=row["replacement"] if patched else row["original"]
        api.clearListing(address,address.add(len(code)-1));memory.setBytes(address,code);api.disassemble(address)


class Game(BoundedMachine):
    def __init__(self,program,api,monitor,kind,count=3,player=0,plan=(),unlocked=False,first=1):
        self.kind,self.count,self.player,self.plan,self.first=kind,count,player,plan,first
        self.rng,self.ranges,self.writes,self.policy_calls=12345,[],[],[]
        self.unlocked,self.unlock_key=unlocked,0
        self.cars={n:{"CarID":player if n==0 else -1,"CarClass":player//7 if n==0 else -1,
                      "DriverID":30 if n==0 else -1,"PlayerType":1 if n==0 else 2} for n in range(5)}
        start={"QuickRace":0x458090,"MasterRallye":0x451DD0,"RallyeCup":0x45ABC0,"Invitation":0x45ABC0,
               "Challenge":0x44FEC0,"save":0x452640,"load":0x452FE0,"loader":r.LOADER,
               "composed":0x47B780,"cup-stage":0x45B170,"invitation-stage":0x45B170,
               "master-stage":0x452370}[kind]
        args=(first,count,player//7,player,-1) if kind=="QuickRace" else (first,count,player//7)
        if kind in ("Challenge","save"):args=(0,)
        if kind=="load":args=()
        if kind=="loader":args=(0,1,3,1)
        if kind in ("composed","cup-stage","invitation-stage","master-stage"):args=()
        super().__init__(program,api,monitor,start,args)
        self.registry=self.alloc(bytes(0x1200));self.race=self.alloc(bytes(0x100));self.data=self.alloc(bytes(0x100))
        self.broker={};self.current_path={};self.path_nodes={};self.class_value=player//7;self.numcars=None;self.next_race=None
        self.put("ECX",self.data)
        for n in range(25):self.write(self.registry+n*0x34+0xC,0 if n<7 else 1 if n<14 else 2)
        self.write(self.registry+25*0x2C+0x570,0);self.write(self.registry+25*0x2C+0x574,7)
        # Synthetic log-name interface, not an AI controller/model.
        self.log=self.alloc(bytes(16));self.vtable=self.alloc(bytes(16));self.write(self.log,self.vtable)
        self.write(self.vtable+12,0x7FF000);self.name=self.cstring("SYNTHETIC DRIVER")
    def boundary(self,pc):
        sp=self.reg("ESP")
        if pc==r.LOADER and self.kind!="loader":
            hint,first,count,slot=(self.read(sp+i*4) for i in range(1,5))
            self.policy_calls.append((hint,first,count,slot))
            cls=self.plan[slot-first] if first==1 and 0<=slot-first<len(self.plan) and 1<=count<=4 else -1
            if self.kind=="Challenge":cls=14 if cls>=0 else -1
            self.ret(cls,16)
        elif pc in (0x4ADA50,0x4AE700,0x4B0AF0,0x4D1E90):
            self.ret(self.race if pc==0x4ADA50 else self.data)
        elif pc==0x4AE2D0:self.ret(int(self.first!=1))
        elif pc==0x4AE620:self.ret(5 if self.kind in ("Invitation","invitation-stage") else 0)
        elif pc==0x4ABE90:self.ret({"QuickRace":2,"Challenge":7,"RallyeCup":6,"Invitation":8}.get(self.kind,5))
        elif pc in (0x4B04F0,):self.ret(self.class_value)
        elif pc==0x4B04C0:self.class_value=self.read(sp+4);self.ret(None,4)
        elif pc in (0x4AC660,0x4B0630,0x4B06C0,0x4B0750,0x4AC5C0):
            slot=self.read(sp+4)
            key={0x4AC660:"CarID",0x4B0630:"CarID",0x4B06C0:"CarClass",0x4B0750:"DriverID",0x4AC5C0:"PlayerType"}[pc]
            self.ret(self.cars.get(slot,{}).get(key,0),4)
        elif pc in (0x4ACAF0,0x4ACC10,0x4ACCD0,0x4B05E0,0x4B0670,0x4B0700,0x4AC8E0):
            slot,value=self.read(sp+4),self.read(sp+8)
            key={0x4ACAF0:"CarID",0x4ACC10:"CarClass",0x4ACCD0:"DriverID",
                 0x4B05E0:"CarID",0x4B0670:"CarClass",0x4B0700:"DriverID",0x4AC8E0:"PlayerType"}[pc]
            if slot>4 and self.kind not in ("load",):raise ValueError("Active publisher escaped Car4")
            self.cars.setdefault(slot,{})[key]=value;self.writes.append((slot,key,value));self.ret(None,8)
        elif pc in (0x4B0520,0x4B0790,0x4B0820,0x4B08B0,0x4B0940,0x4B09D0,0x4B0A60):
            self.ret(None,8)
        elif pc in (0x4B0900,0x4B0990):self.ret(0,4)
        elif pc in (0x4B07E0,0x4B0870):self.emu.writeRegister("ST0",0);self.ret(None,4)
        elif pc==0x45A3C0:self.ret(self.registry)
        elif pc==0x4B0310:self.unlock_key=self.read(sp+4);self.ret(self.data)
        elif pc==0x4AFB70:self.ret(int(self.unlocked),4)
        elif pc==0x4D1DF0:
            low,high=self.read(sp+4),self.read(sp+8)
            if self.kind=="master-stage" and (low,high)==(1,10):self.ret(4,8);return True
            if (low,high)!=(0,65535):raise ValueError("Unexpected native range")
            self.rng=(self.rng*48271)%2147483647
            value=((self.rng&0xFFFFFF)*65535)//(1<<24)
            self.ranges.append((low,high,value));self.ret(value,8)
        elif pc==0x5C8471:self.ret(0x750000)
        elif pc in (0x414920,0x411C90):
            vec=self.reg("ECX");pos=self.read(sp+4);count=1 if pc==0x414920 else self.read(sp+8)
            ptr=self.read(sp+(8 if pc==0x414920 else 12))
            if count!=1:raise ValueError("Unexpected vector insert count")
            begin,end=self.read(vec+4),self.read(vec+8)
            if not begin:
                begin=end=self.alloc(bytes(512));self.write(vec+4,begin);self.write(vec+12,begin+512);pos=begin
            if not begin<=pos<=end<begin+508:raise ValueError("Vector escaped synthetic allocation")
            for cursor in range(end,pos,-4):self.write(cursor,self.read(cursor-4))
            self.write(pos,self.read(ptr));self.write(vec+8,end+4);self.ret(pos,8 if pc==0x414920 else 12)
        elif pc in (0x411670,0x4504B0):self.ret()
        elif pc==0x485CF0:self.ret(self.log)
        elif pc==0x7FF000:self.ret(self.name,8)
        elif pc==0x4D11D0:
            ptr=self.reg("ECX");self.write(ptr,self.read(sp+4));self.ret(ptr,4)
        elif pc==0x4AC3D0:self.numcars=self.read(sp+4);self.ret(None,4)
        elif pc==0x4AC2B0:self.next_race=self.read(sp+4);self.ret(None,4)
        elif pc in (0x4AC4D0,0x4AC400,0x4AC220,0x4AC1C0,0x4AC500):self.ret(None,4)
        elif pc==0x4ABF20:self.ret({"cup-stage":10,"invitation-stage":36}.get(self.kind,2))
        elif pc==0x4AC100:self.ret(1)
        elif pc==0x4AE2A0:self.ret(None,4)
        elif pc==0x4D0580:
            ptr=self.reg("ECX");self.write(ptr,self.read(sp+4));self.ret(ptr,4)
        elif pc==0x4D8EC0:
            path=self.text(self.read(self.read(sp+4)));ptr=self.path_nodes.get(path)
            if ptr is None:ptr=self.alloc(bytes(16));self.path_nodes[path]=ptr;self.current_path[ptr]=path
            self.ret(ptr,4)
        elif pc in (0x4D6760,0x4D6520):
            self.ret(self.broker.get(self.current_path[self.reg("ECX")],0))
        elif pc==0x4D6650:self.emu.writeRegister("ST0",0);self.ret()
        elif pc in (0x4D8000,0x4D7AA0,0x4D7ED0):
            self.broker[self.current_path[self.reg("ECX")]]=self.read(sp+4);self.ret(None,4)
        elif pc==0x522D80:self.ret(self.data)
        elif pc==0x5229B0:self.ret(None,8) # native PlayerState writer is a documented OS/XML boundary
        elif pc in (0x453BD0,0x45BF60):self.ret() # scoring/best-time/conditions boundary
        elif pc==0x45B3F0:self.ret(None,8)
        elif pc in (0x4AE090,0x4AE030,0x4AE0F0,0x4AE150,0x4AE1B0,0x4AE210):
            self.ret({0x4AE090:2,0x4AE030:10,0x4AE150:3}.get(pc,0))
        elif pc==0x4ADFB0:self.ret(self.player,4)
        elif pc==0x4AC730:self.ret(self.player//7,4)
        elif pc==0x458950:self.ret(self.data)
        else:return self.heap_boundary(pc)
        return True
    def execute_case(self):
        pop=20 if self.kind=="QuickRace" else 4 if self.kind in ("Challenge","save") else 0 if self.kind in ("load","composed","cup-stage","invitation-stage","master-stage") else 16 if self.kind=="loader" else 12
        self.execute_bounded(self.boundary,pop)
        return {"cars":self.cars,"writes":self.writes,"rng":self.ranges,"policy_calls":self.policy_calls,
                "steps":self.steps,"driver_draw_executed":0x458980 in self.visited or 0x45221E in self.visited or 0x45B05B in self.visited}


def run_builders(program,api,monitor,source,only=None):
    rows=[]
    for kind in ("QuickRace","MasterRallye","RallyeCup","Invitation","Challenge"):
        if only=="campaigns" and kind=="QuickRace":continue
        if only and only!="campaigns" and kind!=only:continue
        for count in (range(5) if kind=="QuickRace" else (1,) if kind=="Challenge" else (3,)):
            for player in ((0,7,14) if kind!="Challenge" else (0,)):
                for unlocked in (False,True):
                    install(program,api,monitor,source,False)
                    m=Game(program,api,monitor,kind,count,player,unlocked=unlocked)
                    try:baseline=m.execute_case()
                    finally:m.emu.dispose()
                    install(program,api,monitor,source,True)
                    m=Game(program,api,monitor,kind,count,player,unlocked=unlocked)
                    try:stock=m.execute_case()
                    finally:m.emu.dispose()
                    for key in ("cars","writes","rng"):
                        if baseline[key]!=stock[key]:raise ValueError(f"{kind}/{count}/{player} Stock differs: {key}")
                    rows.append({"kind":kind,"count":count,"player":player,"unlocked":unlocked,"stock_exact":True})
                    if count==0:continue
                    plans=itertools.product(range(3),repeat=count) if kind=="QuickRace" else ((2,1,0)[:count],(0,2,1)[:count])
                    for plan in plans:
                        m=Game(program,api,monitor,kind,count,player,plan,unlocked)
                        try:result=m.execute_case()
                        finally:m.emu.dispose()
                        active=[result["cars"][n] for n in range(1,count+1)]
                        classes=tuple(r.stock_class_local(c["CarID"])[0] if kind in ("RallyeCup","Invitation")
                                      else c["CarClass"] for c in active)
                        if classes!=tuple(plan) and kind!="Challenge":
                            raise ValueError(f"{kind}/{count}/{player}/{plan} class mismatch {active}; calls={result['policy_calls']}")
                        ids=[result["cars"][n]["CarID"] for n in range(count+1)]
                        if len(set(ids))!=len(ids) or any(not 0<=i<25 for i in ids):
                            raise ValueError("Invalid or duplicate ID")
                        if any(result["cars"][n]!=baseline["cars"][n] for n in range(count+1,5)):
                            raise ValueError("Inactive participant changed")
                        if result["cars"][0]!=baseline["cars"][0]:raise ValueError("Human changed")
                        if kind=="Challenge" and result["cars"][1]["DriverID"]!=baseline["cars"][1]["DriverID"]:
                            raise ValueError("Challenge rewrote already selected driver")
                        if len(result["policy_calls"])!=count:raise ValueError("Hook count differs from active count")
                        rows.append({"kind":kind,"count":count,"player":player,"plan":plan,"unlocked":unlocked,
                                     "cars":{str(n):result["cars"][n] for n in range(count+1)},
                                     "classes_from_registry":classes,
                                     "cup_racedata_class_is_not_active_race_class":kind in ("RallyeCup","Invitation")})
    return rows


def persistence(program,api,monitor):
    m=Game(program,api,monitor,"save")
    expected={0:{"CarID":0,"CarClass":0,"DriverID":30,"PlayerType":1},
              1:{"CarID":14,"CarClass":2,"DriverID":4,"PlayerType":2},
              2:{"CarID":7,"CarClass":1,"DriverID":8,"PlayerType":2},
              3:{"CarID":1,"CarClass":0,"DriverID":2,"PlayerType":2}}
    m.cars.update(expected)
    try:m.execute_case();saved={k:v for k,v in m.broker.items() if k.startswith("MasterRallye/")}
    finally:m.emu.dispose()
    for n,row in expected.items():
        for key in ("CarID","CarClass","DriverID"):
            if saved[f"MasterRallye/Car{n}/{key}"]!=row[key]:raise ValueError("Native save identity mismatch")
    m=Game(program,api,monitor,"load");m.broker.update(saved)
    try:
        m.execute_case()
        for n,row in expected.items():
            for key in ("CarID","CarClass","DriverID"):
                if m.cars[n][key]!=row[key]:raise ValueError("Native load identity mismatch")
        if m.policy_calls:raise ValueError("Loading rerolled roster")
    finally:m.emu.dispose()
    return {"native_save_load_identity_equal":True,"policy_calls_during_load":0,
            "active_participants":4,"stock_serialized_tail_not_active_capacity_proof":True,
            "boundaries":["typed Broker","PlayerState XML/file writer"],"runtime_fresh_process_test":False}


def loader_cases(program,api,monitor):
    rows=[]
    for filename,present,loaded,export in (
        ("C:\\Game\\MRallye.exe",True,False,True),
        ("C:\\Game\\MRallye.exe",True,True,True),
        ("C:\\Game\\MRallye.exe",False,False,True),
        ("C:\\Game\\MRallye.exe",True,False,False),
        ("MRallye.exe",True,False,True),
        ("C:\\"+"a"*240+"\\MRallye.exe",True,False,True),
        ("C:\\"+"a"*270+"\\MRallye.exe",True,False,True)):
        m=Game(program,api,monitor,"loader");seen=[]
        targets={name:0x7FF010+n*16 for n,name in enumerate(r.IAT)}
        for name,target in targets.items():m.write(r.IAT[name],target)
        def os_boundary(pc):
            sp=m.reg("ESP")
            if pc==targets["GetModuleFileNameA"]:
                destination,limit=m.read(sp+8),m.read(sp+12)
                data=filename.encode()+b"\0";m.emu.writeMemory(api.toAddr(destination),data[:limit])
                m.ret(min(len(filename),limit),12)
            elif pc in (targets["GetModuleHandleA"],targets["LoadLibraryA"]):
                path=m.text(m.read(sp+4));seen.append(path)
                wanted=filename[:filename.rfind("\\")+1]+"MRallyeRandomizer.dll"
                if path!=wanted:raise ValueError("Loader path/NUL mismatch")
                m.ret(0x710000 if present and (loaded or pc==targets["LoadLibraryA"]) else 0,4)
            elif pc==targets["GetProcAddress"]:
                if m.text(m.read(sp+8))!="MRChooseV1":raise ValueError("Wrong DLL export")
                m.ret(0x7FF100 if export else 0,8)
            elif pc==0x7FF100:
                if [m.read(sp+i*4) for i in range(1,5)]!=[0,1,3,1]:raise ValueError("DLL ABI mismatch")
                m.ret(2,16)
            else:return m.heap_boundary(pc)
            return True
        try:
            m.execute_bounded(os_boundary,16)
            expected=2 if present and export and filename.startswith("C:\\Game\\") else 0xFFFFFFFF
            if m.reg("EAX")!=expected:raise ValueError("Loader fail-closed result")
            rows.append({"filename_length":len(filename),"dll_present":present,"already_loaded":loaded,
                         "export_present":export,"result":m.reg("EAX"),"api_calls":len(seen)})
        finally:m.emu.dispose()
    return rows


def lifecycle_cases(program,api,monitor):
    rows=[]
    for kind in ("cup-stage","invitation-stage","master-stage"):
        m=Game(program,api,monitor,kind)
        for slot,vehicle in enumerate((0,14,7,1)):
            m.cars[slot]["CarID"]=vehicle;m.cars[slot]["CarClass"]=r.stock_class_local(vehicle)[0]
            m.cars[slot]["DriverID"]=30 if slot==0 else slot
        expected={n:dict(row) for n,row in m.cars.items()}
        m.broker["MasterRallye/VehicleClass"]=0
        try:
            m.execute_case()
            if m.cars!=expected or m.policy_calls:raise ValueError("Stage rerolled or rewrote identities")
            next_race={"cup-stage":11,"invitation-stage":37,"master-stage":3}[kind]
            if m.next_race!=next_race:raise ValueError("Stage advance mismatch")
            rows.append({"kind":kind,"same_roster":True,"policy_calls":0,"next_race":next_race,
                         "boundaries":["scoring/bests/conditions","typed Broker","XML/file writer"]})
        finally:m.emu.dispose()
    for plan in ((),(2,2,0,1),(2,1,0,2)):
        m=Game(program,api,monitor,"composed",count=4,plan=plan)
        try:
            result=m.execute_case()
            if m.numcars!=5 or len(result["policy_calls"])!=4:raise ValueError("R-AI2 setup composition failed")
            classes=tuple(m.cars[n]["CarClass"] for n in range(1,5))
            if classes!=(plan or (0,0,0,0)):raise ValueError("Composed class plan mismatch")
            if len({m.cars[n]["CarID"] for n in range(5)})!=5:raise ValueError("Composed duplicate IDs")
            rows.append({"kind":"R-AI2-composed","plan":plan,"NumCars":5,"policy_count":4,
                         "classes":classes,"capacity_shim_unchanged":True})
        finally:m.emu.dispose()
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--install",required=True,type=Path)
    p.add_argument("--project",required=True,type=Path);p.add_argument("--source",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path);p.add_argument("--only");args=p.parse_args()
    source=args.source.read_bytes();r.build(source,True);out=r.ignored_output(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    import pyghidra
    pyghidra.start(install_dir=args.install)
    from java.lang import Object
    from ghidra.program.flatapi import FlatProgramAPI
    project=pyghidra.open_project(args.project,"MasterRallye");consumer=Object()
    program=project.getProjectData().getFile("/MRallye.exe").getReadOnlyDomainObject(consumer,-1,pyghidra.task_monitor())
    transaction=program.startTransaction("R-AI1.2 unsaved native verification")
    try:
        if str(program.getExecutableSHA256())!=r.RETAIL_SHA256:raise ValueError("Unknown Ghidra program")
        api=FlatProgramAPI(program);monitor=pyghidra.task_monitor()
        rows=run_builders(program,api,monitor,source,args.only)
        saved=persistence(program,api,monitor) if args.only in (None,"campaigns","persistence") else {}
        install(program,api,monitor,source,True)
        loader=loader_cases(program,api,monitor) if args.only in (None,"campaigns","loader") else []
        lifecycle=lifecycle_cases(program,api,monitor) if args.only in (None,"campaigns","lifecycle") else []
        report={"status":"STATIC_NATIVE_R_AI12_PASS","cases":len(rows)+bool(saved)+len(loader)+len(lifecycle),"failed":0,"skipped":0,
                "runtime_game_test":False,"project_saved":False,"builders":rows,"persistence":saved,
                "loader":loader,"lifecycle":lifecycle,
                "boundaries":["Broker","heap insertion/free","TLS","native game range output","DLL callback"]}
        out.write_text(json.dumps(report,indent=2)+"\n");print(json.dumps({k:v for k,v in report.items() if k!="builders"},indent=2))
    finally:
        program.endTransaction(transaction,False);program.release(consumer);project.close()


if __name__=="__main__":main()
