"""Identity-filtered debugger recipe, not an engine API or spawn feature.

Discovery reads one original gaAiHayBale initializer. Explicit known target
pointers are required for the selected lifecycle recipe. Budgets count matched
identity observations, not the debugger's global breakpoint hits.
"""
import argparse
import importlib.util
from pathlib import Path


def pointer(value):
    if not isinstance(value,int) or value < 0x10000 or value > 0x7FFFFFFC or value % 4:
        raise ValueError('Verified aligned live32-bit pointer required')
    return f'{value:08X}'


def point(address,name,predicate,fields,cap=2):
    counter='$rp12_'+name+'_matches';a=f'{address:08X}'
    condition=f'({predicate}) && ({counter} < .{cap})'
    return [f'mov {counter}, 0',f'bp {a}, "rp12_{name}"',
        f'SetBreakpointCondition {a}, 0',f'SetBreakpointFastResume {a}, 0',
        f'SetBreakpointSilent {a}, 1',
        f'SetBreakpointLogCondition {a}, "{condition}"',
        f'SetBreakpointLog {a}, "PROP12 event={name} tid={{x:tid()}} ecx={{p:ecx}} {fields} matched={{u:{counter}+1}}"',
        f'SetBreakpointCommandCondition {a}, "{condition}"',
        f'SetBreakpointCommand {a}, "mov {counter}, {counter}+1"']


def discovery():
    # Entry vtable/stack owner association is grounded in original4C9CF0
    # prologue+4C9D7F:124-byte saved/local frame, owner at ESP+80 ->entryESP+4.
    lines=['// Exact retail EXE bf8a...; one original owner discovery only.',
           '// Debugger variables only, no run/call/register/native data edits.',
           '// User cold-load control <=60s; no match does not authorize spawning.']
    lines += point(0x4C9CF0,'hay_owner','[ecx] == 00691470',
                   'egg={p:[esp+4]} caller={p:[esp]}',1)
    return '\n'.join(lines)+'\n'


def selected(egg,body,instance,prototype):
    egg,body,instance,prototype=map(pointer,(egg,body,instance,prototype))
    # Use a current ORIGINAL prop identity confirmed by discovery/owner join,
    # never previous-process pointers or one of the vehicle-only controls.
    lines=['// ORIGINAL verified live prop only; all pointers are session-local.',
           '// No automatic run/call/admission; game data is never written.',
           '// Two MATCHES per point. Global frontend hits cannot consume caps.']
    recipes=[
        (0x43E2A0,'admission',f'[esp+4] == {egg}','egg={p:[esp+4]} caller={p:[esp]}'),
        (0x56EEF0,'attach',f'[esp+4] == {egg}',
         'egg={p:[esp+4]} body={p:[esp+8]} category={x:[esp+C]}'),
        # At these original direct calls: backend local/saved28 + argument4
        # + return4 ->entry childESP+28 holds the parent Egg argument.
        (0x621220,'clone',f'[esp] == 0056EFBA && [esp+28] == {egg} && [esp+4] == {prototype}',
         'prototype={p:[esp+4]} egg={p:[esp+28]}'),
        (0x621310,'bind',f'ecx == {instance} && [esp+4] == {body}','body={p:[esp+4]}'),
        (0x4F5840,'retire',f'ecx == {egg}','caller={p:[esp]}'),
        (0x4F5780,'egg_destroy',f'ecx == {egg}','caller={p:[esp]}'),
        (0x4FEDC0,'body_destroy',f'ecx == {body}','flags={x:[esp+4]} caller={p:[esp]}'),
        (0x6212C0,'shape_destroy',f'ecx == {instance} || ecx == {prototype}','caller={p:[esp]}'),
    ]
    for address,name,condition,fields in recipes:
        lines += point(address,name,condition,fields)
    lines += ['// End control manually after exit; remove only rp12_* breakpoints.',
              '// Pointer membership/disappearance is not destructor/refcount proof.']
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--egg',type=lambda v:int(v,16))
    parser.add_argument('--body',type=lambda v:int(v,16))
    parser.add_argument('--instance',type=lambda v:int(v,16))
    parser.add_argument('--prototype',type=lambda v:int(v,16))
    args=parser.parse_args()
    helper=Path(__file__).resolve().parents[2]/'tools/rigid_lifecycle_probe.py'
    spec=importlib.util.spec_from_file_location('original_probe_identity',helper)
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    verifier.verify_executable(args.exe)
    values=(args.egg,args.body,args.instance,args.prototype)
    if any(v is not None for v in values) and not all(v is not None for v in values):
        raise ValueError('All four independently verified current target pointers required')
    script=selected(*values) if all(v is not None for v in values) else discovery()
    with args.output.open('x',encoding='utf-8') as f:f.write(script)


if __name__=='__main__':main()
