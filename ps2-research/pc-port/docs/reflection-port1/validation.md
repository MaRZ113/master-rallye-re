# Focused validation

| Check | Result | Scope |
|---|---|---|
| Baseline Win32 Release | PASS | Independent serial MSBuild; unmodified Git-object staging |
| PS2 Win32 Release | PASS | Independent serial MSBuild; final source/test hashes match staging |
| Baseline CTest | 24/24 PASS | Existing native baseline tests |
| PS2 CTest | 26/26 PASS | Baseline + foliage extension + reflection contracts |
| Focused Python | 25/25 PASS; 0 FAIL, 0 SKIP | Existing integration + tree lock + reflection checks |
| Optional original-image Reset case | PASS | MRR_REFLECTION_TEST_GXI set to verified private GXI |
| Interface generator | PASS | Two repeat executions per variant; exact locked hashes; no initial rewrites |
| Proxy verification | PASS, both | Win32 exports/PE and forwarding checks; not runtime validation |
| Compileall | PASS | Port renderer/tests/tools/overlay |
| Diff check | PASS | No whitespace errors |
| Frozen renderer / SDK | PASS | Clean tracked and untracked source state; exact Git tree |
| Asset provenance | PASS | Four canonical PS2 hashes; selected original PC DX and EXE hashes |
| PILOT1.4 preservation | PASS | Previous archive/DLL and classifier/pixel implementation retained |
| Extracted handoff Python | 25/25 PASS | Packaged source/tests/evidence; external verified staging; no private corpus |
| In-game reflection / visual comparison | NOT_PERFORMED | User-controlled A/B required |

The reflection native suite covers opt-in parsing, unsupported mode/version,
material/layout/owner/resource rejection, current upload revisions, cached geometry
invalidation, one submitted draw and native HRESULT, partial SetTextureStageState
or SetTexture failure, exact restoration, failed-restoration retry with held COM
ownership, managed texture upload/caps/Lock/Unlock failures and release balance.
No render-target changes occur in the synthetic device.

Stock wrapper tests make no temporary writes or image allocations, including
after a failed Reset. Enabled Reset integration uses the verified local asset:
failed native Reset suspends the effect but retains mirroring; reset-echo cannot
resume it; successful native Reset uploads again; shutdown releases ownership.
The environment-dependent subcase explicitly prints NOT_PERFORMED when no
MRR_REFLECTION_TEST_GXI is supplied. It was executed and passed here; the source
asset is deliberately absent from the handoff. Other native tests use synthetic
data and require only the external locked renderer/toolchain.

ZIP verification passed repeated byte-identical serialization, member CRC,
complete checksum manifest round-trip and exclusion checks for original GXI,
PSM, DX, EXE and archive assets. Both proxy DLLs have separate verified hashes.
After packaging, all 25 Python tests also passed from an isolated extraction
using the external verified staged renderer. The four canonical PS2 file hashes
were checked again at closeout and remained unchanged.

Eight temporary-Git tests prove unrelated research commits are accepted while
committed renderer changes, index/worktree drift, untracked sources, wrong branch
and malformed locks fail closed. Ignored build files remain permitted.

An independent read-only source review found no concrete blocking defect in
native state ownership/restoration/Reset. Its enabled-Reset coverage concern was
closed with the final original-image integration test. This is code/test evidence,
not proof of live D3D8 admission or PS2 pixel parity.

Full repository and unrelated broad suites were not expanded. No PCSX2 session
or game launch was performed. Current source and DLL hashes are recorded in
build-report.json; handoff member hashes are in SHA256SUMS.txt.
