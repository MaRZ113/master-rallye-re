# R5V-F.2d retail cook determinism

## Result

**MERCEDES RETAIL NATIVE COOKER: DETERMINISTIC FOR COMPLETE/CAR/WHEEL.**

Cook B is a fresh single-session recook of all three Mercedes roles. Its DebugView log records GXM reads, DX saves, and DX reloads for each role. Recomputed Cook B SHA-256 values match the frozen Cook A snapshots byte-for-byte:

| Role | Bytes | Cook A SHA-256 | Cook B SHA-256 | Cook B log evidence |
|---|---:|---|---|---|
| `complete.dx` | 122372 | `ddad0c7b13be70388a60a541255eaaf3af7f9b1815f5aa02f2b60050862dc28b` | identical | read 1498, save 1519, reload 1520 |
| `car.dx` | 112722 | `5ec5f7480ddfc1380131a012b300a4cdeb28b869a1668b6f8bbe97210893ff44` | identical | read 1621, save 1642, reload 1643 |
| `wheel.dx` | 12997 | `8707d887a75c452eb739775e21f94109521d9fc6be07726cee28a8e911c590ff` | identical | read 1650, save 1671, reload 1672 |

The Cook B log is `research-output/r5v_f_2b/cook-b/cook-b.log`; the separately recorded comparison is `cook-b/cook-b-hashes.txt`. The captured DX files are preserved under `cook-b/cache_snapshot/DataGx/Vehicles/Mercedes/`. Their computed hashes were checked again before packaging.

This proves repeatability for these exact GXM inputs, retail executable, cooker configuration, and runtime environment. It does not establish determinism for arbitrary GXM or other retail builds.

## Cache-only handoff

The assembled runtime is at `research-output/r5v_f_2b/cache-only/runtime/`. Its Mercedes folder contains the three Cook B DX files and the 25 required DXT files. The machine-readable inventory and SHA-256 closure are in `cache-only/cache-manifest.json`; the human run procedure is in `cache-only/CACHE_ONLY_TEST_INSTRUCTIONS.md`.

Static package checks pass. Preview, race car/wheel load, and authoring-source independence remain **WAITING_FOR_HUMAN** until the isolated DebugView test is run.
