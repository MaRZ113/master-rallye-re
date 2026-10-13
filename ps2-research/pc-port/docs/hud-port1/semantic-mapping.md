# HUD-PORT1 — SpeedDial semantic packet mapping

Status: **PARTIAL**. Replacement: **NOT_IMPLEMENTED**. Live semantic mapping:
**NOT_PERFORMED**. This is one original-PC widget investigation, not another
whole-HUD reverse or a new rendering feature.

## Original native identity now grounded in bytes

Exact retail PE SHA256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
ImageBase `0x00400000`, PE32/i386. REA opened that exact file using Ghidra
12.1.4, ephemeral-source-immutable profile; GNU objdump independently decoded
the original instruction windows. No process attachment, code injection,
engine call, game memory write or original file edit was performed.

| Original address | Byte-backed role |
|---|---|
| `0x006E5234` | Exact terminated `gaHudAiSpeedDial` string |
| `0x004A8120` | Constructor; references that string at `0x004A8124`; installs vtable `0x00690F38` at `0x004A8147` |
| `0x004A81A0` | Factory; allocates `0x44` bytes, calls constructor at `0x004A81D2` |
| `0x00690F38` | Six examined vtable slots: destructor `4A8200`, factory `4A81A0`, serialization `4A8230`, deserialization/init `4A8370`, no-op `4A85B0`, no-op `403630` |
| `0x004A8370` | Reads authored fields, calls `4A8440` with the first original stack argument at `4A842A` |
| `0x004A8440` | SpeedDial initialization; passed object+`0x4C` is dereferenced for point components +`0x54/+0x58`; calls original HUD-setting service |
| `0x004F5950` | Original Egg AI attachment; four AI pointer slots at Egg+`0x04+4*slot`, `slot=0..3`; replacing an occupied slot calls its destructor |
| `0x0056BA70` | Render service consumes its original entity/Egg argument; passes the same pointer to `56D110` at `56BAE1` if +`0x4C` is non-null |
| `0x0056D110` | Existing independently verified UI packet consumer; final draw return `56D7C4` |

These roles are **CONFIRMED_BY_EXE**. They provide a concrete class fingerprint
for a passive observation: a current consumer entity whose valid current AI
slot points to an object with vtable `0x00690F38` is a candidate original
SpeedDial owner. This is substantially stronger than screen location, texture,
draw ordinal or generic UI callsite. It has **not** yet been tested on a live
consumer entity; static structural compatibility is not a live join.

Important pseudocode limitation: Ghidra renders constructor assignment +`0x08`
as `in_ECX[2] = in_ECX`. Assembly instead reads the post-call local stack value
into EAX and stores EAX into `[ESI+8]`. Treat that field as the original
interning result only after verifying `4D0580` semantics independently; do not
publish the decompiler's self-pointer expression as an original structure.
Similarly, Ghidra types `4A8440`'s pointer parameter as float. The integer
pointer dereferences in assembly are authoritative. No field at AI+`0x0C`
has been promoted to a texture-bank ID; it participates in authored `Hud No`
settings and must not be confused with image key0.

## Precise next read-only join

Reuse one complete F10 capture's **current** consumer entity roster. With the
game paused at the corresponding original consumer (or a tightly bounded
read-only snapshot with explicit race/UI generation and double rereads), read
only each roster entity's four confirmed AI slots, each readable AI vtable,
and the already established entity/packet identity. Do not scan the heap or
call any native getter. Require exactly one SpeedDial-class candidate for the
selected player HUD, reject stale/changed slots and generations, and retain
negative controls for SpeedNeedle, other counters, pause and frontend.

If passive polling cannot establish same-lifetime join, use a capped manual
x32dbg observation at `4A8370` / `4A8440` with ECX=AI and original stack
argument=owner, followed by the existing `56D110` consumer. This requires user
participation; it is not requested during the parent's current physics run.
No unbounded per-frame UI logpoints and no new Broker reads are needed.

Minimum F10 correlation inputs: session executable SHA and DLL SHA, frame ID,
device ID, active race generation, UI epoch, current consumer entity, packet,
point and content-storage pointers, packet mode, completeness/drop counters,
the verified consumer return RVA `0x0016D7C4`, FVF `0x142`, primitive arguments,
current texture/resource generation and original/effective pipeline states.
Keep the captured entity-to-packet identity distinct from texture ownership.
A current passive snapshot must reread entity AI slots and packet pointer
before/after the bounded reads and reject any changed or unreadable tuple.
The original `4F5950` setter destroys an occupied AI and `4F5880` destroys an
occupied +`0x4C` packet, so a pointer retained across restart/exit is unsafe.
Even identical double reads do not solve ABA reuse or prove draw-time ordering;
without current lifetime/epoch correlation the result remains a candidate.
**Native image bank/key offset: UNKNOWN.** No UI packet field is relabeled as
key0 merely because authored XML selects key0.

## Remaining asset/draw gate

Protected `Hud0.xml` authors `SpeedDial`, `hud\\hud-template`, image-bank index
0; `SpeedNeedle` uses the same model but index2. Existing live captures still
contain `owner_mapping_status=unmapped`. Neither XML names nor this new class
fingerprint alone proves the full plate's texture generation, UVs, native
packet child geometry or bank selection. PC DXB remains unsupported by the
PS2 PSB parser. Preserve the original unsupported-format boundary.

The replacement decision is therefore **BLOCKED_PENDING_CURRENT_SEMANTIC_JOIN
AND_PLATE_RESOURCE_GEOMETRY**. A future plate-only pilot can retain original PC
needle, speed and gear feeds, but may activate only after current SpeedDial
class + current packet + bank0 geometry + texture ownership are verified.
No implementation, config key, build or texture override was added here.

```text
Hud0 SpeedDial / gaHudAiSpeedDial (source)
 -> exact native class constructor / vtable (CONFIRMED_BY_EXE)
 -> current Egg AI slot + consumer entity (UNKNOWN LIVE LINK)
 -> current packet / bank0 / original plate geometry (UNKNOWN RESOURCE LINK)
 -> existing final native draw (known generic UI path)
```

The frozen renderer, once-per-frame HUD context cache, GRASS2/water/reflection,
canonical build roots and original game resources remain unchanged.
