# R-DEMO2.6 — exact 8.4.1 hull structure and function map

All addresses refer to `demo-8.4.1/MRallye.exe`, SHA256 `bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be`. Recovered from this exact binary; names are semantic labels, not original symbols. Raw decompilation/disassembly remains ignored under `.research-output/r-demo2/exact-841-static/`.

## Function map

| VA / range | Semantic label | Instruction-level basis and xrefs | Status |
|---|---|---|---|
| `005BA290` | pairwise face intersection/edge construction | walks hull state `+0x24` faces in `0x40` strides, builds `0x80` objects at `+0x34`, appends each to both faces via `005C42D0` | CONFIRMED_BY_EXE for data flow; geometric naming INFERRED |
| `005BA6B0` | assign two edge endpoints | walks `+0x34` objects in `0x80` strides, uses `005C3960` match or `005BA930` nearest selection, calls `005C3100` twice per object | CONFIRMED_BY_EXE |
| `005BA930` | nearest vertex-object pointer | searches `+0x44` array in `0x20` strides by squared Euclidean distance and returns address of chosen object | CONFIRMED_BY_EXE |
| `005BABC0` | process all faces | walks `+0x24` face array, calls `005C4350` at `005BABF1` | CONFIRMED_BY_EXE |
| `005C28A0` | `0x80`-byte edge-object initializer | installs sentinel at edge `+0x64`, count 0 at `+0x68`; another list at `+0x70` | CONFIRMED_BY_EXE |
| `005C3100` | append endpoint pointer | writes stack pointer argument into new `0x0c` node `+8`, linked from edge `+0x64`; increments edge `+0x68` | CONFIRMED_BY_EXE |
| `005C3200–005C3238` | two-edge endpoint-overlap predicate | reads two payloads from each edge `+0x64` list; compares four endpoint-pointer pairs; sets `AL` 1/0; only identified xref is `005C4457` | CONFIRMED_BY_EXE |
| `005C3A40` | face/plane initializer | initializes `0x40` face, sentinel at `+0x28`, count at `+0x2c`; derives double-precision normal/plane data from three points | CONFIRMED_BY_EXE for fields; exact plane semantics partly INFERRED |
| `005C42D0` | append edge pointer to face | writes passed `0x80`-object pointer into a new face-list node `+8` at `005C430D`; increments `+0x2c`; xrefs `005BA37D`, `005BA38A` | CONFIRMED_BY_EXE |
| `005C4350` | per-face processing wrapper | calls `005C43A0` then `005C4530`; xref `005BABF1` | CONFIRMED_BY_EXE |
| `005C43A0–005C4528` | reorder face edges by shared endpoint | moves first face edge into local list; searches next connected edge; inserts selected pointer or zero | CONFIRMED_BY_EXE for control flow; algorithm label INFERRED |
| `005BC430` | allocate circular-list sentinel | allocates `0x0c`; initializes `+0/+4` to itself when no neighbors passed; does not initialize `+8` | CONFIRMED_BY_EXE |
| `005BC490` | insert local list node | allocates `0x0c`, rewires neighbors, copies pointed-to value to node `+8` at `005BC4D0`, increments list count | CONFIRMED_BY_EXE |
| `005C4C70` | erase face-list node | rewires both neighbors and decrements count | CONFIRMED_BY_EXE |

## Structure map

| Object / field | Observed use | Narrowest justified meaning | Evidence |
|---|---|---|---|
| Hull state `+0x24/+0x28` | begin/end addresses, difference shifted 6 | `0x40`-stride face-object vector | `005BABC0`, `005BA290` |
| Hull state `+0x34/+0x38` | begin/end, difference shifted 7 | `0x80`-stride edge/intersection-object vector | `005BA290`, `005BA6B0` |
| Hull state `+0x44/+0x48` | begin/end, difference shifted 5 | `0x20`-stride vertex-object vector | `005BA6B0`, `005BA930` |
| Face `+0x28` | pointer to circular-list sentinel | face edge-pointer list head | `005C3A75`, `005C42D5`, `005C43BC` |
| Face `+0x2c` | increment/decrement/test | count of face edge pointers | `005C430F–005C4315`, `005C4430`, `005C44E0` |
| Edge `+0x64` | points to circular-list sentinel | two endpoint vertex-object pointers | `005C2990`, `005C3105`, `005C3200` |
| Edge `+0x68` | increment after endpoint insert | endpoint count | `005C3141–005C3145` |
| Edge `+0x70/+0x74` | initialized as another list/count | another relation list; role unresolved | `005C29AC–005C29AF` |
| `0x0c` list node `+0/+4` | linked forward/back; head self-links | next/previous list-node pointers | `005BC430`, `005BC490`, `005C42D0` |
| `0x0c` list node `+8` | set from supplied pointer at `005C42D0`, `005C3100`, or `005BC490` | payload pointer: edge in face/local lists, vertex in edge endpoint list | `005C430D`, `005C313D`, `005BC4D0` |

The user's captured `16495D28` node has `+0=16495B48`, `+4=16495788` and `+8=0`. Its previous pointer is the captured local head `16495788`; it is an **inserted node**, not an uninitialized sentinel. This aligns with `005BC490` writing the literal-zero local variable into payload `+8`.

## Critical control flow

```asm
005C4441 MOV EBX,[ECX+8]        ; current local-list edge pointer
005C4451 MOV EDI,[EAX+8]        ; candidate face-list edge pointer
005C4454 PUSH EBX
005C4457 CALL 005C3200          ; any shared endpoint?
005C445C TEST AL,AL
005C445E JNZ 005C447D           ; yes: keep EDI
...                                ; try remaining face-list nodes
005C447B XOR EDI,EDI            ; exhausted: choose NULL
005C4481 MOV [ESP+1C],EDI
005C4496 CALL 005BC490          ; insert selected pointer at local node +8
005C44E5 JNZ 005C443B           ; if face list still nonempty, repeat
005C3212 MOV EDX,[EAX+64]       ; crashes when argument EAX==0
```

A sentinel's own `+8` has no initialized payload in `005BC430`, but the runtime chain points to the **first inserted node**, and the no-match branch supplies a literal zero. Do not interpret this as an STL implementation fingerprint or infer a missing constructor initialization as the crash cause.
