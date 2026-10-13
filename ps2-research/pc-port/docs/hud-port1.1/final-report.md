# HUD-PORT1.1 — exact plate source mapping gate

Status: **PARTIAL; replacement NOT_IMPLEMENTED**. This bounded investigation
used the existing current-SpeedDial evidence and one new original consumer
function through REA/Ghidra12.1.4, plus five small x86 instruction windows/functions
through independent GNU objdump. Exact PE SHA256 remains
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
REA evidence `ev_aa8a5e5bd263e0a58a0ed855d9c26191c9c4ed4aca8862c8abde8266070b78c9`.
Pseudocode is not original source. Original instruction addresses and byte hashes
are retained in `plate-source-evidence.json`.

## New confirmed original-byte facts

- `56D448`: packet+8/+C is a begin/end vector. Content rows have stride0x38
  (`56D81D`). One row's model ID is at+0x10; u16 image-key begin/end at+4/+8.
- `56D5AA` loads a u16 authored key, calls `56E5C0`, then `56D5D5` reads the
  returned map node's signed16 subimage index at+0x0E. Thus image **key0 is
  not automatically subimage index0**. Neither is AI+0C an image key.
- Bank+4/+8 holds16-byte subimage records; subimage+4/+8 is its triangle span.
  `56D7CC` advances each triangle0x34 bytes.
- Source triangle layout: texture-resource ID at+0, three float UV pairs at
  +4..+0x18 and three signed32 integer XY pairs at+0x1C..+0x30.
- `56D655..65D` resolves the triangle texture ID through original `54ACD0`.
  The returned wrapper is in EAX at checkpoint56D65D. `56D6B8` loads
  `[EAX]` into EBP; `56D708..70E` passes EBP as the stage0 texture argument to
  original device vtable+0xF4 (SetTexture). This proves **argument pointer**,
  not F10 COM resource generation or original resource pixel identity.
- For row flag+0x34==0, the generated source-position expression is
  `X=intX+rowX-0.5; Y=rowY+0.5-intY`; Z comes from rowZ. The source triangle
  XY/UV is distinct from final transformed screen vertices. WORLD and other
  transform calls still apply, and active row flags must be reported.

## One exact first missing link

**A same-session draw-time observation joining current SpeedDial class/packet,
key0-selected subimage, actual source triangles and SetTexture argument to the
proxy's current texture generation and certified frame/lifetime.** Historical
frame35007 pointers or draw95/96 are not reused by the collector or recipe.

`paused-plate-probe.py` is a one-shot RPM-only collector at explicit debugger
pause56D65D. It uses PROCESS_VM_READ and exact original executable identity,
checks current Egg AI **slot0** vtable690F38, packet ownership, exactly one row
with exactly key0, the current native key-map index and exactly two source
triangles. It rejects changed owner/bank/geometry/wrapper tuples and nonfinite
UV. It reads <=32 map nodes and <=2 triangles within the established64KiB
budget. No heap scan, engine getter, COM method or memory write is used.
Slot0 is an explicit fail-closed restriction, not a universal HUD AI layout.

User-declared debugger pause is not independently verified by RPM. Double reads
are not an atomic native generation proof. Even a successful collector does
**not** authorize replacement. Native argument may be a proxy/native wrapper;
matching it to F10 generations requires the actual same-session current binding
and unwrap relationship, not pointer equality assumed across COM layers.
Current player ownership, restart/Reset resource retirement and original DXT
content hash remain runtime gates. No source edit, DLL build or A/B visual
success is claimed.

| Gate | Result |
|---|---|
| Original current SpeedDial class | Prior bounded runtime evidence retained |
| Native key/plate/vertex instruction contract | PASS / CONFIRMED_BY_EXE |
| Current exact plate bytes | NOT_PERFORMED |
| Key0 current bank selection | NOT_PERFORMED |
| Current texture content/generation | BLOCKED on same-session binding join |
| Current player/race/UI/Reset lifetime | PARTIAL |
| Replacement implementation / visual A/B | NOT_PERFORMED |

Focused tests: `python .../plate-contract-tests.py -v` **16/16 PASS**:
source layout, UV/size/span checks, exact-vs-needle/ambiguous joins, changed
owner/bank/triangle/texture argument, no synthetic authorization. These are
synthetic tests, not live original plate observations. Frozen renderer,
overlay integration, accepted DLL and once-per-frame HUD cache remain unchanged.
