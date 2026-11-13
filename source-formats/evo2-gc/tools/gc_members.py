import sys,os,re
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','decoders'))
from evo2_formats import pod2_members,member_bytes
BS=chr(92)
pc=pod2_members(open(sys.argv[1],'rb').read());gcd=open(sys.argv[2],'rb').read();gc=pod2_members(gcd)
P=set(m.name.upper().replace(BS,'/') for m in pc)
extra=[m for m in gc if m.name.upper().replace(BS,'/') not in P]
print(len(extra))
for m in extra:print(m.name.replace(BS,'/'),m.size if hasattr(m,'size') else '')
for m in gc:
    n=m.name.upper().replace(BS,'/')
    if n.endswith(('JWR.TRK','SMT.TRK','CFRT.TRK','WDRT.TRK')):
        b=member_bytes(gcd,m);print('==',n);print(b[:1500].decode('latin1','replace'))
