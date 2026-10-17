import sys,statistics as st
sys.path.insert(0,sys.argv[1]);import gsdump
from collections import defaultdict
hdr,shot,gs,pk=gsdump.replay(sys.argv[2])
g=defaultdict(list)
for k,rgba,f,xyz,fogcol in gs.kicks:g[k].append((rgba,f,xyz,fogcol))
def a(b):return 'A%dB%dC%dD%d'%(b&3,b>>2&3,b>>4&3,b>>6&3)
rows=sorted(g.items(),key=lambda kv:-len(kv[1]))
print('ptype attr ctx TBP PSM TCC TFX ALPHA FIX FBP TEST | n | RGBA med | A med | F p10/50/90 | FOGCOL')
for k,v in rows[:40]:
    ptype,attr,ctx,tbp,psm,tcc,tfx,al,fix,fbp,test=k
    flags=''.join(c for c,b in zip('ITFAL',(attr>>3&1,attr>>4&1,attr>>5&1,attr>>6&1,attr>>7&1)) if b)
    rs=[st.median(x[0][i] for x in v) for i in range(4)];fs=sorted(x[1] for x in v);n=len(fs)
    print(f'{ptype} {flags:5} c{ctx} tbp{tbp:5x} psm{psm:2x} tcc{tcc} tfx{tfx} {a(al)} fix{fix:3d} fb{fbp:3x} t{test:04x} | {len(v):6d} | {rs[0]:5.0f}{rs[1]:5.0f}{rs[2]:5.0f} {rs[3]:4.0f} | {fs[n//10]:3d}{fs[n//2]:4d}{fs[9*n//10]:4d} | {v[0][3]:06x}')
