"""Verify known original registry sites without modifying a binary.

This is a bounded evidence verifier, not a claim that indirect consumers or
every engine table have been exhausted. Hashes describe the inspected target.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import sdk_capacity_native as native


def inspect(raw):
    pe=native.registry.parse_pe(raw);rows=[]
    def site(owner,va,expected,meaning):
        off=native.registry.va_to_file_offset(pe,va,len(expected));actual=raw[off:off+len(expected)]
        if actual!=expected:raise ValueError('Original capacity site differs: '+owner+' at '+hex(va))
        rows.append({'classification':'Stock Native','owner':owner,'va':hex(va),
            'file_offset':off,'bytes':actual.hex(),'meaning':meaning})
    site('registry_allocator',0x45a3df,bytes.fromhex('68000c0000'),'PUSH 0xC00; singleton heap object, not global fixed buffer')
    for a,b in [(0x458cf3,'6a1a8d4604'),(0x458e45,'6a1a83c604'),(0x686795,'6a1a6a348b45f0')]:
        site('vehicle_lifetime_count',a,bytes.fromhex(b),'26 records; imm8 is sign-extended into a 32-bit stack argument')
    for a,b in [(0x458d10,'8d8e4c050000'),(0x458e2a,'8d864c050000'),(0x6867b2,'054c050000')]:
        site('racetest_lifetime_base',a,bytes.fromhex(b),'RaceTest starts at registry+0x54C')
    for a,disp in native.registry.SECONDARY_INIT_LEAS:
        site('racetest_initializer',a,bytes.fromhex('8d8e')+struct.pack('<I',disp),'One of 39 initialized RaceTest rows, stride44')
    for a,disp in native.registry.SECONDARY_CONSUMER_DISPS:
        site('racetest_consumer_displacement',a+3,struct.pack('<I',disp),'Verified displacement operand, not an independent vehicle-count limit')
    for owner,a,b,meaning in [
        ('frontend_class_counts',0x480a4a,'b807000000894620894624','T1/T2 counts7/7 at state+20/+24'),
        ('frontend_T3_count',0x480a62,'c746280b000000','T3 count11 at state+28'),
        ('frontend_position_publisher',0x4819a4,'83fe0c7cb1','12 position keys; not a registry-sized vehicle buffer'),
        ('frontend_reverse_T1',0x481e55,'83f807','Signed physical-ID partition threshold7'),
        ('frontend_reverse_T2',0x481e68,'83f80e','Signed physical-ID partition threshold14'),
        ('result_CarID',0x47c6d5,'894108','MOV [ECX+8],EAX; 32-bit physical CarID'),
        ('network_selected_physical_id',0x481c68,'e8b3010000','CALL physical mapping helper481E20'),
        ('network_selected_setter',0x481c75,'e8c6bb0200','CALL4AD840; stores selected physical ID as Broker Int'),
        ('network_byte_writer',0x434453,'884605','MOV [ESI+5],AL; selectedCar wire field is one byte'),
        ('network_byte_reader_clear',0x433f9f,'33d2','Clear EDX before loading unsigned byte'),
        ('network_byte_reader',0x433fa5,'8a5605','MOV DL,[ESI+5]; physical ID256 would alias0'),
        ('network_peer_store',0x434161,'898804080000','MOV [EAX+804],ECX; received identity widened back to dword'),
    ]:site(owner,a,bytes.fromhex(b),meaning)
    text=next(s for s in pe['sections']if s['name']=='.text')
    lo=text['raw_offset'];hi=lo+text['raw_size'];candidates=[]
    for off in range(lo,hi-4):
        if raw[off]!=0xe8:continue
        address=pe['image_base']+text['rva']+off-lo
        if address+5+struct.unpack_from('<i',raw,off+1)[0]==0x45a3c0:candidates.append(hex(address))
    return {'source_sha256':hashlib.sha256(raw).hexdigest(),'source_bytes':len(raw),
        'reference_identity_matches':hashlib.sha256(raw).hexdigest()==native.i0.RETAIL_SHA256,
        'sites':rows,'verified_site_count':len(rows),
        'raw_direct_call_candidates':candidates,
        'candidate_coverage':'Byte-pattern candidates in .text; Ghidra function ownership is separate evidence',
        'registry_layout':{'header':4,'count':26,'record_stride':52,'RaceTest_count':39,'RaceTest_stride':44,'bytes':3072},
        'maximum_global_CarID':None,
        'coverage':'Known original storage/lifecycle, 39 RaceTest initializers, 11 direct tail consumers, frontend and paired network sites; not all indirect engine consumers',
        'status':'PASS_VERIFIED_CAPACITY_SITES; STATIC_NOT_GAMEPLAY'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();report=inspect(a.source.read_bytes());a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k]for k in ('status','verified_site_count','maximum_global_CarID')}))
