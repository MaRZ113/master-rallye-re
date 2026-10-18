import rabbitizer,struct,sys
b=open(r"D:\Game\Master Rallye PS2\SLES_509.06",'rb').read()
for rng in sys.argv[1:]:
    lo,hi=[int(x,16) for x in rng.split('-')]
    print('==',rng)
    for va in range(lo,hi,4):
        w=struct.unpack_from('<I',b,va-0xff000)[0]
        ins=rabbitizer.Instruction(w,va,rabbitizer.InstrCategory.R5900)
        t=ins.disassemble()
        if any(k in t for k in ('lui','c.','jal ','lwc1','mtc1','sw ','addiu')): print(f"{va:06x} {w:08x} {t}")
