# Native Broker Dump — nullable payload guards

**KNOWN STOCK NATIVE DEVELOPER-TOOL BUG**, reproduced by the user on pristine
stock and mixed-class builds after ordinary Race Results. It is not evidence
of mixed-class actor instability. Native walker `0x601D00..0x602297` prints
entries at stride `0x1C`: path handle+0, payload pointer+4, type+8, flags+C,
revision+10, scope+14, SaveFile handle+18. Diagnostic storage is not an actor.

## Bounded handler audit (CONFIRMED_BY_EXE)

All type0..11 payloads are pointer-backed. NULL here means the **payload object
pointer**, not a zero interned-string handle inside a valid wrapper. A reachable
NULL state is established for StringList and for the XmlData getter contract.

| Type ID / label | Branch | Payload / dereference | Classification | Legitimate NULL established? |
|---|---|---|---|---|
| 0 Bool | 601E70 | node+4 -> byte deref601E77 | NULL_UNSAFE | UNKNOWN |
| 1 Float | 601EA1 | node+4 -> FLD601EAE | NULL_UNSAFE | UNKNOWN |
| 2 Int | 601ECB | node+4 -> MOV601ED3 | NULL_UNSAFE | UNKNOWN |
| 3 Matrix | 601EF0 | 4DDAE0 -> floats601F2B onward | NULL_UNSAFE | UNKNOWN |
| 4 String | 601FC6 | 4DDB30 -> wrapper -> 4D0570 reads[ECX] | NULL_UNSAFE | UNKNOWN for NULL wrapper |
| 5 nuVector4 | 602062 | 4DE9E0 -> floats60206E onward | NULL_UNSAFE | UNKNOWN |
| 6 nuVector3 | 6020AB | 4DE990 -> floats6020B7 onward | NULL_UNSAFE | UNKNOWN |
| 7 nuVector2 | 6020EB | 4DE940 -> floats6020F7 onward | NULL_UNSAFE | UNKNOWN |
| 8 MarkerListName | 601F6A | 4DE8E0 -> wrapper -> 4D0570 | NULL_UNSAFE | UNKNOWN for NULL wrapper |
| 9 StringList | 601FF4 | node+4 at601FF9 -> [EBX+4/+8]60201E/21 | NULL_UNSAFE | YES, native result setters |
| 10 xmlData | 60211F | 4DDA10 -> [EAX]602153, vcall602157 | NULL_UNSAFE | YES, explicit nullable getter/setter contract |
| 11 XmlFilename | 601F98 | 4DEA30 -> wrapper -> 4D0570 | NULL_UNSAFE | UNKNOWN for NULL wrapper |
| 12 uninitialized | 601D93 /602174 | payload ignored; prefix skipped | NOT_POINTER_BACKED for Dump | NULL is ignored |
| StringListName | UNKNOWN | No separate registered label/type or formatter found | STRUCTURALLY_UNKNOWN | UNKNOWN; no guessed alias |

IDs are registered by `0x4DDB90/0x4DEF70`. Wrong-type getter fallbacks are not
proof that typed NULL payloads are safe. No guard is added for unproven NULL
wrapper/scalar/vector/matrix states. No generic Dump-safety claim is made.

## StringList

`0x47D340` publishes NULL PointsList for RACE TIME; `0x47D400` publishes NULL
TimeList in the alternate results format. Setter `0x4DE1C0` explicitly stores
NULL with type9. Header/open brace at `0x602004` precede unsafe `0x60201E`.

Replace six bytes at `0x60201E` (`8B 7B 04 3B 7B 08`) with JMP `0x68E2A0`
and NOP. The19-byte guard TESTs EBX and branches on NULL to `0x602040`, the
stock allocated-empty cleanup. Non-NULL replays MOV/CMP and resumes at
`0x602024`, retaining its comparison flags and list iteration. Cleanup closes
the brace, restores indentation/Broker register and continues the next entry.

NULL output is the existing empty-list grammar `{ }`. **An empty list in this
hardened Dump may mean a NULL payload or an allocated empty list; it does not
prove which existed.** No parser or type-label change is needed.

## XmlData

`0x4DDA10` explicitly returns0 on type mismatch, NULL payload, and certain
filename/query mismatches. `0x4DE480` accepts NULL, stores type10/payload and
checks an old object before release; Broker wrapper `0x4D84C0` forwards that
value. Native Broker Editor `0x65F170` case10 forwards this getter through the
setter, so nullable values can be written through an existing path. This does
not establish XmlData as the cause of the observed Race Results crash.

Dump nevertheless unconditionally dereferences the getter result at `0x602153`.
Replace its seven bytes (`8B 10 8B C8 FF 52 0C`) with JMP `0x68E2C0` and two
NOPs. The28-byte guard preserves flags with PUSHFD/POPFD; non-NULL replays the
original virtual call and resumes `0x60215A`. NULL joins `0x60218E`, the existing
no-root cleanup/next-entry path. It retains the existing xmlData label without
a body, just like a non-NULL object whose root method returns0. Normal XML
printing remains untouched. No SEH/VEH or access-violation recovery exists.

## Cave and parser proof

Caves `[68E2A0,68E2B3)` and `[68E2C0,68E2DC)` are zero raw `.text` padding beyond
original declared end68E294. Read-only Ghidra reports no references into any
byte; the pristine file has no literal absolute pointer into either interval.
They do not overlap existing AI code `[68E300,68E463)`, sections or relocation
sites. Only VirtualSize is extended; raw size/image size/aligned pages unchanged.
Exact expected zero bytes and input hash are verified by the builder.

12 native x86 fixture executions: pristine/hardened populated list, allocated
empty list, NULL list, NULL XML, non-NULL XML with no root, and non-NULL XML
with nullable getter outcome. Three expected pristine unsafe dereferences are
detected before execution; all six hardened fixtures complete. Nine complete
Dumps are accepted by the **unchanged pinned Observatory parser**. Non-NULL
output and log argument/indent sequences equal pristine; NULL StringList output
equals stock allocated-empty output. Braces balance, indentation/RET/callee-saved
registers restore, and `Research/AfterPoints=1` is present after the unsafe entry.

The representative fixture contains ResultsType=RACE TIME, populated NameList
and TimeList, NULL PointsList, then an ordinary Int. enString intern lookup,
logger printf sink, allocator/free and non-NULL XML internals are explicit
synthetic boundaries. The actual native walker/branches/list loops/cleanup
execute. Real post-results Dump/liveness and subsequent race loading remain
the human gate; synthetic emulation is not that result.
