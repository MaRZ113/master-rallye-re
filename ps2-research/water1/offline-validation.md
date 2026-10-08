# Offline reproduction and independent checks

`tools/water_runtime.py` supports only justified diagnostics:

- `inspect`: named canonical PSM through PackFS, visual materials/strips, counts,
  topology metrics and separately validated tag-103 boundary.
- `compare`: validated read-only PC draw data, all-draw geometric correspondence
  and Turkey3 centroid height projection. No fitted transform.
- `contract`: committed ELF-derived render state, inheritance and submission map.
- `waterfall-uv`: explicit counter/Y/U evaluation of the recovered bounded formula.

All CLI diagnostics and optional source footprint SVG stay under ignored
`ps2-research/data/water1/`. The SVG uses authored X/Z, not screenshot tracing
or a synthetic blue-water shader. No full geometry or extracted image enters Git.

```powershell
python ps2-research/tools/water_runtime.py compare --input 'D:/Game/Master Rallye PS2' --course TURKEY3 --pc-root 'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked' --sdk 'D:/Game/Master Rallye/master-rallye-re-course' --output ps2-research/data/water1/turkey3.json --svg ps2-research/data/water1/turkey3.svg
python ps2-research/tools/water_runtime.py compare --input 'D:/Game/Master Rallye PS2' --course FRANCE1 --pc-root 'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked' --sdk 'D:/Game/Master Rallye/master-rallye-re-course' --output ps2-research/data/water1/france1.json
python ps2-research/tools/water_runtime.py compare --input 'D:/Game/Master Rallye PS2' --course ITALY_S1 --pc-root 'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked' --sdk 'D:/Game/Master Rallye/master-rallye-re-course' --output ps2-research/data/water1/italys1.json
python ps2-research/tools/water_runtime.py inspect --input 'D:/Game/Master Rallye PS2' --course TURKEY1 --output ps2-research/data/water1/turkey1.json
python ps2-research/tools/water_runtime.py inspect --input 'D:/Game/Master Rallye PS2' --course SPAIN_S2 --output ps2-research/data/water1/spains2.json
python ps2-research/tools/water_runtime.py contract --output ps2-research/data/water1/contract.json
python ps2-research/tools/water_runtime.py waterfall-uv --counter 15 --source-y 20 --first-source-y 20 --source-u .25 --output ps2-research/data/water1/synthetic-waterfall.json
```

The first three commands were run against original inputs. The two controls
were separately decoded using the same public inspection functions. Raw reports
were reviewed against exploratory independent decoders; compact results are
`case-evidence.json`. Exact source resource identity is verified before CLI
PackFS operations. Unknown build, grammar, ambiguous input, string lengths,
vertex range or non-finite coordinates fail closed.

| Independent evidence | Purpose |
|---|---|
| Original PSM bytes +391d38/390ba8 | Material belongs to actual visual mesh, not string occurrence alone |
| Separate GRASS1 spatial decoder | Confirms scene ends exactly before tag103 without deriving visual faces from it |
| PC SDK coverage +all-draw corner tests | Independent geometry representation; France/Italy exact bounded controls |
| Barycentric X/Z height projection | Detects equivalent surfaces with different tessellation; not a repeated triangle-key test |
| Original ELF words/JAL/vtable pointers | Validates classification, mode/handle fields, CPU draw/state/upload/start |
| GS bitfields +ALPHA masks | Distinguishes alpha content/test/blend and depth test/write |
| Original GXI plus existing parser | Texture alpha statistics independent of render-state assumptions |

Source coordinates are decoded exact float32 byte values.
Count/range/string/bit operations are **EXACT_ELF_OPERATION** within the
documented grammar. Geometric area, normals and correspondence are
**MATHEMATICALLY_EQUIVALENT** diagnostics using host doubles and stated tolerances.
The optional waterfall formula is **FLOAT32_RECONSTRUCTION**, not exact EE/VU
parity. FCSR, host sine parity, caller clock and captured runtime inputs remain
**UNKNOWN** where applicable. No original-data synthetic replacement is emitted.

The function inventory records unresolved ends instead of treating a truncated
Ghidra decompilation as a full function. Queries use newest installed Ghidra12.1.4
and ghidra_ai_bridge; all temporary scalar/stack substitutes are rolled back.
The canonical file is never modified. A HI/LO-consuming window is intentionally
rejected by the scalar surrogate guard rather than analyzed with wrong math.
