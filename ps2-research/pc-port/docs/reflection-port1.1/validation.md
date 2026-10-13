# Focused validation

| Check | Result |
|---|---|
| Frozen Git objects, renderer tree and worktree | PASS; unchanged |
| Exact staging patch application | PASS; fresh final stage |
| Generator twice per variant and locked outputs | PASS |
| Independent baseline Win32 Release /CTest | PASS;24/24 |
| Independent PS2 Win32 Release /CTest | PASS;29/29 |
| Python port tests | PASS;44/44;0fail/0skip |
| Proxy export/PE verification | PASS; both artifacts |
| Compileall/diff-check | PASS |
| Handoff manifest/CRC/repeated serialization | PASS |
| Extracted handoff Python tests | PASS;44/44; external verified staging, no private assets |
| Original local GXI and object asset Reset tests | PASS; explicit private inputs |
| Classifier function-byte witness | PASS; unchanged from previous built source |
| Synthetic capture/state/lifetime/error coverage | PASS; native mock GPU |
| Previous Mode1 live draw/restoration | Technical PASS from supplied audit/F10 |
| New Mode4 live driver CopyRects | NOT_PERFORMED |
| New appearance and PS2 parity | NOT_ESTABLISHED |

Native coverage tests selected-only COLOROP/texture masks, defaults, invalid
requests, same-count/sourcehash/owner/resource negatives, one draw/HRESULT,
attempted-write failures and retained-reference repairs. Mode3 no-GXI/no image
allocation and real Reset versus echo are tested. Original corpus-dependent
image subcases ran here with explicit verified local paths; without these paths
they print NOT_PERFORMED rather than fabricating an integration PASS.

Capture tests exercise42scalar/texture slots plus target/depth/viewport/stream:
read failures, apply failure positions, restore retries, COM references, implicit
viewport/UP stream effects, frame cache, source/caps/budget rejection, copy/draw
failures, S_OK/null outputs and null canonical COM identity. These validate
transactions and policy on native mocks, not GPU color output or visual parity.

An intermediate PS2 run failed the existing reflection_contracts getter case:
an unconditional repair consumed baseline pending state before logical read.
New observation hooks now use native_states_pending() for the PS2 extension
only. Final original reflection_contracts passes; no baseline test was weakened.
The final two-file null-identity guard received an incremental PS2 rebuild,
all29CTest and44Python tests, exports and repeat generator checks. The baseline
source/DLL was unchanged and its separate24CTest result retained.

The two old handoff archive hashes and all four course-layer source hashes are
recorded in build-report.json. No broad unrelated suite, original executable
analysis, automatic game launch, deployment or push was performed.
