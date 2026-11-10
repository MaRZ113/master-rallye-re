"""Evidence-bound pool insertion; native exclusions, shuffle and drivers stay native.

Only the original retail adapter is qualified. Cup/Invitation share pool
bodies; their independent eligibility uses the original Race/Type getter.
"""
import struct

SUPPORTED={'T1':('quick_race','rallye_cup','master_rallye'),'T2':('quick_race','rallye_cup','master_rallye'),'T3':('quick_race','rallye_cup','invitation','master_rallye'),'T4':()}
# Existing parent hooks have already appended ID26/27. Values are physical
# sentinels, independent of menu order. Reentry includes BOTH player exclusions.
T1=(('quick_race',0x458167,0x458137,0x4582d5),('rallye_cup',0x45ad14,0x45ace2,0x45ae66),('master_rallye',0x451ed9,0x451ea7,0x45202b))
T3=(('quick_race',0x4581f8,0x4581cc,0x458201,'468d56f283fa077ccb'),('master_rallye',0x451f4e,0x451f22,0x451f57,'468d4ef283f9077ccb'),('rallye_cup',0x45ad89,0x45ad5d,0x45ad92,'468d4ef283f9077ccb'),('invitation',0x45acbb,0x45ac8f,0x45acc4,'468d56f283fa077ccb'))


def validate_eligibility(cls,flags):
    for mode,row in flags.items():
        if row['enabled'] and mode not in SUPPORTED[cls]:raise ValueError(f'{cls} {mode} AI insertion is not qualified; shared/restricted event remains disabled')


def emit(code,rows,image,pe,native,hooks):
    for row in rows:validate_eligibility(row['vehicle_class'],row['ai_eligibility'])
    for mode,hook,reentry,exit_ in T1:
        ids=[r['physical_id']for r in rows if r['vehicle_class']=='T1'and r['ai_eligibility'][mode]['enabled']]
        if not ids:continue
        label='pool_t1_'+mode;code.label(label)
        for k,physical in enumerate(ids):
            native.i0._comparison_bytes(code,'esi',27 if k==0 else ids[k-1]+1);code.jne(label+str(k))
            code.emit(b'\xbe'+struct.pack('<I',physical));code.jump(reentry);code.label(label+str(k))
        native.i0._comparison_bytes(code,'esi',ids[-1]+1);code.jne(label+'_parent')
        code.emit(b'\xbe\x07\0\0\0');code.jump(exit_);code.label(label+'_parent')
        code.jump(native.branch_target(image,pe,hook,0xe9));hooks.append((hook,label,0xe9))
    for mode,hook,reentry,exit_,expected in T3:
        shared=mode in ('rallye_cup','invitation')
        selected=[r for r in rows if r['vehicle_class']=='T3'and (any(r['ai_eligibility'][m]['enabled']for m in ('rallye_cup','invitation'))if shared else r['ai_eligibility'][mode]['enabled'])]
        ids=[r['physical_id']for r in selected]
        if not ids:continue
        off=native.registry.va_to_file_offset(pe,hook,9)
        if image[off:off+9]!=bytes.fromhex(expected):raise ValueError('T3 AI loop preimage conflict at '+hex(hook))
        label='pool_t3_'+mode;code.label(label)
        # Reproduce increment, derived counter and signed branch exactly.
        code.emit(bytes.fromhex(expected)[:7]);code.emit(b'\x0f\x8c\0\0\0\0');code.rel32.append((len(code.code)-4,len(code.code),reentry))
        for k,physical in enumerate(ids):
            native.i0._comparison_bytes(code,'esi',21 if k==0 else ids[k-1]+1);code.je(label+'_select'+str(k))
        code.jump(label+'_done')
        for k,physical in enumerate(ids):
            code.label(label+'_select'+str(k))
            if shared:
                # Existing native Race singleton and integer getter. Save all
                # registers/flags around Broker calls; no persistent mode data.
                code.emit(b'\x9c\x60');code.call(0x4ada50);code.emit(b'\x8b\xc8');code.call(0x4abe90)
                for key,value in (('rallye_cup',6),('invitation',8)):
                    if selected[k]['ai_eligibility'][key]['enabled']:
                        code.emit(b'\x83\xf8'+bytes([value]));code.je(label+'_allow'+str(k))
                code.emit(b'\x61\x9d');code.jump(label+'_select'+str(k+1)if k+1<len(ids)else label+'_done')
                code.label(label+'_allow'+str(k));code.emit(b'\x61\x9d')
            code.emit(b'\xbe'+struct.pack('<I',physical));code.jump(reentry)
        code.label(label+'_done')
        # Restore ordinary stock loop sentinel and its derived scratch register;
        # continue at the ORIGINAL gated special-vehicle additions.
        code.emit(b'\xbe\x15\0\0\0'+(b'\x8d\x56\xf2'if mode in ('quick_race','invitation')else b'\x8d\x4e\xf2'))
        code.jump(exit_);hooks.append((hook,label,0xe9,9))
