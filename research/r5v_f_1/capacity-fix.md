# Independent T1/T2 capacity initialization

## Raw retail evidence

The retail executable is SHA-256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Ghidra Bridge disassembled `FUN_00480a20`:

```asm
00480a4a MOV EAX,0x7
00480a4f MOV dword ptr [ESI + 0x20],EAX
00480a52 MOV dword ptr [ESI + 0x24],EAX
```

Ghidra bytes at these VAs match the original retail file bytes. In the old
candidate, changing the immediate at `0x480A4B` from 7 to 8 affected both stores:

```text
T1 capacity [ESI+0x20] = 8
T2 capacity [ESI+0x24] = 8  <- false extra slot
```

## False Bowler chain

The two untouched retail mapping helpers explain the observed alias:

```asm
; FUN_00481e20: class1 / T2 branch
00481e38 MOV EAX,[ECX + 0x18]
00481e3b ADD EAX,0x7
00481e3e RET

; FUN_00481e50: reverse mapping
00481e68 CMP EAX,0xe
00481e7c ADD EAX,-0xe
00481e7f MOV [ESI + 0x10],0x2
00481e86 MOV [ESI + 0x1c],EAX
```

Therefore an exposed `T2 local7` is interpreted as absolute `7+7 = ID14`.
The reverse helper sees ID14, chooses class2/T3 and stores local index
`14-14 = 0`. ID14 is the canonical Bowler Wildcat slot in T3. The false T2
entry is a capacity coupling bug; the mapping is the original retail behavior
and must remain unchanged.

## Cleanup helper

The patch replaces the complete 11-byte original sequence at `0x480A4A` with a
relative jump and six NOP bytes. The helper at `0x68E3E0` emits:

```asm
MOV EAX,0x7                         ; preserve original live EAX
MOV dword ptr [ESI + 0x20],0x8      ; T1 = 8
MOV dword ptr [ESI + 0x24],0x7      ; T2 = 7
JMP 0x480A55                        ; resume before untouched stores
```

The existing T3 count patch remains `11 -> 12` at `0x480A65`. No class mapper,
navigation field or ID is changed.

Regression tests inspect the emitted bytes, decode both destination offsets and
immediates, check the continuation target, and fail if T2's value is anything
other than 7. Candidate disassembly is preserved under ignored
`research-output/r5v_f_1/cleanup/VALIDATION.json`.

## Runtime check

The owner reports cleanup P0 FULL PASS for the same candidate SHA recorded in
`validation.md`: T1 retains eight entries, the false T2 Bowler is gone, and T3
remains intact. The follow-up report does not provide a separate T3 numeric
count observation, so the T3=12 conclusion is supported by the preserved
static configuration and the report that the existing layout remained intact.
