# R-DEMO findings and continuation status

Status: **R-DEMO historical baseline; continued in R-DEMO2**. First-pass Trooper 8.4.1 results remain recorded here. Clean DXT bytes, 9.3.1 DX regeneration and the crashing `$chull` experiment are now documented in `research/r-demo2/`; full DebugView/ProcMon traces remain pending.

## Corpus and source formats

- The active worktree is `research/r-demo-pipeline`; the separate `master` tree and authoritative corpora were not edited.
- Three external corpora were hashed: demo-8.4.1 3,898 files / 298,491,020 bytes; demo-9.3.1 2,494 / 206,861,293; retail 7,716 / 1,168,251,134. Manifests preserve `corpus_id` and `relative_path`.
- GXI/GXB/GXP strict image structure has corpus-wide results; one September test GXI is malformed. 1,450/1,483 same-build GXI/DXT pairs reproduce complete bytes; 33 nonmatches are September fonts. September CarSheet GXB matches TGA pixels. Thirty-one November GXP images reproduce 146 DXT tiles byte-identically.
- GXM header counts pass 109/109 files. The material/geometry prefix is parsed in 80 files, with 102,636 indexed records; 29 post-header variants remain opaque. Trooper sidecars match GXM materials/mesh spans. November Jump `$chull` source geometry numerically matches retail Jump tag101 to float precision after an axis transform (**CONFIRMED_BY_CORPUS**, cross-build comparison).
- Demo 8.4.1 contains source-era course GXM, including France1 and Italy1; these are comparison oracles for a future R5T phase. No full course reverse engineering was started.

## Human runtime evidence: demo-8.4.1 Trooper

The user supplied first-pass in-game observations; see `runtime/loader-matrix.md` and `runtime/gxm-live-loading.md`. A structurally identified Vector C position edit visibly changed the vehicle body (**CONFIRMED_BY_RUNTIME**). For the tested path, `car.gxm` is required for race body and primary collision, `complete.gxm` for the presentation/menu model, and `wheel.gxm` for visual wheels (**CONFIRMED_BY_RUNTIME**). Removing the corresponding DX while retaining GXM caused no visible difference; the DX-only cases did not restore these visuals. Wheel physics persisted when visual wheels were absent. These results do not show whether any DX was opened, read or used by another subsystem. They do not establish behavior in demo 9.3.1 or retail.

## Continuation tools and static evidence

- `tools/scanner/r_demo_texture_compare.py` performs an original/offline/runtime three-way comparison using the shared GXI converter. `demo-8.4.1:DataGx/Vehicles/Trooper/Black-tga.gxi` reconstructs the original `black-tga.dxt` byte-identically (SHA256 `c8af53e3c1ea06c42178b3e1988dff0b3c64f150b722cba6bdd0450dc1357f82`). A clean runtime-generated file was later supplied and is byte-identical; see `research/r-demo2/dxt-regeneration.md`.
- An isolated Trooper `$chull` candidate translates 36 exclusive source Vector C positions by +0.4 source X. It changes 126 bytes only inside those float fields, reparses, and is stored under ignored scratch (SHA256 `0425e1636bc83844da241d48e30fedae2d48aff024cb4f1e329506ac64b1e699`). Human testing later reported a crash in both demos (**CRASHED_IN_RUNTIME**); see `research/r-demo2/chull-crash.md`.
- `tools/runtime/demo_debug_capture.py` can inspect standard Win32 child controls and capture appended text to ignored UTF-8 logs. The user later attempted the Win32 helper by PID/title/list-windows without readable output; DebugView is now the preferred fallback. Window/control details remain unknown. `tools/runtime/demo_debug_classify.py` recognizes only observed/executable-confirmed templates; see `runtime/debug-capture.md` and `runtime/debug-message-catalog.md`.
- Targeted PE32 xrefs in both demo EXEs locate GXI/DXT branch functions and Debug literals for reading GXI, saving a cached texture, and loading cached DX texture (**CONFIRMED_BY_EXECUTABLE**). The 8.4.1 logging sink contains an `OutputDebugStringA` call. Actual per-resource file order and active output channels still need live traces; see `runtime/targeted-exe-xrefs.md`.

## Remaining gates

1. Repeated 9.3.1 DX rebuild determinism and a controlled visible GXM edit through the original cooker.
2. DebugView capture in both demos, including the final stage before the `$chull` crash.
3. ProcMon correlation for actual texture/model cache hit, miss and fallback order.
4. Cache invalidation tests and targeted EXE cache-flag analysis.
5. Keep the retail writer unchanged until original-cooker policy is supported by differential runtime evidence. No push or merge is authorized.

The retail DX parser still does not decode the demo draw grammar. The 29 opaque GXM variants are outside this loader-focused continuation unless needed for an isolated test.
