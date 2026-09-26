# R-BRIDGE2 — DEMO 9.10.0 cooker bridge to retail

## Decision

**The practical bridge is confirmed by human runtime testing.** Older demo source/assets were processed by the original DEMO 9.10.0 cooker; its generated DX/DXT resources were then loaded by retail in an existing vehicle slot. The user confirmed Trooper and Rav4 transfers, model rendering, and damage. Trooper was tested in the retail Navara slot. The exact older source corpus, source hashes, generated hashes, and the Rav4 target slot were not recorded. Driving physics equivalence was not tested.

The demonstrated route is:

```text
older demo source/assets
        -> original DEMO 9.10.0 cooker
        -> generated revision-135 vehicle DX and generated DXT
        -> RETAIL existing vehicle slot
```

This runtime result answers feasibility. It does not prove that raw 8.4.1 or 9.3.1 DX is directly accepted by retail, and it does not replace the future standalone parser/rebuilder work.

## Corpus boundaries and inventory

The 8.4.1, 9.3.1, 9.10.0, and retail corpora remain distinct. Hashes below are recomputed from the read-only corpus files by `tools/scanner/r_bridge2.py`. Retail has no vehicle GXM in the extracted corpus.

| Vehicle / role | DEMO 9.10.0 DX: bytes / SHA-256 | DEMO 9.10.0 GXM: bytes / SHA-256 | Retail DX: bytes / SHA-256 |
|---|---|---|---|
| Jump / car | 124,436 / `baedb30dae27857a768e5332e0346a3aa2f4c8dfcb0860635d69b0c444cc5c79` | 217,594 / `55bd09e1f8c9c647c82381dba463bb555dfcc51c6b2d63b9e8e39c55231da17e` | 127,341 / `a6ad8bcb7c71e572f065a5c3710308730c2c4f0cc8b32f25af279adc923a7baa` |
| Jump / complete | 134,496 / `8a2bad8811eb18ba05cc0d51333726f7c886b9dbeda4dde81d61af8450346117` | 255,282 / `e001670f5dc825a359cc6e035a55035fa0a67f60f820c4d6f1d34cf6310dca0d` | 134,496 / `bf7dc94e437fd66b90f9ca54fc150651a834b75147c894bf7804c98f1aa9a65a` |
| Jump / wheel | 12,997 / `6ef55e14367738bd8a7549c47bfa52aa89a76d955a572dd7d7295aaf39ae6afd` | 27,227 / `68c084024eb7df133e133b47739991a0f25440452c6e9259facc51250d963245` | 12,997 / `81c6a980df7c32ae16702afda6a42dfb6f9b5917c9cd6d7ddb4e3a84c0bf0ab0` |
| Navara / car | 159,515 / `717d42d0eaaeed10cfef5dd870f79796172dc2f14d947fbed3cb89371fdf2d86` | 265,427 / `1cf07b67ac432abf4307a19e7ec77c8717c0209bb29796545e38d251c21cc1c9` | 166,309 / `2d3727f5bcd889ba38891276111c53f9c4d67cee1f5ece13de374a8235690655` |
| Navara / complete | 174,417 / `1fbc46dbe7aca3abc35b7b96208f222fe665418d4daf12746b65c7cf7892fe05` | 308,766 / `1fdff62f4ea64b581354e4953b6ea711684c6cdb84426b2c22eee2c00d05ca79` | 174,352 / `0edab556302273db41736993cdd041e73b1894419a623526c91f458b5fcfdc2e` |
| Navara / wheel | 12,904 / `2ae0c70a1912edfa8c628038541305132bf6843a00d33ce8761f351f17b72e08` | 27,030 / `184c7846ca1a9d9296b754b44479b2e9c9c15c2061242d86159f8f73d970969a` | 12,904 / `2ae0c70a1912edfa8c628038541305132bf6843a00d33ce8761f351f17b72e08` |

The selected 9.10.0 Jump folder contains 25 DXT and 26 GXI files; Navara has 35 DXT and 89 GXI. Retail Jump has 29 DXT; retail Navara has 95 DXT. These are corpus inventories, not the hashes of the runtime-generated transfer sets.

All six listed 9.10.0 GXM files pass the existing GXM material-table prefix parser. All six listed 9.10.0 DX files and all six corresponding retail DX files pass the retail typed parser; their headers use magic `0xD00D`, revision 135, and marker 1337. Retail parser acceptance is static structure evidence, separate from the human runtime bridge result.

## Revision and compatibility

The 18 vehicle DX files present in DEMO 9.10.0 (six vehicles × car/complete/wheel) all carry revision **135** and pass the project's retail typed parser. The complete 9.10.0 `DataGx` inventory has 40 DX files and is mixed: 35 revision 135, one 133, two 134, and two 131. The retail typed parser accepts 34/40 overall; the six failures are non-vehicle or special resources. Do not describe every 9.10.0 DX file as revision 135 or parser-compatible.

