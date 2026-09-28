# Course source to compiled map (R5T-B)

| Source evidence | Compiled/runtime observation | Status |
|---|---|---|
| France1/Italy1 8.4.1 GXM/TXT paired node tables parse exactly; mesh spans and helper names are preserved | Selecting France1 in 9.10.0 with DX/DXT absent emits revision-135 DX and DXT | `CONFIRMED_BY_SOURCE_COMPILED_PAIR` + `CONFIRMED_BY_RUNTIME`; no per-node causal mapping |
| France1 `startpoint` is a source `moMesh` at `Index 0`, `Size 12` | Owner reports the recooked old source retains old 8.4-style grid placement | `CONFIRMED_BY_RUNTIME` correlation; no controlled startpoint edit |
| France1 `_raceline`; Italy1 `raceline`; bounds names `_limits`, `$boinds`/`_boinds`, and `$ps2cells` have exact source spans | Recooked course AI works per owner report | `CONFIRMED_BY_RUNTIME` for AI; no source-to-route binary mapping |
| France1/Italy1 contain source `$bsp`; France1 nested `$draw $landdb` and `$nodraw` | Recooked rev135 DX has tag100 raw tail; repeat France cooks preserve that raw tag100 hash | Source presence and compiled structure confirmed, but `$bsp` → tag100 is **not** isolated |
| Old France TXT has no `$alphatest` or `$shader(tree)` strings; late TXT contains both | Old-source recooked foliage draws use `flags_0x20=01000101`; native 9.10/retail tree-name candidates mostly use `01010101` | Source and binary/corpus correlation; visual fix is not confirmed |
| RaceTest France1/Italy1 XML has `Marker`, `gaRaceSplitTimeAI`, `gaRacePostFirstSplitTimeAI` records | Every positioned marker lies within the matching Demo 9.10 DX position AABB | Binary facts confirmed; shared coordinate frame is a `HIGH_CONFIDENCE_INFERENCE`, not proof of gameplay ownership |
| R5T-A reports retail SFL dimensions/payload lengths; no SFL bytes are in current inputs | No spatial transform or SFL-to-helper correlation computed | Meaning and coordinate mapping remain `UNKNOWN` |

The two repeated France1 cooks are especially useful as a control: the same
source/executable produced different DX render-prefix hashes/counts while all
172 non-DX files matched, and the raw tag100 payload hash remained constant.
This separates observed render-prefix variability from tag100 bytes, but does
not identify the source of that variability.

The exact binary metrics live in `cooker-baseline.json`,
`foliage-materials.json`, and `xml-marker-correlation.json`.
