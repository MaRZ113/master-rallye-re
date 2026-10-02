# R5V-F.2b validation status

| Gate | Status | Evidence |
|---|---|---|
| Research branch | PASS | `research/r5v-f-2b-native-mercedes-cook-proof` |
| Source identity | PASS | 59 root-file hashes, pinned GXM hashes, and separate `lpha` inventory in ignored `research-output/r5v_f_2b/source-manifest.json` |
| Retail EXE/Data.sma identity | PASS | Exact F.2a SHA-256 values; staged copies re-hashed |
| Retail archive Mercedes cache absence | PASS, static | 0 `DataGx/Vehicles/Mercedes/` members in 7,595-member archive index |
| Historical DXT validity | PASS | 44/44 byte-identical DXT round trips; only 25 root Mercedes files staged |
| ID26 harness structure | PASS, static | 27 records; T1=8, T2=7, T3=12; ID25 Trooper intact; candidate rebuild verified |
| Source/canonical mutation check | PASS | Source manifest before/after equal; output-only copies; retail hashes unchanged |
| Authoring path and Junction | PASS, path setup | Junction target is the isolated authoring root; retail read the staged GXM from the runtime tree without rewriting it; no GXI-read event is logged |
| Retail `complete.dx` cook | PASS | Cache miss → staged `complete.gxm` read → build → save → reload; output SHA recorded |
| Revision/parser/footer/bounds | PASS | Revision 135; strict SDK validation; recognized footer bounds match; collision tail validated |
| Material/texture references | PASS | 20 non-null DX refs resolve to staged DXT and all 20 load in the captured retail log |
| Semantic comparison to legacy rev127 | PASS, small bounded color drift | Counts, bounds, normals, UVs, local/global indices match; tiny position drift and one-code RGB change recorded, cause not independently established |
| Car/wheel cook and collision | AUTHORIZED, NOT RUN | `car.dx` / `wheel.dx` remain absent; complete-only gate passed |
| Cook A/B | NOT RUN | Gated on validated first cook |
| Cache-only preview/race | NOT RUN | Gated on Cook A/B and output validation |
| Final Mercedes P0/P1 | BLOCKED | Car/wheel outputs and collision, full Cook A/B, and cache-only load proof remain pending |

The repo-local isolated runtime tree is at
`D:\Game\Master Rallye\master-rallye-re-e0.1\research-output\r5v_f_2b\runtime-cook`.
The complete-only gate is now passed. Use an offline Practice/Quick Race
solely to cook `car.dx` and `wheel.dx`, then return their log and output hashes
for offline validation. This partial result is not the full R5V-F.2b pass.
