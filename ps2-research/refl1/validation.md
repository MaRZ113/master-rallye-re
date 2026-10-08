# Validation and acceptance

## Repository / provenance

Starting HEAD=fa32b51e2036f7c44e41f6382225d29b58577f25; clean master, ahead5.
No branch/worktree creation, checkout, reset, push or PC deployment occurred.
All intended edits are ps2-research source/tests/docs/compact metadata plus its
README index. Raw data is ignored. Course SDK retained clean HEAD
4244fa0c4d878523c9947f54816bf377cdfb2589 on its existing reference branch.
PC renderer/proxy paths have no diff against starting HEAD.

All four canonical SHA256 and sizes were freshly checked at preflight and again
at closeout. Selected original PSM/GXI payloads have independent PackFS range,
compressed/decoded hash provenance. Embedded five-MPG hashes were recomputed.
No original file was modified; no alternate corpus substituted.

## Automated results

| Check | Result | Scope |
|---|---|---|
|Focused REFL1 unittest|PASS20,0skip|Synthetic equations/grammar, original PSM/GXI/ELF checks|
|First sandbox full unittest|FAIL environment:6errors,196run|WinError5 on temporary/link protection fixtures; no PS2 semantic failure claimed|
|Permitted full unittest rerun|PASS196,0skip|PackFS,UI1/UI2,CDELTA1,AMBIENT1,GRASS1,WATER1,REFL1|
|Full pytest|PASS196 +259subtests,0skip|Same canonical/PC/SDK/HUD inputs; no weakened tests|
|Compileall|PASS|tools/tests; newly added packaging tool checked at closeout|
|git diff --check|PASS|Tracked changes and final staged review|
|Independent runtime capture|NOT_PERFORMED|No trustworthy running PCSX2 session; synthetic evaluation is not runtime PASS|
|Isolated handoff unittest|PASS184run,16skip|No external corpora; class/per-test skips explicitly reported|
|Isolated handoff pytest|PASS171 +160subtests,25skip|No external corpora; pytest expands class skips into individual tests|

A working handoff includes all REFL1 compact evidence, tools/tests, four small
UI2 JSONs and the two required WATER1 metadata dependencies. Original files,
coordinates, images, ELF dumps and Ghidra projects are excluded. The archive
manifest/receipt verifies every payload, source commit, size and SHA256.

## Acceptance matrix

| Gate | Status | Evidence / boundary |
|---|---|---|
|1 Git discipline|PASS|master, scoped edits, no push/reset/worktree|
|2 Corpus provenance|PASS|Four hashes/sizes before/after; canonical ELF/PackFS|
|3 Vehicle selection|PASS|Tata/Kia paint meshes and same-model carflat control|
|4 Material ownership|PASS|Real tag2 strips, exact material offsets, classifier fields|
|5 Texture resources|PASS|Nine selected resources; principal four roles separated|
|6 Environment source|PASS|Static input + framebuffer writer -> actual shared target consumer|
|7 Dynamic lifecycle|PARTIAL|Reset/enable/cache/writer/consumer proved; exact live VRAM allocation and release/reset bodies open|
|8 Reflection math|PASS|Normal/matrix interpolation/product/scale/bias original VU operations|
|9 Coordinate ownership|PASS|Object cache/current-retained rule and camera matrix setters traced; live w remains explicit input|
|10 Painted body|PASS|Tata/Kia mode3, mixed source, concrete two-pass contract|
|11 Glass/windscreen|PASS|Mode20, static highlight, alpha primary/depth masks|
|12 Chrome/trim|PASS|Selected chrome source replaced by carshiny; bounded no distinct shader claim|
|13 GS state|PARTIAL|TCC/TFX/ABE/FIX/ATE/ZTST/ZMSK proved; inherited full draw state not captured|
|14 VU/packet|PASS|Shared upload independently linked, CPU selector/strip/state/DMA; live residency UNKNOWN|
|15 Cross vehicle|PASS|Different genuine Tata/Kia payloads/geometry, same shader contract|
|16 PC comparison|PASS|Native NORMAL/texture-stage behavior separated from proxy REFLECTIONVECTOR experiment|
|17 Offline reconstruction|PASS|Bounded inspect/resources/coordinates/contract; no invented target simulator|
|18 Runtime honesty|PASS|NOT_PERFORMED explicit; live frame/VU/FCSR unknowns retained|
|19 Portability|PASS|Material/image/math/timing interfaces documented; no implementation|
|20 Regression|PASS|Full196/259subtests, compileall, diff-check, source/reference checks|
|21 Scope|PASS|No renderer/SDK/assets changes or next phase begun|

**PS2-REFL1 STATUS: COMPLETE at static/executable contract level.**
Main material -> source -> normal coordinates -> texture/pass -> CPU/VU-compatible
submission chain is specified and reproducible with explicit inputs. Partial
lifecycle/full-live-state gates are bounded closeout questions, not disguised
runtime proof. RUNTIME_VALIDATION: NOT_PERFORMED.
