# G1 duplicate-selection correction

## Evidence boundary

**Current G1 outcome:** `CONFIRMED_BY_RUNTIME / CLOSED`. The owner supplied a
completed eight-participant T2 race and Broker result: Car3 and Car7 both used
physical ID8, kept separate DriverIDs 6 and 5, all eight entries finished,
and the game displayed eight separate results. The exact candidate SHA and raw
capture files are not present locally, so these values remain owner-provided
runtime evidence rather than a locally revalidated capture bundle. This closes
repeated-ID participant/materialization safety for the reported T2 scenario.
It does not provide a faulting EIP for the earlier crash report or qualify
every class/course/count combination.

The supported image is pristine retail `MRallye.exe`, SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
The owner reported that seven-AI T1/T2 Quick Races can crash with a same-class
player, while an outside-class control and observed T3 cases did not show the
same symptom. Six AI avoids the reported boundary. No exception record with
the faulting EIP, parameters, registers, or stack is available. The first
failing instruction in that earlier report remains **unproven**; the later
successful T2 duplicate-ID race is not an exception trace.

## Static native path

The current F3 Quick Race selector filters the eligible source pool against
prior participant CarIDs. Under strict T1 or T2 selection, a same-class player
leaves six alternative stock physical IDs. After six AI choices have used
those alternatives, the next selector call sees no unused physical ID in that
class. The policy core now detects that exhausted unique set before returning
the class decision.

The exact-build Ghidra export identifies the retail physical chooser as
`FUN_00458090`, bytes from `0x00458090` through `0x004584D6`, SHA256
`2daec5f26455c98bfa399308ce8a3030ebe5871dfe4fd13a675526bb97842a71`, with
`RET 0x14`. It calls the vector-length helper `FUN_004116A0` (`0x004116A0`),
which returns zero when the vector begin pointer is null. Its refill/shuffle
helper is `FUN_00450580`, which returns with plain `RET`. The decompilation
shows the chooser selecting the last temporary-vector element after refill;
the available path does not establish a second empty check at that point.
Driver selection is separate in `FUN_00458980` (`RET 4`), and the native
CarID/Class/DriverID setters still publish into the selected CarN.

The relevant retail instruction sequence is:

```text
0045837D  CALL 0x004116A0       ; temporary-pool length
00458382  TEST EAX,EAX
00458384  JNZ  0x004583EB       ; use existing temporary entries
004583A8  CALL 0x00450580       ; refill/shuffle from saved eligible pool
004583B8  CMP  EAX,ECX
004583BE  JNC  0x004583E2       ; skip copy if source range is empty
004583E2  CALL 0x0041FA50       ; clear temporary vector
004583EB  MOV  EAX,[ESP+0x38]
004583F4  MOV  ECX,[EAX-4]       ; select last temporary element
```

This is a hazardous empty-source path in static control flow: if the source
range is empty, refill has no elements to copy, the temporary vector is
cleared, and the code reaches the last-element read. This sequence explains
why the G1 correction targets exhausted source-pool pruning. It is not a
captured runtime exception location; the owner has not supplied a faulting
EIP or stack for the reported crash.

This makes unique-pool exhaustion a concrete static risk consistent with the
observed boundary. The owner-provided later runtime result confirms a T2 race
with duplicate IDs completed through finish and Results. It does not prove
that this path was the earlier crash's cause or qualify replay, cleanup, every
course, or every restricted-class combination.

## G1 behavior

`choose_class()` retains the requested class. While unique eligible IDs
remain, the Quick Race callback returns the ordinary class selector (`0..2`)
and the generated selector keeps pruning prior CarIDs. When `Duplicates=1`
and that class has no unused eligible ID, only the G1 Quick Race build returns
the private marker `0x100 | class_id`. The G1 Quick Race pool-end path then
preserves the human CarID exclusion but stops removing earlier AI CarIDs from
the source pool. The retail chooser's own refill can select a valid member of
the same class again. The repeated CarID remains only an identity value: the
retail loop still constructs and populates a distinct CarN participant and
calls the native DriverID chooser per participant.

The `Duplicates=Never` path stays bounded. Before starting an extended Quick
Race it compares the requested AI count with the number of distinct valid
eligible physical IDs after the human-car exclusion. An impossible roster is
refused only for the applicable Quick Race path. It does not add a global
Start guard, cross-class fallback, or a failure path for Practice,
Checkpoint, Cup, Master Rallye, Invitation, or Challenge.

## Hook and ABI scope

The generated candidate preserves the exact 17-operation F3 ownership set.
Only these three Quick Race selector operations differ: initialization at
`0x0045810B`, loop at `0x00458379`, and pool end at `0x004582D5`. The G1
selector remains inside its allocated `0x300`-byte interval and does not
replace the retail chooser entry or overlap the chooser's later refill and
publication code.

The emitted-byte test checks the private class marker, relative branch
destinations, `PUSHFD`-adjusted marker address, unique-selection bound, repeat
bound, and `CMP EDI,ESI` loop termination against the actual generated bytes.
The selector carries its loop limit in ESI across the native CarID accessor
and vector erase. Exact Ghidra exports show those callees preserve ESI:
`FUN_004AC660` saves/restores ESI and ends in `RET 4`; `FUN_00416620`
likewise restores ESI before `RET 4`. The Quick Race singleton accessor used
by this selector does not touch ESI/EDI. The no-flag selector output is tested
byte-identical to F3, and the F3 runtime DLL is pinned to its preserved SHA.

Static checks establish preimages, boundaries, non-overlap, and ABI facts
visible in the disassembly. The owner-provided G1 runtime result now confirms
that the reported T2 duplicate-ID participant lifecycle completed through
finish and Results. The exact candidate identity was not supplied here, and
the separate post-dump/results crash remains an Observatory safety issue.

