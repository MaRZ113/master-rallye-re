; GHOST1 G3/G4 code cave (retail MRallye.exe bf8aef32...), assembled at 0x70020390 by tools/ghidra/AsmCave.java.
; G3: native GHOST mode in the Quick Race mode select. G4: 5 difficulty levels, MRallyeExtras.ini [Ghost]
; options, Alpha-model fallback. Strings are written by tools/ghost1_build.py (MENU_STRINGS):
;   0x70020c00 "Frontend/QuickModeSelect/GhostList"   0x70020c30 "Frontend/QuickModeSelect/Ghost"
;   0x70020c50 "Frontend/QuickRace/GhostMode"         0x70020c70 "VERY EASY"   0x70020c80 "EXTREME"
;   0x70020c90 "kernel32.dll"   0x70020ca0 "GetPrivateProfileIntA"   0x70021100 ".\MRallyeExtras.ini"
;   0x70020ce0 "Ghost"   0x70020cf0 "WithOpponents"   0x70020d00 "RecordAllModes"   0x70020d10 "UseAlphaModel"
;   0x70020d20 "DataGx\Vehicles\%sAlpha\car.dx"   0x70020d40 "DataGx\Vehicles\%sAlpha\wheel.dx"
;   0x70020d70 "Vehicles/%s/car"   0x70020d80 "Vehicles/%s/wheel"
; All branches must assemble short; AsmCave rejects 0x66/0x67-prefixed encodings.
; Broker ABI: 0x4d0580 key ctor (thiscall &slot, char*, RET 4); 0x4d8ec0 -> Broker (no args);
; setters on Broker (args &key,value, RET 8): int 0x4d8000, bool 0x4d7aa0, list 0x4d8880;
; int getter 0x4d6760 (thiscall Broker, &key, RET 4).
; Text table: CALL 0x485cf0 -> obj; CALL [[obj]+0xc] (thiscall obj, group, index, RET 8) -> char*.
; String temp: 0x4d11d0 (thiscall &tmp, char*, RET 4), buffer freed with 0x5b4c00 (cdecl).
; List: new(0x10) 0x5c1cb4 (cdecl); insert 0x407b30 (thiscall list, pos, n, &tmp, RET 0xc).
; IAT: GetModuleHandleA [0x68f238], GetProcAddress [0x68f0c0], GetFileAttributesA [0x68f100].

; --- MODES: JMP from 0x479fc0 in list builder 0x479bb0 ---------------------------------------
; EBP = ModeList, EDI = RaceDifficultyList (both not yet published).
modes_lbl:
PUSHAD
SUB ESP,0x8
MOV EBX,EBP
PUSH 0x1
PUSH 0x3e
CALL append_lbl
MOV EBX,EDI
PUSH 0x1
PUSH 0x70020c70
CALL insert_lbl
PUSH 0x0
PUSH 0x70020c80
CALL insert_lbl
PUSH 0x10
CALL 0x5c1cb4
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
PUSH 0x70020c00
LEA ECX,[ESP + 0x4]
CALL 0x4d0580
PUSH EBX
LEA EAX,[ESP + 0x4]
PUSH EAX
CALL 0x4d8ec0
MOV ECX,EAX
CALL 0x4d8880
modes_out_lbl:
ADD ESP,0x8
POPAD
LEA ECX,[ESP + 0x14]
PUSH 0x6b68a8
JMP 0x479fc9

; --- append(group, index): stdcall, list in EBX ------------------------------------------------
append_lbl:
SUB ESP,0x4
CALL 0x485cf0
MOV EDX,dword ptr [EAX]
PUSH dword ptr [ESP + 0xc]
PUSH dword ptr [ESP + 0xc]
MOV ECX,EAX
CALL dword ptr [EDX + 0xc]
PUSH EAX
LEA ECX,[ESP + 0x4]
CALL 0x4d11d0
LEA ECX,[ESP]
PUSH ECX
PUSH 0x1
PUSH dword ptr [EBX + 0x8]
MOV ECX,EBX
CALL 0x407b30
PUSH dword ptr [ESP]
CALL 0x5b4c00
ADD ESP,0x8
RET 0x8

