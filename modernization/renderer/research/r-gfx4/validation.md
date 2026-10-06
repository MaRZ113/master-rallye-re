# R-GFX4 automated validation and scope

READY_FOR_HUMAN_RUNTIME for Stock classifier A/B. Visual prototype BLOCKED_BY_CLASSIFICATION; no new human R-GFX4 pass is claimed. Starting clean research/general-re HEADd46ebdce5477ebfd08e049c25cea2801572fbb97. No new branch/worktree or push. Only modernization/renderer changed; frozen R-GFX1/R-GFX2, other reverse files, corpora, game installation and retired trees remain unmodified.

- Win32 x86 Release via tools/build.py: PASS.
- CTest native_contracts, visual_contracts, classifier_contracts:3/3 PASS.
- Python unittest discovery:55 PASS, no skips.
- python -m compileall modernization/renderer: PASS.
- PE/export/import verifier: valid PE32/I386; Direct3DCreate8@5, ValidateVertexShader@3, ValidatePixelShader@2, no d3d8 self-import.
- git diff --check: PASS; ABI generation16/97 remains deterministic.

DLL SHA256: b3a52962d3bb56678690f92ce4d1f7e97d4719dbdeecdd60f0847fcde429902d. Size: 1036800 bytes. Product: modernization/renderer/.build-msvc/Release/d3d8.dll, ignored and not committed/deployed. Build identity is per binary, not a reproducible byte-for-byte rebuild guarantee.

Native new cases: static/moving/rotation-only tracks; same geometry/two instances; draw and four-wheel permutations; mutual-match ambiguity; generation reuse; cold Reset/epoch, no-race-frame scene boundary; fixed group capacity and saturated static group; immutable geometry identity excluding WORLD; exact-build/race/owner reasons; alpha/no-normal/disabled-env gates. DYNAMIC_ENV_OBJECT is explicitly not promoted to a vehicle. Config Stock/recognized-but-blocked/invalid/unknown-build cases pass. Actual native trace files expose additive R-GFX4 fields and Stock reflection provenance. Existing R-GFX3 AF MIN-only, MAG/MIP/stage1, FOV preview exclusion/exact Z, shadow, failures/getters/Reset and full COM forwarding tests pass.

Python new cases: source color/alpha interpretation, constant/variable correlations, rank-deficient fit, malformed arrays; pinned header constants/FVF strides; legacy/unknown/incomplete traces; material aggregation and recorded temporal fields; preserved wheel axle metric and Broker build rejection; native captured-field compatibility. A runtime-only positive vehicle identity and draw-local override/restoration are **not implemented or claimed tested**, because their gate is unsatisfied.

Static asset/parser results, synthetic tracker tests, prior human R-GFX3 observations and pending human R-GFX4 validation remain separate. Compiler warnings from pinned unions/mocks are unchanged. Threshold quality, tracker CPU cost in actual gameplay, real group count/unknown-state prevalence, static-world false positives and scene-transition coverage need human Stock capture.

Reproduce analysis using protected external inputs: analyze_vehicle_lighting_inputs.py <retail Vehicles root>; analyze_vehicle_draws.py <F10 files>; validate_vehicle_correlation.py <Broker JSON> <matching-process F10>. Tools read inputs and print JSON; they do not edit input assets/logs. Output input hashes are retained in the tracked summaries.
