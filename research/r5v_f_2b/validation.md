# R5V-F.2d validation status

| Gate | Status | Evidence |
|---|---|---|
| Research branch / artifacts local to branch | PASS | `research/r5v-f-2b-native-mercedes-cook-proof`; proprietary outputs remain under ignored `research-output/` |
| Cook B native GXM-to-DX path | PASS | One log shows GXM read, DX save, and DX reload for complete (1498/1519/1520), car (1621/1642/1643), and wheel (1650/1671/1672) |
| Cook A/B determinism | PASS, 3/3 | Recomputed complete/car/wheel Cook B SHA-256 matches frozen Cook A values; see `determinism.md` |
| Rev135 parser / geometry | PASS | All three exact DX outputs are identical to the previously parsed Cook A files; strict results VALID |
| Authentic Mercedes tag101 structure | PASS | Finite, indexed, closed, Euler 2, convex, zero-edit serializer pass |
| Tag101 legacy secondary descriptors | UNRESOLVED, bounded | 36 secondary descriptor bytes differ; semantic name remains unknown; accepted for cache-only and controlled runtime P1 |
| DXT dependency closure | PASS, 25/25 | All required DXT files resolve, parse, match source hashes, and were runtime-loaded in prior cook evidence |
| Junction removal | PASS | Fixed helper removed only the exact marked Junction; authoring target and 25 GXI files remain |
| Cache-only package assembly | PASS, static | Fresh runtime copy; exactly 3 DX + 25 DXT under Mercedes; no GXM/GXI/TXT there; manifest hashes rechecked |
| Cache-only preview | WAITING_FOR_HUMAN | Not run in the packaged runtime |
| Cache-only race car/wheel load | WAITING_FOR_HUMAN | Not run in the packaged runtime |
| No authoring-path dependency at runtime | WAITING_FOR_HUMAN | Static Junction absence is proven; runtime log still required |
| Final Mercedes ML-320 profile / candidate | BLOCKED BY CACHE-ONLY GATE | Prompt requires cache-only preview and race load PASS first; no final-profile executable generated |
| P0 / P1 gameplay acceptance | NOT STARTED | Must follow cache-only PASS and final profile generation |
| Synthetic regression suite | PASS | `PYTHONPATH=src python -m unittest discover -s tests\synthetic -v`; 239 tests |

The package and exact human steps are in `research-output/r5v_f_2b/cache-only/`. Do not treat static package checks or the Cook B log as the cache-only runtime result. No ID27, track work, or push is part of this phase.