; --- insert(char*, front): stdcall, list in EBX; front != 0 inserts at the beginning -----------
insert_lbl:
SUB ESP,0x4
PUSH dword ptr [ESP + 0x8]
LEA ECX,[ESP + 0x4]
CALL 0x4d11d0
MOV EAX,dword ptr [EBX + 0x8]
CMP dword ptr [ESP + 0xc],0x0
JZ insert_pos_lbl
MOV EAX,dword ptr [EBX + 0x4]
insert_pos_lbl:
LEA ECX,[ESP]
PUSH ECX
PUSH 0x1
PUSH EAX
MOV ECX,EBX
CALL 0x407b30
PUSH dword ptr [ESP]
CALL 0x5b4c00
ADD ESP,0x8
RET 0x8

; --- ini(key, default): stdcall -> GetPrivateProfileIntA("Ghost", key, default, ".\MRallyeExtras.ini")
ini_lbl:
PUSH 0x70020c90
CALL dword ptr [0x68f238]
TEST EAX,EAX
JZ ini_default_lbl
PUSH 0x70020ca0
PUSH EAX
CALL dword ptr [0x68f0c0]
TEST EAX,EAX
JZ ini_default_lbl
PUSH 0x70021100
PUSH dword ptr [ESP + 0xc]
PUSH dword ptr [ESP + 0xc]
PUSH 0x70020ce0
CALL EAX
RET 0x8
ini_default_lbl:
MOV EAX,dword ptr [ESP + 0x8]
RET 0x8

; --- DIFFTEXT(level): stdcall from 0x47b70d, Quick Race summary difficulty text for ICont level 0..4
diff_lbl:
MOV EAX,dword ptr [ESP + 0x4]
TEST EAX,EAX
JNZ diff_hi_lbl
MOV EAX,0x70020c70
RET 0x4
diff_hi_lbl:
CMP EAX,0x4
JL diff_mid_lbl
MOV EAX,0x70020c80
RET 0x4
diff_mid_lbl:
DEC EAX
PUSH EAX
CALL 0x485cf0
MOV EDX,dword ptr [EAX]
PUSH 0x41
MOV ECX,EAX
CALL dword ptr [EDX + 0xc]
RET 0x4

; --- FMT: CALL from 0x4bfe9c / 0x4bfeee (sprintf of Vehicles/%sAlpha/car|wheel in 0x4bfe00) ----
; cdecl (buf, fmt, name). Uses the plain model when UseAlphaModel=0 or the loose Alpha DX is missing.
fmt_lbl:
PUSH EBX
PUSH ESI
PUSH EDI
SUB ESP,0x100
MOV ESI,dword ptr [ESP + 0x114]
MOV EBX,0x70020d20
MOV EDI,0x70020d70
CMP ESI,0x6e6ee8
JZ fmt_check_lbl
MOV EBX,0x70020d40
MOV EDI,0x70020d80
fmt_check_lbl:
PUSH 0x1
PUSH 0x70020d10
CALL ini_lbl
TEST EAX,EAX
JZ fmt_plain_lbl
PUSH dword ptr [ESP + 0x118]
PUSH EBX
LEA EAX,[ESP + 0x8]
PUSH EAX
CALL 0x5c20ba
ADD ESP,0xc
LEA EAX,[ESP]
PUSH EAX
CALL dword ptr [0x68f100]
CMP EAX,-0x1
JNZ fmt_keep_lbl
fmt_plain_lbl:
MOV dword ptr [ESP + 0x114],EDI
fmt_keep_lbl:
ADD ESP,0x100
POP EDI
POP ESI
POP EBX
JMP 0x5c20ba

; --- INIT: CALL from 0x47a560 (init 0x47a540, replaces CALL 0x4ae090 = QuickRace mode getter) ---
init_lbl:
CALL 0x4ae090
CMP EAX,0x1
JNZ init_ret_lbl
SUB ESP,0x4
PUSH 0x70020c50
LEA ECX,[ESP + 0x4]
CALL 0x4d0580
LEA EAX,[ESP]
PUSH EAX
CALL 0x4d8ec0
MOV ECX,EAX
CALL 0x4d6760
ADD ESP,0x4
TEST EAX,EAX
MOV EAX,0x1
JZ init_ret_lbl
MOV EAX,0x4
init_ret_lbl:
RET

