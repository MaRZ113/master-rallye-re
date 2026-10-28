"""GT3-specific state layer; numeric material names never imply semantic roles.

The shared GS interpreter handles common opcodes. GT3 mode2/3 parameters remain
explicit source values, not GT4 variable colors or invented native MR shaders.
"""
from .gt4_materials import interpret as gs_interpret

def interpret(commands):
    common=[];mode2=None;mode3=None;hints=[]
    for n in commands:
        op=n['opcode'];a=n['operands']
        if op==50:mode2=[a[0],a[0],a[0],0.]
        elif op==51:mode2=list(a)
        elif op==54:mode3=[a[0],a[0],a[0],0.]
        elif op==55:mode3=list(a)
        elif op in (40,49):hints.append(n)
        else:common.append(n)
    state=gs_interpret(common)
    state['gt3_parameters']={'mode2':mode2,'mode3':mode3,'hints':hints}
    state['gt3_lighting_pending']=any(any(v!=0 for v in x)for x in (mode2,mode3)if x is not None)
    return state