| DX producer / source route | 8.4.1 loader | 9.3.1 loader | 9.10.0 loader | retail loader |
|---|---|---|---|---|
| 8.4.1 raw DX | CONFIRMED_BY_RUNTIME | UNKNOWN | UNKNOWN | REJECTED_BY_STATIC (revision 127 gate) |
| 9.3.1 raw DX | UNKNOWN | CONFIRMED_BY_RUNTIME | UNKNOWN | REJECTED_BY_STATIC (revision 131 gate) |
| 9.10.0 emitted vehicle DX | UNKNOWN | UNKNOWN | CONFIRMED_BY_RUNTIME | CONFIRMED_BY_RUNTIME for the reported cooker-generated vehicle resources |
| retail DX | UNKNOWN | UNKNOWN | CONFIRMED_BY_RUNTIME for human-tested resources | CONFIRMED_BY_RUNTIME |

The human also reported that model resources from other demos worked in 9.10.0, but did not identify their exact source build or establish whether each was loaded raw or passed through the cooker. Those producer cells stay UNKNOWN. The retail-to-9.10.0 observation is runtime evidence for the tested resources, not a universal promise for every retail DX.

The prior R-BRIDGE1 result remains valid: raw revision-127/131 demo DX is not a direct retail candidate. Using the 9.10.0 cooker avoids that immediate blocker because tested output is in the late retail-compatible vehicle format. A standalone converter still needs evidence-backed draw/material parsing and writing.

## Jump wheel across four generations

Jump is the same-vehicle control. `wheel.dx` is especially stable in render structure:

| Transition | Byte comparison and structure |
|---|---|
| 8.4.1 → 9.3.1 | Both 12,932 bytes. Exactly one byte differs, offset `0x04` (revision 127 → 131). Positions, normals, colors, UVs, local/global indices, 388-byte draw region, and 56-byte collision block are exact matches. |
| 9.3.1 → 9.10.0 | 12,932 → 12,997 bytes; 2,401 differing bytes by same-offset comparison, including a 65-byte size increase. Counts and topology are stable. 196 position components drift by at most `2.2351742e-8`; 216 normal components by at most `5.9604645e-8`. Colors, UVs, and indices match. The draw region grows from 388 to 453 bytes; the 56-byte tag-102/collision tail is exact. This is a serialization transition with small float drift. |
| 9.10.0 → retail | Both 12,997 bytes and revision 135. Exactly 485 bytes differ: 260 in position bytes and 225 in normal bytes. All other parsed regions are unchanged, and the byte-region partition reports zero unexplained bytes. The maximum component differences match the small float drift above. |

The 9.10.0 Jump `car.dx` is not a byte-compatible retail copy: 124,436 vs 127,341 bytes, 2,361 vs 2,401 vertices, and differing render/draw/collision content. The `complete.dx` files share the 134,496-byte size and topology/index arrays, with very small position/normal drift, changed colors, and an identical draw region; tag-102 data differs. The established bridge is a cooker workflow, not a blanket file-copy rule.

## Navara 9.10.0 versus retail

`Navara/wheel.dx` is exactly byte-identical: both files are 12,904 bytes, revision 135, SHA-256 `2ae0c70a1912edfa8c628038541305132bf6843a00d33ce8761f351f17b72e08`.

`car.dx` and `complete.dx` are not exact interchangeable controls. The car files differ in size, vertex/index counts, draw serialization, and collision data. Complete files have 3,397 vertices in both, but positions, normals, colors, UVs, index streams, draw bytes, and tag-102 data differ materially. The sampled wheel asset alone is directly identical.

Named configuration values also differ outside the DX assets: 9.10.0 Navara has `WheelBase=2.6`; retail Navara has `WheelBase=2.8`. Both extracted XMLs list `TrackWidthFront/Rear=1.7`, wheel radii `0.38`, and front/rear ride heights `0.05`. This is evidence that slot configuration can evolve separately from model files; it does not by itself establish which config entry the runtime wheel instance uses.

## Transfer records and limits

| Vehicle | Result | Known target | Missing provenance |
|---|---|---|---|
| Trooper | HUMAN_RUNTIME_CONFIRMED: loaded/rendered in retail and damage works; race wheel placement is wrong while complete-model placement looks correct. | Navara slot | Exact older source corpus and source/generated hashes |
| Rav4 | HUMAN_RUNTIME_CONFIRMED: imported by the same 9.10 cooker route; model/render and damage were reported working; wheel placement issue was reported. | UNKNOWN | Exact older source corpus, target slot, and source/generated hashes |

The current practical path is the original 9.10.0 cooker. Its DX/DXT output was generated by the game, not by this repository's writer. The human runtime record is retained in `.research-output/r-bridge2/r-bridge2-scan.json`; proprietary/generated resources remain outside Git.

## Reusable analysis

`src/master_rallye/bridge2_analysis.py` parses named complete-model wheel spans, measures source and DX-space bounds, compares DX render/index/draw/collision regions, and audits exact XML vehicle roots without inventing `CarN` aliases. The read-only entry point is `tools/scanner/r_bridge2.py`:

```powershell
$env:PYTHONPATH = 'src'
python tools/scanner/r_bridge2.py `
  --corpora-root 'D:\Game\Master Rallye\corpora' `
  --output '.research-output\r-bridge2\r-bridge2-scan.json'
```

All generated reports go beneath ignored `.research-output/`. See [R-BRIDGE2 wheel placement](r-bridge2-wheel-placement.md) for the current blocker.
