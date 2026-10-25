"""Read-only ModelSet2 command graph, retaining unresolved callbacks/VM state.

Operand layouts follow the local PDTools ModelSetupPS2Command readers.
This module decodes control flow from original bytes; it never executes the
game VM or treats unknown wheel callbacks as identity transforms.
"""
from __future__ import annotations
from collections import deque
from .gt4_source import Reader

# Fixed operand formats. Empty formats are real zero-argument commands, not
# catch-all no-ops. Unsupported opcodes terminate that graph edge explicitly.
FORMATS={2:'B',3:'H',4:'B',5:'H',11:'',12:'',13:'',14:'B',15:'16f',16:'16f',
         17:'3f',18:'3f',19:'4f',20:'f',21:'f',22:'f',23:'',24:'',25:'B',26:'',27:'',
         28:'BB',29:'',30:'',31:'B',32:'BB',33:'I',34:'',35:'',36:'I',37:'',38:'',
         39:'f',40:'4f',41:'B',42:'B',43:'B',44:'H',45:'',46:'',47:'B',
         49:'3f',50:'f',51:'4f',52:'f',53:'HH',54:'f',67:'',72:'H',76:'H',
         78:'',79:'',80:'B',81:'H',82:'4f',83:'4f',84:'H',85:'H',86:'',87:'',88:'',89:'B',90:'H'}


def command_graph(data,start,end,*,budget=8192):
    """Return bounded reachable nodes/edges; branch conditions stay explicit."""
    if not 0<=start<end<=len(data):raise ValueError('invalid command bounds')
    r=Reader(data);todo=deque([start]);nodes={};spans={}
    while todo:
        at=todo.popleft()
        if at in nodes:continue
        if len(nodes)>=budget:raise ValueError('command graph budget exceeded')
        if not start<=at<end:raise ValueError('command target outside model command span')
        op=r.get('B',at)[0];pos=at+1;node={'offset':at,'opcode':op,'operands':[],'edges':[]}
        if op==0:pass
        elif op in (8,9):
            fmt='B' if op==8 else 'H';delta=r.get(fmt,pos)[0];pos+=1 if op==8 else 2
            node.update(operands=[delta],edges=[at+1+delta])
        elif op in (6,7,77):
            if op==7:
                node['parameters']=list(r.get('4f',pos));pos+=16
            else:
                node['parameter']=r.get('H',pos)[0];pos+=2
            count=r.get('B',pos)[0];pos+=1
            if count>64:raise ValueError('command branch budget exceeded')
            table=pos;offsets=r.get(('h' if op==77 else 'H')*count,pos);pos+=2*count
            node['branch_targets']=[table+2*i+d for i,d in enumerate(offsets)]
            node['edges']=list(node['branch_targets'])
            if op in (6,77):node['edges'].insert(0,pos)
            node['qualification']='LOD selection' if op==7 else 'UNRESOLVED_CALLBACK_OR_VM_CONDITION'
        elif op==10:
            count=r.get('B',pos)[0];pos+=1
            if count>32:raise ValueError('bbox budget exceeded')
            node['bounds']=list(r.get('f'*(count*3),pos));pos+=count*12
            delta=r.get('H',pos)[0];target=pos+delta;pos+=2
            node['edges']=[pos,target];node['qualification']='BOUNDING_TEST_NOT_EXECUTED'
        elif op in FORMATS:
            fmt=FORMATS[op];node['operands']=list(r.get(fmt,pos))
            import struct
            pos+=struct.calcsize('<'+fmt);node['edges']=[pos]
        else:node['qualification']='UNSUPPORTED_OPCODE';node['error']=f'unknown operand layout {op:#x}'
        if pos>end:raise ValueError('command operands exceed model span')
        for other,stop in spans.items():
            if at<stop and other<pos:raise ValueError('command target overlaps another command operand')
        spans[at]=pos;node['end']=pos;node['raw']=data[at:pos].hex();nodes[at]=node
        todo.extend(node['edges'])
    return {'start':start,'end':end,'nodes':[nodes[k] for k in sorted(nodes)],
            'unsupported':[n for n in nodes.values() if n.get('error')],
            'policy':'control-flow graph only; callbacks, VM and matrix effects retain original operands'}


