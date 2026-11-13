"""Bounded Xbox vertex-token inspection, independently authored from encodings.

This does not emulate NV2A precision, driver linking, GPU state or rasterization.
Original binary payloads are supplied privately, never embedded in this module.
"""
import math
import struct

MAC=('NOP','MOV','MUL','ADD','MAD','DP3','DPH','DP4','DST','MIN','MAX','SLT','SGE','ARL')
ILU=('NOP','MOV','RCP','RCC','RSQ','EXP','LOG','LIT')
OUTPUTS={0:'position',3:'V0',4:'V1',5:'fog',6:'point_size',7:'back0',8:'back1',9:'T0',10:'T1',11:'T2',12:'T3',15:'address'}
SCHEMA='nv2a-vertex-inspection/1'
MAX_INSTRUCTIONS=136


def decode_program(raw):
    if not isinstance(raw,(bytes,bytearray)):raise ValueError('Vertex program bytes required')
    if len(raw)<4 or len(raw)>4+MAX_INSTRUCTIONS*16:raise ValueError('vertex program byte budget')
    kind,count=struct.unpack_from('<HH',raw)
    if kind!=0x2078 or not 1<=count<=MAX_INSTRUCTIONS or len(raw)!=4+count*16:
        raise ValueError('vertex program header/count/span')
    instructions=[]
    for index in range(count):
        w=struct.unpack_from('<4I',raw,4+index*16);a,b,c=w[1:]
        mac=(a>>21)&15;ilu=(a>>25)&7
        if mac>=len(MAC):raise ValueError('reserved vertex MAC opcode')
        constant=(a>>13)&255;vertex=(a>>9)&15
        def argument(mux,reg,neg,swizzle):
            if mux not in(1,2,3):return {'kind':'unused','raw_mux':mux}
            return {'kind':('unused','temporary','input','constant')[mux],
                    'index':reg if mux==1 else vertex if mux==2 else constant-96,
                    'negate':bool(neg),'swizzle':list(swizzle),'relative':bool(c&2)if mux==3 else False}
        inputs={
            'A':argument((b>>26)&3,(b>>28)&15,(a>>8)&1,[(a>>k)&3 for k in(6,4,2,0)]),
            'B':argument((b>>11)&3,(b>>13)&15,(b>>25)&1,[(b>>k)&3 for k in(23,21,19,17)]),
            'C':argument((c>>28)&3,((b&3)<<2)|(c>>30),(b>>10)&1,[(b>>k)&3 for k in(8,6,4,2)])}
        output_index=(c>>3)&255;output_kind='output'if c&0x800 else'constant'
        outputs={'temporary_index':(c>>20)&15,'mac_mask':(c>>24)&15,'ilu_mask':(c>>16)&15,
                 'external_mask':(c>>12)&15,'external_from':'ILU'if c&4 else'MAC',
                 'external_kind':output_kind,'external_index':output_index&15 if output_kind=='output'else output_index-96,
                 'external_name':OUTPUTS.get(output_index&15,'reserved')if output_kind=='output'else'constant'}
        final=bool(c&1)
        if final!=(index==count-1):raise ValueError('vertex program termination mismatch')
        instructions.append({'ordinal':index,'mac':MAC[mac],'ilu':ILU[ilu],
                             'inputs':inputs,'outputs':outputs,'final':final,
                             'uninterpreted_word0':w[0]})
    return {'schema':SCHEMA,'instructions':instructions,'count':count}


def describe(program):
    """Stable readable typed report, not a recovered source-code listing."""
    lines=[]
    def src(s):
        if s['kind']=='unused':return '?'
        prefix={'temporary':'r','input':'v','constant':'c'}[s['kind']]
        return ('-'if s['negate']else'')+prefix+('['+str(s['index'])+']'if prefix=='c'else str(s['index']))+'.'+''.join('xyzw'[i]for i in s['swizzle'])+(' REL'if s['relative']else'')
    mask=lambda n:''.join('xyzw'[i]for i in range(4)if n&(8>>i))
    mac_inputs={'NOP':'','MOV':'A','MUL':'AB','ADD':'AC','MAD':'ABC','DP3':'AB','DPH':'AB','DP4':'AB','DST':'AB','MIN':'AB','MAX':'AB','SLT':'AB','SGE':'AB','ARL':'A'}
    for item in program['instructions']:
        out=item['outputs'];operations=[]
        for path,key in [('MAC','mac'),('ILU','ilu')]:
            op=item[key]
            if op=='NOP':continue
            destinations=[];m=out['mac_mask'if path=='MAC'else'ilu_mask']
            index=out['temporary_index']if path=='MAC'or item['mac']=='NOP'else 1
            if m:destinations.append('r'+str(index)+'.'+mask(m))
            if out['external_mask']and out['external_from']==path:
                destinations.append((out['external_name']if out['external_kind']=='output'else'c['+str(out['external_index'])+']')+'.'+mask(out['external_mask']))
            keys=mac_inputs[op]if path=='MAC'else'C'
            operations.append(op+' '+','.join(destinations)+' <- '+', '.join(src(item['inputs'][k])for k in keys))
        lines.append(str(item['ordinal'])+': '+' | '.join(operations))
    return lines


