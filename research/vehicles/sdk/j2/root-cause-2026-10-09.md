# R5V-J.2 — ID27 Vehicle Select re-entry root cause

**Status:** native root cause proven by exact-bundle static decoding; the
corrected candidate is `READY_FOR_HUMAN_RUNTIME`. J.2 is not closed.

The stack-ABI hotfix is human-runtime pass: Vehicle Select now opens and ID26
restores. The same candidate still restores ID27 as Navara. The human result
therefore confirms the remaining symptom but is not being used as a substitute
for a same-player, per-constructor Broker trace. The cause below is established
from the actual inherited J.1 native patch bytes and the constructor dataflow.

## First incorrect transition

`FUN_00480B60` (`0x00480B60`) gets the active `PlayerID` from its scene object
at `this+0x2c`. In the Quick Race restoration path, the constructor sets that
player context with `FUN_004AE700`, reads the stored physical vehicle through
`FUN_004ADFB0`, then calls `FUN_00481E50` at `0x00480E5E` with the scene object
in ECX and the stored physical ID on the stack. This is the native
physical-ID-to-class/local restoration boundary.

The J.1 reverse-map branch for ID27 at `0x0068E880` was:

```asm
cmp  dword ptr [esp+4], 27
jne  stock_ID26_fallback
push esi
mov  esi, ecx
mov  dword ptr [esi+0x10], 1   ; class = T2
mov  dword ptr [esi+0x14], 7   ; BUG: T1 local ordinal slot
jmp  0x00481E89
```

The object stores class at `+0x10`, then one local ordinal per class:

| Class | Local ordinal field |
|---|---:|
| T1 (0) | `+0x14` |
| T2 (1) | `+0x18` |
| T3 (2) | `+0x1c` |

This layout is independently visible in the stock reverse mapper: the T2 arm
writes its local ordinal at `+0x18`. The native forward mapper at
`0x0068E860` likewise checks a T2 local ordinal at `+0x18` before returning
physical ID27.

The constructor later indexes the local field as
`this+0x14 + class*4`. Because ID27's bad reverse branch writes `7` to the T1
field while setting class T2, the T2 field remains its initialized value `0`.
The existing J.2 publication stub reads that T2 field, so it faithfully
publishes `T2/local0`; the native T2 forward map then resolves local0 to stock
physical ID7/Navara. The corresponding Vehicle Select state is therefore
reported as CarModel/selectedCar 7 with XValue 0. The original Car0=27 stored
value is not overwritten by this mapper or the XY stub.

## Why ID26 was unaffected

ID26 is T1/local7. Its reverse branch writes T1 local state at `+0x14`, which
is exactly the T1 slot. It continues to restore correctly. Stock ID7 uses the
native T2 arm and stores T2/local0 at `+0x18`; that path is unchanged.

## Corrected intervention

The verified J.1 bundle remains untouched. The J.2 derived composite changes
the displacement byte in the inherited ID27 mapper instruction at
`0x0068E895` from `0x14` to `0x18`, making the operation
`C7 46 18 07` (`MOV dword ptr [ESI+0x18],7`). The physical ID remains 27; the
class remains T2; no Quick Race stored selection, `selectedCar`, unlock state,
or commit state is directly written. The existing 86-byte stack-ABI-correct
constructor publication stub is unchanged.

The 246-row J.1 operation table is preserved in the derived J.2 plan with one
inherited code-cave row corrected; the two J.2 constructor hook/stub rows are
then added, for 248 total operations. This avoids overlapping a separate patch
inside the parent's code-cave range. The source J.1 bundle on disk is still
independently verified at 246 operations.

The emitted candidate verifier decodes the effective reverse/forward mapper
bytes and symbolically executes the scene writes. It requires class 1 at
`+0x10`, local 7 at `+0x18`, and forward resolution back to physical ID27. It
rejects the previous J.1 `+0x14` displacement. Byte-diff tests prove that the
composite changes only this one inherited displacement plus the constructor
hook and stub; the ID26 helper, stock mapper fallback, and existing resource
inventory are unchanged.

## Evidence boundary

This proves the native code defect and the corrected static state transition.
It does not yet prove the corrected candidate's behavior in-game. The latest
human run of the stack-hotfix candidate established crash-free Vehicle Select,
ID26 restoration, and continued ID27-to-Navara restoration; no new Broker
capture at the internal constructor boundaries was supplied. The corrected
candidate requires a fresh-process human test. If it fails, capture one
same-player before/after pair for `PlayerID`, QuickRace Car0/Car1, CarModel,
selectedCar, YValue and XValue and stop before adding further patches.

Candidate and test details are in
[`root-cause/human-retest.md`](root-cause/human-retest.md) and
[`root-cause/validation.md`](root-cause/validation.md).
# Historical static diagnosis; final runtime status is superseded by
# [J.2 closeout](closeout-2026-10-09.md). The owner later confirmed the exact
# corrected candidate in human runtime; no new Broker capture was supplied.
