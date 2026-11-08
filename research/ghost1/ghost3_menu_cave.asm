; GHOST1 G3: native GHOST mode in the Quick Race mode select (retail MRallye.exe bf8aef32...).
; Assembled at 0x0068E390 by tools/ghidra/AsmCave.java. Strings (written by ghost1_build.py):
;   0x0068E800 "Frontend/QuickModeSelect/GhostList"
;   0x0068E830 "Frontend/QuickModeSelect/Ghost"
;   0x0068E850 "Frontend/QuickRace/GhostMode"
; All branches must assemble short (Ghidra picks 66-prefixed rel16 Jcc for long ones).
; Broker ABI: 0x4D0580 key ctor (thiscall &slot, char*, RET 4); 0x4D8EC0 -> Broker (no args);
; setters on Broker (args &key,value, RET 8): int 0x4D8000, bool 0x4D7AA0, list 0x4D8880;
; int getter 0x4D6760 (thiscall Broker, &key, RET 4).
; Text table: CALL 0x485CF0 -> obj; CALL [[obj]+0xC] (thiscall obj, group, index, RET 8) -> char*.
; String temp: 0x4D11D0 (thiscall &tmp, char*, RET 4), buffer freed with 0x5B4C00 (cdecl).
; List: new(0x10) 0x5C1CB4 (cdecl); insert 0x407B30 (thiscall list, pos=[list+8], n, &tmp, RET 0xC).

; --- MODES: JMP from 0x479FC0 in list builder 0x479BB0 (EBP = ModeList being built) -------------
; Appends GHOST (text 0x3E:1) to ModeList and publishes GhostList (0x3F:0..2), then replays
; the two overwritten instructions and returns to 0x479FC9.
modes_lbl:
PUSHAD
SUB ESP,0x8
MOV EBX,EBP
PUSH 0x1
PUSH 0x3e
CALL append_lbl
PUSH 0x10
CALL 0x005c1cb4
ADD ESP,0x4
TEST EAX,EAX
JZ modes_out_lbl
MOV EBX,EAX
XOR ECX,ECX
MOV dword ptr [EBX],ECX
MOV dword ptr [EBX + 0x4],ECX
MOV dword ptr [EBX + 0x8],ECX
MOV dword ptr [EBX + 0xc],ECX
PUSH 0x0
PUSH 0x3f
CALL append_lbl
PUSH 0x1
PUSH 0x3f
CALL append_lbl
PUSH 0x2
PUSH 0x3f
CALL append_lbl
PUSH 0x68e800
LEA ECX,[ESP + 0x4]
CALL 0x004d0580
PUSH EBX
LEA EAX,[ESP + 0x4]
PUSH EAX
CALL 0x004d8ec0
MOV ECX,EAX
CALL 0x004d8880
modes_out_lbl:
ADD ESP,0x8
POPAD
LEA ECX,[ESP + 0x14]
PUSH 0x6b68a8
JMP 0x00479fc9

; --- append(group, index): stdcall, list in EBX ------------------------------------------------
append_lbl:
SUB ESP,0x4
CALL 0x00485cf0
MOV EDX,dword ptr [EAX]
PUSH dword ptr [ESP + 0xc]
PUSH dword ptr [ESP + 0xc]
MOV ECX,EAX
CALL dword ptr [EDX + 0xc]
PUSH EAX
LEA ECX,[ESP + 0x4]
CALL 0x004d11d0
LEA ECX,[ESP]
PUSH ECX
PUSH 0x1
PUSH dword ptr [EBX + 0x8]
MOV ECX,EBX
CALL 0x00407b30
PUSH dword ptr [ESP]
CALL 0x005b4c00
ADD ESP,0x8
RET 0x8

; --- INIT: CALL from 0x47A560 (init 0x47A540, replaces CALL 0x4AE090 = QuickRace mode getter) ---
; QuickRace mode 1 + GhostMode set -> report 4 so the menu reopens on GHOST (Mode = 4 - 1).
init_lbl:
CALL 0x004ae090
CMP EAX,0x1
JNZ init_ret_lbl
SUB ESP,0x4
PUSH 0x68e850
LEA ECX,[ESP + 0x4]
CALL 0x004d0580
LEA EAX,[ESP]
PUSH EAX
CALL 0x004d8ec0
MOV ECX,EAX
CALL 0x004d6760
ADD ESP,0x4
TEST EAX,EAX
MOV EAX,0x1
JZ init_ret_lbl
MOV EAX,0x4
init_ret_lbl:
RET

; --- ACCEPT: CALL from 0x47A8EE (accept 0x47A8C0, replaces CALL 0x4AE060 = QuickRace mode setter)
; Mode 3 (GHOST) -> QuickRace mode 1, GhostMode = 1, Frontend/QuickRace/Ghost = QuickModeSelect/Ghost.
; Other modes -> GhostMode = 0. Tail-jumps to the original setter.
accept_lbl:
PUSH ECX
PUSH EBX
SUB ESP,0x4
XOR EBX,EBX
CMP dword ptr [ESP + 0x10],0x4
JNZ accept_flag_lbl
MOV dword ptr [ESP + 0x10],0x1
INC EBX
PUSH 0x68e830
LEA ECX,[ESP + 0x4]
CALL 0x004d0580
LEA EAX,[ESP]
PUSH EAX
CALL 0x004d8ec0
MOV ECX,EAX
CALL 0x004d6760
PUSH EAX
PUSH 0x6e58b4
LEA ECX,[ESP + 0x8]
CALL 0x004d0580
LEA EAX,[ESP + 0x4]
PUSH EAX
CALL 0x004d8ec0
MOV ECX,EAX
CALL 0x004d8000
accept_flag_lbl:
PUSH 0x68e850
LEA ECX,[ESP + 0x4]
CALL 0x004d0580
PUSH EBX
LEA EAX,[ESP + 0x4]
PUSH EAX
CALL 0x004d8ec0
MOV ECX,EAX
CALL 0x004d8000
ADD ESP,0x4
POP EBX
POP ECX
JMP 0x004ae060

; --- START: CALL from 0x47B871 (Quick Race setup 0x47B780, replaces CALL 0x4AE0F0 = ghost type) --
; Race/GhostPlayback = Race/Car0/RecordSpline = (GhostMode != 0), then tail-jumps to the getter.
start_lbl:
PUSH ECX
PUSH EBX
SUB ESP,0x4
PUSH 0x68e850
LEA ECX,[ESP + 0x4]
CALL 0x004d0580
LEA EAX,[ESP]
PUSH EAX
CALL 0x004d8ec0
MOV ECX,EAX
CALL 0x004d6760
XOR EBX,EBX
TEST EAX,EAX
SETNZ BL
PUSH 0x6b1dd4
LEA ECX,[ESP + 0x4]
CALL 0x004d0580
PUSH EBX
LEA EAX,[ESP + 0x4]
PUSH EAX
CALL 0x004d8ec0
MOV ECX,EAX
CALL 0x004d7aa0
PUSH 0x6b1dbc
LEA ECX,[ESP + 0x4]
CALL 0x004d0580
PUSH EBX
LEA EAX,[ESP + 0x4]
PUSH EAX
CALL 0x004d8ec0
MOV ECX,EAX
CALL 0x004d7aa0
ADD ESP,0x4
POP EBX
POP ECX
JMP 0x004ae0f0