; --- ACCEPT: CALL from 0x47a8ee (accept 0x47a8c0, replaces CALL 0x4ae060 = QuickRace mode setter)
accept_lbl:
PUSH ECX
PUSH EBX
SUB ESP,0x4
XOR EBX,EBX
CMP dword ptr [ESP + 0x10],0x4
JNZ accept_flag_lbl
MOV dword ptr [ESP + 0x10],0x1
INC EBX
PUSH 0x70020c30
LEA ECX,[ESP + 0x4]
CALL 0x4d0580
LEA EAX,[ESP]
PUSH EAX
CALL 0x4d8ec0
MOV ECX,EAX
CALL 0x4d6760
PUSH EAX
PUSH 0x6e58b4
LEA ECX,[ESP + 0x8]
CALL 0x4d0580
LEA EAX,[ESP + 0x4]
PUSH EAX
CALL 0x4d8ec0
MOV ECX,EAX
CALL 0x4d8000
accept_flag_lbl:
PUSH 0x70020c50
LEA ECX,[ESP + 0x4]
CALL 0x4d0580
PUSH EBX
LEA EAX,[ESP + 0x4]
PUSH EAX
CALL 0x4d8ec0
MOV ECX,EAX
CALL 0x4d8000
ADD ESP,0x4
POP EBX
POP ECX
JMP 0x4ae060

; --- START: CALL from 0x47b871 (Quick Race setup 0x47b780, replaces CALL 0x4ae0f0 = ghost type) --
; playback = GhostMode || (WithOpponents && QuickRace mode == 2 RACE)
; record   = playback || RecordAllModes
start_lbl:
PUSH ECX
PUSH EBX
PUSH ESI
SUB ESP,0x4
PUSH 0x70020c50
LEA ECX,[ESP + 0x4]
CALL 0x4d0580
LEA EAX,[ESP]
PUSH EAX
CALL 0x4d8ec0
MOV ECX,EAX
CALL 0x4d6760
XOR EBX,EBX
TEST EAX,EAX
SETNZ BL
JNZ start_rec_lbl
CALL 0x4ae700
MOV ECX,EAX
CALL 0x4ae090
CMP EAX,0x2
JNZ start_rec_lbl
PUSH 0x0
PUSH 0x70020cf0
CALL ini_lbl
TEST EAX,EAX
SETNZ BL
start_rec_lbl:
MOV ESI,EBX
TEST ESI,ESI
JNZ start_set_lbl
PUSH 0x0
PUSH 0x70020d00
CALL ini_lbl
TEST EAX,EAX
SETNZ BL
MOV ESI,EBX
XOR EBX,EBX
start_set_lbl:
PUSH 0x6b1dd4
LEA ECX,[ESP + 0x4]
CALL 0x4d0580
PUSH EBX
LEA EAX,[ESP + 0x4]
PUSH EAX
CALL 0x4d8ec0
MOV ECX,EAX
CALL 0x4d7aa0
PUSH 0x6b1dbc
LEA ECX,[ESP + 0x4]
CALL 0x4d0580
PUSH ESI
LEA EAX,[ESP + 0x4]
PUSH EAX
CALL 0x4d8ec0
MOV ECX,EAX
CALL 0x4d7aa0
ADD ESP,0x4
POP ESI
POP EBX
POP ECX
JMP 0x4ae0f0

; --- G4.1 FOCUS: CALL from 0x47a3ce (update 0x47a120, replaces CALL 0x525800 = focused button) ----
; Sets the GHOST TYPE row arrows (Left/RightArrowGhost = mode 3 && ghost > 0 / < 2) and maps
; focus 10 (GHOST mode row) -> 1 and 11 (GHOST TYPE row) -> 3 for the Arrow1/Arrow2 highlight switch.
; Strings: 0x70020da0 "Frontend/QuickModeSelect/LeftArrowGhost", 0x70020dd0 "...RightArrowGhost".
focus_lbl:
CALL 0x525800
PUSH EBX
PUSH ESI
PUSH EAX
SUB ESP,0x4
PUSH 0x6b6ae8
LEA ECX,[ESP + 0x4]
CALL 0x4d0580
LEA EAX,[ESP]
PUSH EAX
CALL 0x4d8ec0
MOV ECX,EAX
CALL 0x4d6760
XOR EBX,EBX
CMP EAX,0x3
SETZ BL
PUSH 0x70020c30
LEA ECX,[ESP + 0x4]
CALL 0x4d0580
LEA EAX,[ESP]
PUSH EAX
CALL 0x4d8ec0
MOV ECX,EAX
CALL 0x4d6760
MOV ESI,EAX
XOR EAX,EAX
TEST ESI,ESI
SETG AL
AND EAX,EBX
PUSH EAX
PUSH 0x70020da0
LEA ECX,[ESP + 0x8]
CALL 0x4d0580
LEA EAX,[ESP + 0x4]
PUSH EAX
CALL 0x4d8ec0
MOV ECX,EAX
CALL 0x4d8000
XOR EAX,EAX
CMP ESI,0x2
SETL AL
AND EAX,EBX
PUSH EAX
PUSH 0x70020dd0
LEA ECX,[ESP + 0x8]
CALL 0x4d0580
LEA EAX,[ESP + 0x4]
PUSH EAX
CALL 0x4d8ec0
MOV ECX,EAX
CALL 0x4d8000
ADD ESP,0x4
POP EAX
CMP EAX,0xa
JNZ focus_11_lbl
MOV EAX,0x1
focus_11_lbl:
CMP EAX,0xb
JNZ focus_ret_lbl
MOV EAX,0x3
focus_ret_lbl:
POP ESI
POP EBX
RET

