; GHOST1 G1.2: restore Race/Ghost/Progress (demo 9.3.1 gaRaceLineAI 0x46D890 behaviour).
; Entered by CALL from 0x4BFDE8 (was CALL 0x4D8AE0, Broker vector setter for Race/Ghost/Position).
; Entry: ECX = Broker, [esp+4] = &key(Race/Ghost/Position), [esp+8] = &ghost position (x,y,z float).
; Progress = index of the nearest RaceLine point (0x48-byte records, position at +0x38) / (count - 1).
; All branches must assemble short (a 66-prefixed rel16 Jcc would truncate EIP).
; Labels must end with "_lbl" so the assembler pass can substitute them.
PUSH EBX
PUSH ESI
PUSH EDI
PUSH EBP
MOV ESI,dword ptr [ESP + 0x18]
PUSH ESI
PUSH dword ptr [ESP + 0x18]
CALL 0x004d8ae0
SUB ESP,0x8
PUSH 0x6af65c
LEA ECX,[ESP + 0x4]
CALL 0x004d0580
LEA EAX,[ESP]
PUSH EAX
CALL 0x004e51c0
MOV ECX,EAX
CALL 0x004e4d20
TEST EAX,EAX
JZ early_lbl
MOV EDI,dword ptr [EAX + 0x4]
MOV ECX,dword ptr [EAX + 0x8]
TEST EDI,EDI
JZ early_lbl
MOV EAX,ECX
SUB EAX,EDI
CDQ
MOV EBX,0x48
IDIV EBX
MOV EBX,EAX
CMP EBX,0x2
JGE go_lbl
early_lbl:
ADD ESP,0x8
POP EBP
POP EDI
POP ESI
POP EBX
RET 0x8
go_lbl:
MOV dword ptr [ESP + 0x4],0x7f7fffff
XOR ECX,ECX
OR EBP,0xffffffff
LEA EDX,[EDI + 0x38]
scan_lbl:
FLD float ptr [EDX]
FSUB float ptr [ESI]
FMUL ST0
FLD float ptr [EDX + 0x4]
FSUB float ptr [ESI + 0x4]
FMUL ST0
FADDP
FLD float ptr [EDX + 0x8]
FSUB float ptr [ESI + 0x8]
FMUL ST0
FADDP
FCOM float ptr [ESP + 0x4]
FNSTSW AX
SAHF
JNC skip_lbl
FST float ptr [ESP + 0x4]
MOV EBP,ECX
skip_lbl:
FSTP ST0
INC ECX
ADD EDX,0x48
CMP ECX,EBX
JL scan_lbl
TEST EBP,EBP
JS done_lbl
MOV dword ptr [ESP + 0x4],EBP
FILD dword ptr [ESP + 0x4]
DEC EBX
MOV dword ptr [ESP + 0x4],EBX
FIDIV dword ptr [ESP + 0x4]
FSTP float ptr [ESP + 0x4]
PUSH 0x6e51bc
LEA ECX,[ESP + 0x4]
CALL 0x004d0580
PUSH dword ptr [ESP + 0x4]
LEA EAX,[ESP + 0x4]
PUSH EAX
CALL 0x004d8ec0
MOV ECX,EAX
CALL 0x004d7ed0
done_lbl:
ADD ESP,0x8
POP EBP
POP EDI
POP ESI
POP EBX
RET 0x8
