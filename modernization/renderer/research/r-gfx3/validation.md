# Final-fix automated validation

READY_FOR_SHORT_RETEST, not CLOSED. Starting clean research/general-re HEAD2e6eaea; prior implementation097bb22. All edits are under modernization/renderer; frozen phases/retired worktrees/game files untouched.

- Win32 Release build via tools/build.py: PASS; both native_contracts and visual_contracts PASS.
- Python unittest discovery:44 PASS, no skips.
- python -m compileall modernization/renderer: PASS.
- PE verifier: valid PE32/I386, exports Direct3DCreate8@5, ValidateVertexShader@3, ValidatePixelShader@2; no d3d8 self-import.
- DLL SHA256: 44a76a3a3e96573393b7ee1e492734b62d9c2ef8baae369711ce7c419615efef; size1016320.
- git diff --check: PASS. Generated ABI remains16/97 complete and deterministic.

Native policy coverage: MAG LINEAR/POINT unchanged even when MAG caps supported; stage0 eligible MIN, MIP/stage1/POINT, caps and getters; failed setters/native retries and Reset. Source90 vs45 vsunknown70/89.98/90.02 at both observed aspects and synthetic portrait; default-off/unknown-build/module/caller/ortho/nonfinite/off-center;80 output, preserved aspect and14 exact float bits. Shadow and forwarding regression contracts pass. Actual known-EXE callsite positive FOV behavior still requires the human game retest.

Compiler warnings from pinned anonymous vendor unions and mock unused parameters remain unchanged. Build identity is recorded per binary; no deterministic byte-for-byte rebuild claim is made.
