"""GT4 command-state interpretation before any Master Rallye translation.

State follows original opcode operands and GS arithmetic. Frame-buffer mask
bits mean *preserve destination*, distinct from enabled colour-write bits.
Scene lighting/environment are separate inputs, never inferred from MatN.
"""
from __future__ import annotations


def interpret(commands):
    s={'alpha_test':True,'alpha_func':6,'alpha_ref':32,'alpha_fail':0,
       'date':False,'datm':1,'depth_test':True,'depth_func':2,'depth_write':True,
       'fbmask':0,'blend':[0,1,0,1,0],'cull':True,'cull_mode':1,'depth_bias':0.,
       'external_texture_index':0,'external_material_index':0,
       'variable_scale':[1.,1.,1.,1.],'variable_offset':[0.,0.,0.,0.],
       'facing':'scene','disabled_capabilities':[],'fog_colour':None,'unknown':[]}
    fog_stack=None
    for n in commands:
        op=n['opcode'];a=n['operands']
        if op in (23,24):s['depth_test']=op==23
        elif op==25:
            if a[0] not in range(4):raise ValueError('invalid PGL depth method')
            s['depth_func']=(0,1,3,2)[a[0]]
        elif op in (26,27):s['alpha_test']=op==26
        elif op==28:s.update(alpha_func=a[0],alpha_ref=a[1])
        elif op in (29,30):s['date']=op==29
        elif op==31:
            if a[0] not in (2,5):raise ValueError('unqualified destination-alpha function')
            s['datm']=int(a[0]==5)
        elif op==32:s['blend']=[(a[0]>>k)&3 for k in (0,2,4,6)]+[a[1]]
        elif op==33:s['fog_colour']=a[0]
        elif op==34:fog_stack=s['fog_colour']
        elif op==35:s['fog_colour']=fog_stack
        elif op==36:s['fbmask']=a[0]
        elif op in (37,38):s['depth_write']=op==38
        elif op==39:s['depth_bias']=a[0]
        elif op==41:s['external_texture_index']=a[0]
        elif op==42:s['external_material_index']=a[0]
        elif op in (45,46):s['cull']=op==45
        elif op==47:s['alpha_fail']=a[0]
        elif op in (78,79):s['cull_mode']=2 if op==78 else 1
        elif op==82:s['variable_scale']=list(a)
        elif op==83:s['variable_offset']=list(a)
        elif op in (86,87):s['facing']='scene' if op==86 else 'constant'
        elif op==88:s['disabled_capabilities']=[19,14]
        else:s['unknown'].append(n)
    s['write_bits']=(~s['fbmask'])&0xffffffff
    if any(v>2 for v in s['blend'][:4]):raise ValueError('reserved GS blend selector')
    if not 0<=s['alpha_func']<=7 or not 0<=s['alpha_fail']<=3 or not 0<=s['depth_func']<=3:
        raise ValueError('invalid GS test method')
    return s


def classify(draw,state,packet):
    """Classify by actual use/attributes; retain effects as first-class draws."""
    if state['unknown']:return 'untranslated_state'
    if draw['texture_table']['kind']=='external':return 'generated_environment'
    if state['write_bits']&0xffffff==0:return 'alpha_mask'
    if not state['depth_write'] or state['date']:return 'multipass_colour'
    if state['fbmask']&0xff000000==0xff000000:return 'rgb_surface_preserving_destination_alpha'
    return 'textured_surface' if packet['texture'] not in (0,511) else 'untextured_surface'


def alpha_compare(value,method,reference):
    return (False,True,value<reference,value<=reference,value==reference,
            value>=reference,value>reference,value!=reference)[method]


def blend_pixel(source,dest,selectors):
    """GS ALPHA: (A-B)*C/128+D; source alpha remains unblended."""
    a,b,c,d,fix=selectors;rgb=[source[:3],dest[:3],(0,0,0)]
    factor=[source[3],dest[3],fix][c]
    return tuple(max(0,min(255,((rgb[a][i]-rgb[b][i])*factor)//128+rgb[d][i])) for i in range(3))+(source[3],)


def write_fragment(source,dest,state,*,depth_pass=True,blend_enabled=True):
    """Reference fragment tests/write masks. None means no framebuffer update."""
    if not depth_pass:return None,False
    if state['date'] and int(dest[3]>=128)!=state['datm']:return None,False
    passed=not state['alpha_test'] or alpha_compare(source[3],state['alpha_func'],state['alpha_ref'])
    write_colour=True;write_depth=state['depth_write'];mask=state['fbmask']
    if not passed:
        fail=state['alpha_fail']
        if fail==0:return None,False
        if fail==1:write_depth=False
        elif fail==2:write_colour=False
        elif fail==3:mask|=0xff000000;write_depth=False
    if not write_colour:return None,write_depth
    colour=blend_pixel(source,dest,state['blend']) if blend_enabled else tuple(source)
    old=int.from_bytes(bytes(dest),'little');new=int.from_bytes(bytes(colour),'little')
    return tuple(((old&mask)|(new&~mask&0xffffffff)).to_bytes(4,'little')),write_depth
