"""Probe of the PC course tag1500 block (after tag1400). Grammar found by reading the data:
  u32 1500, u32 sector count S, then per sector: u32 n, n x (f32 x, f32 0, f32 z, f32 0, f32 s, f32 0, u32 link), u32 a, a x u32 id
link = another sector index or 0xFFFFFFFF; id = render batch index (hypothesis checked below against batch bounds)."""
import sys,struct,collections,json,glob
sys.path.insert(0,'src'); sys.path.insert(0,'ps2-research/track-coll2')
import tag1400_io as io
from master_rallye.tag100_diff import extract_tag100_from_dx_bytes
from master_rallye.dx_course import parse_course_dx_bytes

def parse(r):
    W=struct.unpack('<%dI'%(len(r)//4),r); F=struct.unpack('<%df'%(len(r)//4),r)
    assert W[0]==1500
    o=2; out=[]
    for e in range(W[1]):
        n=W[o]; o+=1; pts=[]
        for k in range(n):
            pts.append((F[o],F[o+1],F[o+2],F[o+3],F[o+4],F[o+5],W[o+6])); o+=7
        a=W[o]; o+=1; ids=list(W[o:o+a]); o+=a
        out.append({'points':pts,'ids':ids})
    return out, o*4

def main(path):
    dx=open(path,'rb').read()
    _,_,_,r=io.split_suffix(extract_tag100_from_dx_bytes(dx,'t').raw)
    ents,used=parse(r)
    m=parse_course_dx_bytes(dx,'t')
    return ents,used,len(r),m

if __name__=='__main__':
    res={}
    for p in sorted(glob.glob('D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Course/*/*.dx')):
        try:
            ents,used,size,m=main(p)
            consts=collections.Counter((pt[1],pt[3],pt[5]) for e in ents for pt in e['points'])
            ids=[i for e in ents for i in e['ids']]
            res[p.split('/')[-1].split(chr(92))[-1]]={'sectors':len(ents),'batches':len(m.course_batches),'root_control':list(m.course_wrapper.control_words) if m.course_wrapper else None,
                'consumed_all':used==size,'max_id':max(ids) if ids else None,'zero_words':consts.most_common(2),
                's_values':collections.Counter(round(pt[4],4) for e in ents for pt in e['points']).most_common(3)}
        except Exception as ex:
            res[p]={'error':str(ex)[:100]}
    for k,v in res.items(): print(k,v)