def evaluate_outputs(program, inputs, constants, *, outputs=('V0','T0','T1','T2'), initial_temporaries=None):
    """Floating-point diagnostic for the selected arithmetic subset, not a GPU.

    Constants and input vectors are explicit. Undefined temporary components
    propagate until overwritten; a requested undefined output fails closed.
    Co-issued MAC/ILU read the same previous state. No implicit R11=0, lighting,
    viewport, texture matrix, rasterizer precision or runtime state is supplied.
    """
    if program.get('schema')!=SCHEMA or not 1<=len(program['instructions'])<=MAX_INSTRUCTIONS:
        raise ValueError('Decoded bounded vertex program required')
    if not isinstance(outputs,(list,tuple))or not outputs or any(x not in OUTPUTS.values() for x in outputs):
        raise ValueError('Explicit supported vertex outputs required')
    def vector(value):
        if not isinstance(value,(list,tuple))or len(value)!=4 or any(type(x)not in(int,float)or not math.isfinite(x) for x in value):
            raise ValueError('Finite explicit vertex vector required')
        return list(value)
    if not isinstance(inputs,dict)or not isinstance(constants,dict)or (initial_temporaries is not None and not isinstance(initial_temporaries,dict)):
        raise ValueError('Explicit bounded vertex register maps required')
    if any(type(k)is not int or not 0<=k<=15 for k in inputs)or any(type(k)is not int or not -96<=k<=159 for k in constants):
        raise ValueError('Vertex register map index budget')
    ins={k:vector(v)for k,v in inputs.items()};con={k:vector(v)for k,v in constants.items()}
    temp={k:vector(v)for k,v in (initial_temporaries or {}).items()}
    if any(type(k)is not int or not 0<=k<=12 for k in temp):raise ValueError('Temporary register budget')
    result={}
    def arithmetic(op,a,b,c):
        def binary(x,y,fn):return None if x is None or y is None else fn(x,y)
        if op=='MOV':return a
        if op in('DP3','DP4'):
            terms=[binary(a[i],b[i],lambda x,y:x*y)for i in range(3 if op=='DP3'else 4)]
            return [None if None in terms else sum(terms)]*4
        if op in('MUL','ADD','MAX','MAD'):
            values=[]
            for i in range(4):
                if op=='MUL':v=binary(a[i],b[i],lambda x,y:x*y)
                elif op=='ADD':v=binary(a[i],c[i],lambda x,y:x+y)
                elif op=='MAX':v=binary(a[i],b[i],max)
                else:v=binary(binary(a[i],b[i],lambda x,y:x*y),c[i],lambda x,y:x+y)
                values.append(v)
            return values
        raise ValueError('Unsupported diagnostic vertex MAC '+op)
    keys={'MOV':'A','MUL':'AB','ADD':'AC','MAD':'ABC','DP3':'AB','DP4':'AB','MAX':'AB'}
    for item in program['instructions']:
        if item['uninterpreted_word0']:raise ValueError('Unknown vertex instruction word0')
        def read(name):
            spec=item['inputs'][name];kind=spec['kind'];idx=spec.get('index')
            if spec.get('relative'):raise ValueError('Relative vertex constants unsupported')
            if kind=='temporary':v=temp.get(idx,[None]*4)
            elif kind in('input','constant'):
                source=ins if kind=='input'else con
                if idx not in source:raise ValueError('Missing explicit vertex '+kind+' '+str(idx))
                v=source[idx]
            else:raise ValueError('Missing active vertex operand')
            return [None if v[i]is None else (-v[i]if spec['negate']else v[i])for i in spec['swizzle']]
        mac=None;ilu=None
        if item['mac']!='NOP':
            if item['mac']not in keys:raise ValueError('Unsupported diagnostic vertex MAC '+item['mac'])
            values={k:read(k)for k in keys[item['mac']]}
            mac=arithmetic(item['mac'],values.get('A'),values.get('B'),values.get('C'))
        if item['ilu']!='NOP':
            c=read('C');op=item['ilu']
            if op=='MOV':ilu=c
            elif op in('RSQ','RCC'):
                value=c[0]
                if value is None:ilu=[None]*4
                elif value==0:raise ValueError('Degenerate reciprocal diagnostic input')
                else:ilu=[1/math.sqrt(abs(value))if op=='RSQ'else math.copysign(min(max(abs(1/value),2**-64),2**64),value)]*4
            else:raise ValueError('Unsupported diagnostic vertex ILU '+op)
        out=item['outputs']
        def write(target,mask,value):
            if value is None:raise ValueError('Active output from NOP vertex operation')
            for i in range(4):
                if mask&(8>>i):target[i]=value[i]
        for path,value in [('MAC',mac),('ILU',ilu)]:
            mask=out['mac_mask'if path=='MAC'else'ilu_mask']
            if mask:
                index=out['temporary_index']if path=='MAC'or item['mac']=='NOP'else 1
                if index>12:raise ValueError('Reserved temporary destination')
                write(temp.setdefault(index,[None]*4),mask,value)
            if out['external_mask']and out['external_from']==path:
                if out['external_kind']!='output':raise ValueError('Vertex constant writes unsupported')
                name=out['external_name'];target=temp.setdefault(12,[None]*4)if name=='position'else result.setdefault(name,[None]*4)
                write(target,out['external_mask'],value)
                if name=='position':result[name]=target
    selected={}
    for name in outputs:
        value=result.get(name)
        if value is None or any(x is None or not math.isfinite(x)for x in value):
            raise ValueError('Undefined requested vertex output '+name+'; explicit initial state required')
        selected[name]=list(value)
    return selected
