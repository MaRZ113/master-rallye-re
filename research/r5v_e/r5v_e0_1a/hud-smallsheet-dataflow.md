# HUD SmallCarSheet dataflow — retail

## Scene object candidate

`DataScene/Hud/Hud0.xml` contains `Egg Name="TimeDiffs"` at 2D matrix
translation `(20, 380)` and `AI Name="gaHudTimeDiffsAi"` with `Hud No=0`.
`Hud1.xml` has the matching object at `(20, 150)` with `Hud No=1`. Both have
`en2d Model Name="Null"`. The files separately declare progress markers
`ProgressCar0` through `ProgressCar7`; each uses `hud\hud-template`, frame 3.
This separates the TimeDiffs component from the progress-bar marker.

Raw retail assembly for `0x004AAA30` constructs the object and writes the
`gaHudTimeDiffsAi` string at `0x006E5484`. Its vtable pointer is
`0x00691058`; the factory at `0x004AAAF0` allocates `0x9C` bytes. The
constructor zeroes three child pointers at `+0x0C`, `+0x10`, `+0x14`, and the
corresponding selector-state area beginning at `+0x8C`.

## `0x004AAE70` raw instruction path

Ghidra identifies the function start at `0x004AAE70`; `0x004AB18E` is inside
it. It is a thiscall-shaped function with `ECX=this` and three stack
arguments. At entry, assembly loads the first two stack parameters into
`EBX` and `EBP`; `RET 0x0C` cleans the three argument dwords.

| Address | Raw instruction / calculation | Meaning supported by context |
|---|---|---|
| `0x004AAE74` | `MOV EBX,[ESP+0x34]` | Child/display selector argument |
| `0x004AAE79` | `MOV EBP,[ESP+0x3C]` | Participant index argument |
| `0x004AAE81` | `MOV [EDI+EBX*4+0x8C],EBP` | Save participant index for selected child |
| `0x004AAE88`–`0x004AAE8C` | Load `[EDI+EBX*4+0x0C]`, then `+0x4C` | Resolve selected child and embedded image object |
| `0x004AB00F`–`0x004AB017` | `PUSH EBP`; `CALL 0x004ADA50`; `MOV ECX,EAX`; `CALL 0x004AC660` | Resolve race property for the participant index |
| `0x004AB01E` | `CALL 0x0045A3C0` | Obtain vehicle registry object base |
| `0x004AB023`–`0x004AB026` | `LEA ECX,[EDI+EDI*2]`; `LEA EDX,[EDI+ECX*4]` | Calculate participant CarID times `0x34` |
| `0x004AB02B` | `MOV EAX,[EAX+EDX*4+0x20]` | Read registry base + ID*`0x34` + `0x20` |
| `0x004AB02F`–`0x004AB030` | Push value; `CALL 0x004E1FF0` with `ECX=ESI` | Send the value to the embedded image object's selector setter |

The registry's first record begins at object offset `+4`; therefore
`registry_base + ID*0x34 + 0x20` is exactly
`VehicleRecord[ID] + 0x1C`. It does not read the owned string at record
`+0x20`.

`0x004ABCE0` initializes the race path key set and includes `/CarID`; the
helper path reached through `0x004AC660` composes the participant-indexed
`Race/Car%d/CarID` read. The argument register/stack flow above comes from
raw assembly, not decompiler parameter names. The saved live assembly and
bridge P-code are under ignored `.research-output/r5v_e0_1a/bridge/`.

## Normal retail selector inventory

The final registry metadata at `research/r5v_a/final-vehicle-registry.json`
records the numeric initializer arguments in push order for all 25 normal
records. The first argument now maps to the `+0x1C` field through the raw HUD
consumer above. In record-index order those values are
`[9,17,22,15,1,16,20,13,4,7,24,19,14,26,3,25,0,5,11,10,2,27,6,8,28]`.
Thus no normal record selects frames 12, 18, 23 or 29. This confirms frame 29
is dormant in the normal retail registry; its visual Forklift match is strong
leftover-art evidence, not proof that retail ID25 historically used it.

## What is and is not closed

The value path through an image selector is **RAW-GHIDRA-SUPPORTED**. The
association with the `TimeDiffs` AI is **STRONGLY SUPPORTED** by matching
constructor state, child offsets and per-participant path behavior. Two final
links remain unproven statically:

1. Ghidra reports zero direct callers to `0x004AAE70`, and a direct address
   reference was not found in the focused raw scan. The inspected vtable
   rooted at `0x00691058` does not give a direct dispatch edge to this helper.
   A runtime or dynamically composed dispatch may exist, but it has not been
   demonstrated.
2. `TimeDiffs` has a null scene model name. The string
   `4BFrontend/RaceResults/SmallCarSheet` at `0x006E545E` has no direct string
   references in the current export. The exact binding from the helper's
   child image to this named bank remains unknown.

The scene coordinate and function role make `TimeDiffs` the best static
candidate for the owner-reported top-left image beside `1P`; the scene does
not include a literal `1P` label tying that observation to the object. The
`0 -> 29` runtime diagnostic is designed to prove or disprove both remaining
joins without changing the Trooper model or other identity fields.

## Evidence classification

| Claim | Classification | Evidence |
|---|---|---|
| `0x004AAE70` reads `CarID` then record `+0x1C` | BOTH | Raw assembly and Ghidra P-code calculation plus registry layout |
| Value reaches image selector setter `0x004E1FF0` | BOTH | Raw `ECX`/stack setup and call; Ghidra P-code call at `0x004AB030` |
| TimeDiffs is a relevant scene object | BOTH | Scene XML AI name; raw constructor embeds the same AI name and child fields |
| `0x004AAE70` is dispatched at runtime by TimeDiffs | UNRESOLVED | No direct xref or observed vtable entry |
| Its child image uses SmallCarSheet | UNRESOLVED | Null model in scene XML; SmallCarSheet string has no direct xrefs |
| Race Results use the same record field | RAW-GHIDRA-SUPPORTED | Prior E0.1 producer, scene binding and image-selector consumer |
