# Independent offline reconstruction

`tools/detail_runtime.py` reuses `tngtool` for source identity, named PackFS
lookup and extraction. It adds only the bounded tag-103 source-surface decoder
and justified CPU arithmetic; it does not duplicate PSB/GXI or implement a PC
renderer.

Supported outputs:

- **Mode A, authored metadata:** exact material strings/spelling, byte offsets,
  unique triangle bindings, source budgets and symbolic category resolution.
- **Mode B, supplied polygon generation:** a selected original triangle with
  explicitly synthetic full activation, or a synthetic polygon through the
  Python API; scanlines, original fixed-table hash jitter and plane/lift.
- **Mode C:** CPU point size/color/fade and VIF metadata with explicit scalar
  inputs. Python API `vu_sprite(size2,RGBA4,projected4,clip4)` additionally
  reconstructs the embedded single-record corner/STQ contract with explicit
  transformed vectors. No live camera matrices or program residency are assumed.

```powershell
python ps2-research/tools/detail_runtime.py --input 'D:\Game\Master Rallye PS2' --course FRANCE1 --output ps2-research/data/grass1/france1-metadata.json
python ps2-research/tools/detail_runtime.py --input 'D:\Game\Master Rallye PS2' --course FRANCE1 --triangle 9174 --rounding nearest_even --output ps2-research/data/grass1/france1-grass-surface9174.json
python ps2-research/tools/detail_runtime.py --input 'D:\Game\Master Rallye PS2' --course FRANCE1 --triangle 16967 --output ps2-research/data/grass1/france1-negative16967.json
```

Record mode additionally requires `--record-camera X Z --projection-scale VALUE
--vertical-factor VALUE`; these are labeled explicit synthetic inputs. Original
coordinates can only be written under ignored `ps2-research/data/grass1/`; the
tool refuses an output path elsewhere. No proprietary geometry is committed.
Unknown/malformed source and unsupported exceptional division fail closed.
This diagnostic policy is not a claim that the original engine safely rejects
every malformed PSM.

| Independent basis | Verification |
|---|---|
| Original PSM bytes | Tag headers, budgets, paired string lengths, triangle indices and material refs; canonical cache compared with fresh PackFS payload |
| Original ELF | Direct JAL/string-load/field/mask instructions; returned IDs and downstream comparisons; original word anchors in optional integration test |
| Synthetic analytic geometry | Shared positive/negative source; winding, slope, degeneracy; independently defined height plane; hand-counted 4+3+2 half-open rows |
| RNG mathematics | Original low32 LCG instruction and fixed seed; independently checked ball invariant and table use/order |
| Packet bits | Original REF/UNPACK/MSCAL/DMA CALL, GS identifier stores, mode11 jump-table target; original MPG words map pc449/37c to ELF instruction pairs |
| Embedded VU contract | Independent opcode/semantics references; hand-derived two-corner/STQ, cap56, clip boundary and integer-conversion examples |
| Reproducibility | Seven canonical-source diagnostic cases rerun; hashes identical; no runtime placement equality claim |

The initial synthetic floor test incorrectly assumed `math.floor` for all
inputs. Original instructions `356c40/356c70/356c84` showed an exceptional
quirk: normalized negative powers of two below one convert to **zero**, because the
fractional check excludes the implicit mantissa bit. Tests now include those
original outcomes, while ordinary signed/boundary inputs retain floor checks.
The arithmetic was not replaced by a convenient library floor.

Precision categories:

| Category | Scope |
|---|---|
| EXACT_ELF_OPERATION | Integer token comparisons, low32 RNG recurrence, record offsets, packet/state words and original instruction anchors |
| FLOAT32_RECONSTRUCTION | Normal, scanline, jitter rejection, hash/plane/size/fade arithmetic; explicit nearest-even host float conversion |
| MATHEMATICALLY_EQUIVALENT | Plane-height interpretation, approximate slope angle and interior lattice-density estimate only |
| APPROXIMATE_MODEL | No visually fitted grass distribution or billboard model is supplied |
| UNKNOWN | Live FCSR, PS2 exceptional FPU/VU behavior, clipped camera-history replay, exact program upload/residency, final frame flush and runtime visual parity |

Ghidra12.1.4 was accessed through the installed bridge exporter. Read-only
project queries temporarily normalize LQ/SQ low halves, EE MULT rd and SQRT
operand where audited, then roll back. A generic HI/LO guard remains intact.
The detail builder's sole MFHI was separately audited as consuming its original
DIVU remainder; other guarded queries were run without unsafe normalization.
Original words always ground the claims. Truncated/packed decompilations never
become whole-function proofs. Full queries stay ignored.

`data/grass1/synthetic-vu-sprite.json` is a fully synthetic analytic example:
size(4,8), projected(200,100,600,2), clip(.5,-.5,1,2). Expected corners are
(102,54,300)/(98,46,300), STQ(0,0,.5)/(.5,.5,.5), and FTOI4 values
(1632,864,4800)/(1568,736,4800). This checks the embedded-program arithmetic;
it is not a PS2 frame or proprietary world placement.
