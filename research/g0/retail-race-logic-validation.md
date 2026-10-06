# G0 RaceTest authoring validation

Status: **PASS** for principal corpus no-op validation; France1 edit scenarios: **PASS**.

- Principal Retail course projects: 36
- RaceTest XML parsed and no-op exported byte-identically: 36/36
- StartArea authoring supported: 36/36
- FinishArea authoring supported: 34/36
- SplitTime records authoring supported: 110
- SplitTime visual companion Egg Row3 positions supported: 440/440
- Visual companion count per course: `{"12": 34, "16": 2}`
- Visual companion count per split: `{"4": 110}`
- Split companion layout exceptions: 0
- Split count distribution: `{"3": 34, "4": 2}`

## Safely refused source structures

- Italy_S4 FinishArea: 5 markers; authoring requires exactly four ordered markers; found 5.
- Turkey_s1 FinishArea: 5 markers; authoring requires exactly four ordered markers; found 5.

## France1 static edit checks

- PASS — StartArea rigid +3 runtime X: 4 allowlisted field(s), output SHA256 `c44194011a4bd448554ccbce66bb5869fa98a2e695f842dea7a2de0bdd0381f6`.
- PASS — FinishArea X/Z scale 2 around centroid: 4 allowlisted field(s), output SHA256 `78c82bd16af9a342691ff4a4cef7f168a65429966a74a6ead98dd2716ee12f7d`.
- PASS — SplitTime0 center move: 1 allowlisted field(s), output SHA256 `0a92333c3ccc414e9609c8f795542d3840dc1fdbfed0786d03ca7899c007b75f`.
- PASS — SplitTime0 Radius edit: 1 allowlisted field(s), output SHA256 `bab8d66c8943da290211a76a628bd0f95100ca5411ff7a816e7939a20be08442`.

These generated XML bytes were checked in memory only. No proprietary RaceTest file was written or runtime-tested.