def binding_trace(graph,*,lod=0,callbacks=None):
    """Trace one explicit path and retain per-draw state and transform commands.

    Unknown callbacks stop the trace instead of choosing a visually convenient
    branch. Callers may supply branch choices for diagnostics; these choices do
    not qualify the original callback semantics.
    """
    nodes={n['offset']:n for n in graph['nodes']};at=graph['start'];seen=set();draws=[];state=[];transforms=[];matrix_stack=[];texture={'kind':'internal','index':0}
    while at in nodes:
        if at in seen:raise ValueError('cyclic command path')
        seen.add(at);n=nodes[at];op=n['opcode'];args=n['operands']
        if n.get('error'):return {'draws':draws,'blocked_at':n,'state':state}
        if op==0:return {'draws':draws,'blocked_at':None,'state':state}
        if op in (4,5,53):draws.append({'shape':args[0],'command_offset':at,'texture_table':dict(texture),'commands':list(state),'transforms':list(transforms),'tween':args[1] if op==53 else None})
        elif op in (43,44):texture={'kind':'internal','index':args[0]}
        elif op in (80,81):texture={'kind':'external','index':args[0]}
        elif op==12:matrix_stack.append(list(transforms))
        elif op==13:
            if not matrix_stack:raise ValueError('matrix stack underflow')
            transforms=matrix_stack.pop()
        elif op in range(14,23) or op in (67,72,76,84,85,89,90):transforms.append(n)
        elif op in range(23,40) or op in (41,42,45,46,47,78,79,82,83,86,87,88):state.append(n)
        if op==7:
            if not 0<=lod<len(n['branch_targets']):raise ValueError('LOD outside source branches')
            at=n['branch_targets'][lod]
        elif op in (6,77):
            key=str(n['parameter']);choices=callbacks or {}
            if key not in choices:return {'draws':draws,'blocked_at':n,'state':state}
            branch=choices[key]
            if type(branch)is not int or not 0<=branch<len(n['branch_targets']):raise ValueError('callback branch outside source table')
            # Native CarModel callback 0 returns tail-light state; 7 returns
            # time zone. Other callbacks can modify matrices, even if their
            # return branch skips a shape. Preserve that uncertainty in scope.
            if op==77 or n['parameter'] not in (0,7):
                transforms.append({'callback':n['parameter'],'diagnostic_branch':branch,'qualification':'UNRESOLVED_SIDE_EFFECTS'})
            at=n['branch_targets'][branch]
        elif op==10:at=n['edges'][0] # Render inside bounding box for offline diagnostics.
        else:at=n['edges'][0] if n['edges'] else -1
    return {'draws':draws,'blocked_at':{'offset':at,'error':'path escaped graph'},'state':state}


def translate_invocation(draw,*,shadow=False,packet_external=False):
    """Translate a direct byte trace through the shared conservative router."""
    from .gt4_source import translate_pass
    commands=[];ignored=[]
    for n in draw['commands']:
        op=n['opcode'];a=n['operands']
        if op==26:commands.append('EnableAlphaTest')
        elif op==27:commands.append('DisableAlphaTest')
        elif op==28:
            funcs=['NEVER','ALWAYS','LESS','LEQUAL','EQUAL','GEQUAL','GREATER','NOTEQUAL']
            if a[0]>=len(funcs):commands.append('UnknownAlphaFunction()')
            else:commands.append(f'AlphaFunction({funcs[a[0]]}, {a[1]})')
        elif op==29:commands.append('EnableDestinationAlphaTest')
        elif op==30:commands.append('DisableDestinationAlphaTest')
        elif op==31:commands.append(f'DestinationAlphaFunc({a[0]})')
        elif op==32:
            bits,fix=a;values=[(bits>>s)&3 for s in (0,2,4,6)]+[fix]
            commands.append('BlendFunction('+', '.join(map(str,values))+')')
        elif op==36:commands.append(f'ColorMask({(~a[0])&0xffffffff:#x})')
        elif op==37:commands.append('DisableDepthMask')
        elif op==38:commands.append('EnableDepthMask')
        elif op==39 and a[0]!=0:commands.append(f'DepthBias({a[0]})')
        elif op in (23,24,25,41,42,47,82,83,86,87,88):
            # Retain rather than silently flatten depth/alpha-fail and variable
            # colour/texgen state into a paint material.
            commands.append(f'UntranslatedState_{op}({a})')
        else:ignored.append(n)
    result=translate_pass(commands,shadow=shadow,external_texture=packet_external or draw['texture_table']['kind']=='external')
    result.update(texture_table=draw['texture_table'],source_command_offset=draw['command_offset'],retained_commands=draw['commands'],non_material_commands=ignored)
    if draw['transforms'] or draw['tween'] is not None:
        result.update(route='unsupported_instance_transform_or_tween',transforms=draw['transforms'])
    return result
