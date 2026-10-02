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
| Authoring path preflight | PASS | Exact path absent; read-only preflight returned safe-to-create state |
| Authoring Junction | NOT RUN | Human setup helper prepared; no external path created |
| Retail complete cook | NOT RUN | Awaiting human Vehicle Select capture |
| Cooked DX parser/semantic checks | NOT RUN | No retail cook output |
| Car/wheel cook and collision | NOT RUN | Gated on complete validation |
| Cook A/B | NOT RUN | Gated on validated first cook |
| Cache-only preview/race | NOT RUN | Gated on Cook A/B and output validation |
| Final Mercedes P0/P1 | BLOCKED | No cook proof, cooked collision, determinism, or cache-only load proof |

The isolated runtime tree is prepared at
`D:\Game\Master Rallye\research-output\r5v_f_2b\runtime-cook`. Start with
`HUMAN_COOK_INSTRUCTIONS.txt` and return the complete-cook log and newly
written `complete.dx`. Do not treat this preparation commit as a runtime pass.
