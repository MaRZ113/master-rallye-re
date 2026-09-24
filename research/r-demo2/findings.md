# R-DEMO2 cooker and cache reconstruction

Status: **MORE WORK NEEDED**. The user supplied new demo runtime observations and clean DXT/DX pairs. All supplied binary inputs remain ignored under `.research-output/r-demo2/input/`; only metadata and derived findings enter Git.

- **CONFIRMED_BY_RUNTIME + CONFIRMED_BY_BYTES:** for the tested Trooper `Black-tga.gxi`, original, offline-converted and clean runtime-regenerated DXT are all 1,044 bytes with SHA256 `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82`.
- **CONFIRMED_BY_RUNTIME (human report):** 8.4.1 visibly cooks GXM in memory with persistent model caching disabled on the observed path. Its Debug window names model cooking stages. The previously documented Trooper GXM-live matrix remains build-specific.
- **CONFIRMED_BY_RUNTIME (human report):** in 9.3.1 a missing DX is regenerated from present GXM and written to disk; a present DX can load when GXM is absent. The observed `complete.gxm`-only load generated `complete.dx`; `wheel.gxm`-only generated `wheel.dx` and showed wheels, while `wheel.dx`-only also showed wheels. The visual wheel resource remains separate from wheel physics. No visible Debug window was observed in 9.3.1.
- **CRASHED_IN_RUNTIME (human report):** the isolated `$chull` position-only candidate crashed both demos. This does not disprove `$chull` collision provenance; no second hull edit should be made before the crash stage and source dependencies are identified.
- **CONFIRMED_BY_BYTES:** the supplied 9.3.1 original and one regenerated `car.dx` are both 124,568 bytes but have different hashes. Render topology, colors, UV, local/global indices and raw draw/material bytes match. Render positions/normals and collision/bounds floats differ at tiny scales. Secondary tag101 descriptor sequences also differ (including per-face membership changes in A), so the conservative comparator returns `UNRESOLVED` rather than asserting complete semantic equivalence. See `dx-regeneration.md`.
- **CONFIRMED_BY_CORPUS + same-build regenerated artifact:** 9.3.1 Trooper GXM `$chull` points map numerically to regenerated tag101-B and AABB helper. This removes the former retail cross-build caveat; see `gxm-to-tag101.md`.

Repeated 9.3.1 Trooper car.dx rebuilds A and B are **BYTE_IDENTICAL** (SHA256 `8238078c40f7b419b2f3cc3a14f4511f1cdb6a8bce00f3589a39fbfcde32d5b1`), matching the earlier single regeneration. This supports deterministic output for the two tested runs; see `rebuild-determinism.md`.

A targeted read-only xref audit found paired GXM cache-status and fallback functions in both EXEs, with an unresolved condition selecting `Caching disabled.` versus `Cached model out of date...`; see `targeted-cache-xrefs.md`.

A newly supplied 9.3.1 custom GXM cooker output changes exactly one compiled render position by +0.15 on DX Y and recomputes marker-1339, while normals, render topology, raw draw/material and tag101 remain byte-identical (**CONFIRMED_BY_BYTES**). The user subsequently confirmed that the custom DX loads without GXM and the edit is visible (**CONFIRMED_BY_RUNTIME**). See `source-edit-oracle.md`.

Pending primary runtime evidence: DebugView for both builds, ProcMon cache hit/miss/file order, cache invalidation, and the `$chull` crash stage. No course reverse engineering, executable patch, retail-writer change, push or merge was performed.
