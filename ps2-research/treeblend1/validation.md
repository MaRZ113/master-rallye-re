# TREEBLEND1 validation

**Overall: COMPLETE at the bounded static/executable level. Runtime: NOT_PERFORMED.**

## Regression results

| Check | Actual result |
|---|---|
| Full unittest, configured PS2/PC/SDK/HUD corpus | PASS:270 tests,270 successful,0 failures,0 errors,0 skips;60.380s |
| Full pytest, same external inputs | PASS:270 tests and286 subtests;0 failures/skips;61.04s |
| TREEBLEND-specific coverage | 30 methods:25 synthetic/compact-evidence,5 original ELF/mesh/PC methods |
| Focused final rerun | PASS:30 methods,0 failure/error/skip;17.359s; additional original-anchor check1/1 PASS |
| Compileall tools/tests | PASS |
| Diagnostic repeat | PASS: cases-v4/repeat identical SHA-256 f9c100752acf2f9542ba34f3e88464859a0a0e885add37d21af11093bc871c80 |
| Git diff-check | PASS |
| Isolated handoff unittest | PASS:234 successful methods,13 method skips and8 class-setup skips; standard result Ran247,skipped21;0 failures/errors;0.195s |
| Isolated handoff pytest | PASS:234 tests,170 subtests;36 dependency skips;0 failures;0.57s |
| Input/SDK/renderer integrity | PASS:14 original-file hash checks; SDK HEAD/status unchanged; renderer diff empty |

Initial restricted baseline:240 tests, six existing temporary-file PermissionErrors, **FAIL/environment restriction**, retained in ignored local logs. A reviewed rerun allowed the synthetic temporary-file operations; tests were not weakened or converted to skips. Final logs are included under `validation-logs/`.

Synthetic tests cover token spelling/case/substrings, handler/mode identities, unknown inherited bits, alpha-test/blend/depth distinctions, FBA versus PABE, source-color clamping, original byte float32 round trips, source attribute layout, malformed/non-finite input, deterministic state and output confinement. They do not invent a billboard/wind/LOD model.

Original integration independently checks620 canonical CPU words, selected VU pairs and ten string/vtable/jump-table anchors, five original mesh/material bindings/counts, strict GXI identities/alpha and two PC original flag byte locations. Pixel comparisons use separate GXI/DXT source readers. GEOM/DRESSING's established matcher and correspondence anchors are preserved. A final source-path separator normalization was covered by the focused rerun; its Windows diagnostic values were unchanged.

## Acceptance gates

| Gate | Result | Evidence / boundary |
|---|---|---|
| 1 Git discipline | PASS | Restored master in requested checkout; scoped files; no push |
| 2 Canonical provenance | PASS | Four exact canonical hashes, fresh verification and source preservation |
| 3 tree registration | PASS | 3a75b8,487d08,3ae710; original bytes/vtable/registry |
| 4 treeblend registration | PASS | 3a7468,487d68,3ae618 |
| 5 Material semantics | PASS | Distinct modes6/2, queue/options/mip writes and actual GS masks |
| 6 Mesh ownership | PASS | Mandatory tag2/source material binding through391d38/391690 |
| 7 Vertex interpretation | PASS | Source52→runtime48→cache64,RGBA/UV/control; normal-use scope |
| 8 Texture binding | PASS | Exact primary GXI names→loader→mesh handles→texture-state consumer; live format/CLUT unknown |
| 9 Alpha test | PASS | tree GREATER64/KEEP; treeblend and object disabled |
| 10 Alpha blend | PASS | ABE and ALPHA selectors, source-alpha equation separated from stored file alpha |
| 11 Depth behavior | PARTIAL | ZMSK and ZTST proved; ZTE/FRAME and selected live inheritance not captured |
| 12 Draw order | PASS | Ascending buckets in one31cd98 drain; no global order or distance-sort claim |
| 13 Geometry processing | PASS | Authored strips with ordinary transform/clipping, no plant generator |
| 14 Camera dependence | PASS | No specialized billboard in handler/cache/selector0; ordinary matrices/culling remain |
| 15 LOD relationship | PARTIAL | No shader-specific transition found; complete hierarchy/live active-set predicates remain open |
| 16 Animation | PASS | Bounded absence of time/wind/scroll writes; no whole-game negative claim |
| 17 Render submission | PASS | Both modes share proved cache/queue/VIF1 producers, upload and embedded selector0 contract; live residency separate |
| 18 Turkey3 | PASS | A/256 visual faces/16 geometric components, mode2, bounded PC source mismatch |
| 19 ItalyS1 | PASS | B/64 faces, mode6, shared texture pixels, placement boundary preserved |
| 20 France control | PASS | C tolerance sensitivity; E strict24/24 geometric/material control; source redundancy retained |
| 21 Second treeblend course | PASS | France1 bush01 mode2, exact PC source correspondence |
| 22 Grass separation | PASS | Authored visual foliage kept separate from GRASS1 procedural detail |
| 23 PC portability | PASS | Source/material/texture/instance/LOD/runtime readiness independently classified |
| 24 Validation | PASS | Full regressions, offline repeat, compileall, handoff/integrity closeout |
| 25 Scope discipline | PASS | No PC renderer/SDK/assets/EXE/XML change, no next phase begun |

The two PARTIAL gates expose inherited live-depth and global hierarchy boundaries. They do not break the recovered principal material→mesh→texture/cache→mode-state→submission contract or imply pixel-accurate runtime parity.

## Closeout

The isolated copy contains the complete small historical fixtures; no proprietary input/SDK/HUD root is supplied. Unittest counts class-setup skips differently from pytest:247 executed methods include234 successes and13 skipped methods; eight additionally skipped classes generate21 reported skip entries. Pytest enumerates all270 methods,234 successful/36 dependent skips. Those skips are explicit external dependencies, not missing bundle JSON or suppressed errors.

Fresh post-analysis hashes matched the canonical ELF/CNF/PAK/000, six selected original PC DX/TXT files and four inspected original DXT files. The read-only SDK remained clean at4244fa0c4d878523c9947f54816bf377cdfb2589; PC renderer paths had an empty diff. No raw assets/executables/meshes were selected for Git or archive.

Precommit handoff review verifies copied payload SHA/size plus ZIP CRC/per-file SHA through the shared writer. The final archive is built after the scoped local commit; its actual source commit is `MANIFEST.json.source_commit`, and its external receipt covers the complete archive hash. A live PCSX2 PASS is not claimed.