; --- G4.1 INITSHOW: CALL from 0x47a152 (first update: hide panel groups; retail hid 2..4) -------
initshow_lbl:
PUSH 0x1
PUSH 0x0
PUSH 0x4
CALL 0x4f6310
MOV ECX,EAX
CALL 0x4f6070
PUSH 0x1
PUSH 0x0
PUSH 0x5
CALL 0x4f6310
MOV ECX,EAX
CALL 0x4f6070
RET

; --- G4.1 EXITHIDE: CALL from 0x47a0e1 (leaving the screen: retail hid groups 2..4) --------------
exithide_lbl:
PUSH 0x4
CALL 0x4f6310
MOV ECX,EAX
CALL 0x4f6030
PUSH 0x5
CALL 0x4f6310
MOV ECX,EAX
CALL 0x4f6030
RET

; --- G4.2 MODEIDX: CALL from 0x47b3cf (Quick Race summary 0x47b040, mode 1 branch) ----------------
; Returns EAX = text table, EDX = its vtable, ECX = mode text index (1 GHOST if GhostMode, else 0 PRACTICE);
; the patched caller then does PUSH ECX; JMP 0x47b3e4 (PUSH 0x3e; CALL [EDX+0xc]).
modeidx_lbl:
PUSH EBX
SUB ESP,0x4
PUSH 0x70020c50
LEA ECX,[ESP + 0x4]
CALL 0x4d0580
LEA EAX,[ESP]
PUSH EAX
CALL 0x4d8ec0
MOV ECX,EAX
CALL 0x4d6760
XOR EBX,EBX
TEST EAX,EAX
SETNZ BL
ADD ESP,0x4
CALL 0x485cf0
MOV EDX,dword ptr [EAX]
MOV ECX,EBX
POP EBX
RET

; --- G4.2 GTYPE: CALL from 0x47b43d (replaces PUSH 0x6f5900 = "" for Frontend/QuickRace/GhostTypeString)
; Leaves the string pointer on the stack in place of the return address (net effect = PUSH imm32):
; GhostMode ? "GHOST TYPE - <type>" (sprintf "%s%s%s" at 0x70020e00 of text 28:2, " - " 0x6b579c,
; text(0x3f, Frontend/QuickRace/Ghost)) into the writable buffer 0x70021c00 (.data padding, VirtualSize
; raised to 0x5f000 by the builder) : "".
gtype_lbl:
PUSH ECX
PUSH EDX
SUB ESP,0x4
PUSH 0x70020c50
LEA ECX,[ESP + 0x4]
CALL 0x4d0580
LEA EAX,[ESP]
PUSH EAX
CALL 0x4d8ec0
MOV ECX,EAX
CALL 0x4d6760
TEST EAX,EAX
MOV EAX,0x6f5900
JZ gtype_done_lbl
PUSH 0x6e58b4
LEA ECX,[ESP + 0x4]
CALL 0x4d0580
LEA EAX,[ESP]
PUSH EAX
CALL 0x4d8ec0
MOV ECX,EAX
CALL 0x4d6760
PUSH EAX
CALL 0x485cf0
MOV EDX,dword ptr [EAX]
PUSH 0x3f
MOV ECX,EAX
CALL dword ptr [EDX + 0xc]
PUSH EAX
PUSH 0x6b579c
PUSH 0x2
CALL 0x485cf0
MOV EDX,dword ptr [EAX]
PUSH 0x1c
MOV ECX,EAX
CALL dword ptr [EDX + 0xc]
PUSH EAX
PUSH 0x70020e00
PUSH 0x70021c00
CALL 0x5c20ba
ADD ESP,0x14
MOV EAX,0x70021c00
gtype_done_lbl:
ADD ESP,0x4
POP EDX
POP ECX
XCHG dword ptr [ESP],EAX
JMP EAX
