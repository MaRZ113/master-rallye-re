# R-CAM1-A3j.1 validation

## Scope

Static exact-build dataflow review only. No production source, game binary, Broker value, chassis, wheel, physics state, pause state, or scheduler ABI was modified. No DLL was built and no runtime session was run.

## Target verification

Verified available `D:\Game\Master Rallye\MRallye.exe` immediately before analysis:

- SHA-256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
- Size: `3,121,214` bytes
- PE32 / I386, timestamp `0x3C02695D`
- ImageBase `0x00400000`; entry RVA `0x001C4602` / VA `0x005C4602`

Ghidra 12.1.4 used a temporary project at `D:\CodexScratch\A3jGhidraProject`. Targeted decompilation and instruction review covered reset output, controller consumption, chassis setter, wheel-record cleanup, reset counter readers, and startup placement. No Ghidra project/database was created in the repository.

## Validation performed

- Parsed the new `transform-consumer-evidence.json` and updated `evidence-map.json` as JSON.
- Checked Markdown links in the new documents against repository-relative targets.
- Ran `git diff --check`; no whitespace errors were reported. Git emitted only existing CRLF/LF conversion warnings for already-dirty renderer source files.
- Confirmed the handoff archive contains only A3j.1 documents/evidence, not binaries, logs, or prior task source trees.
- Rechecked branch and HEAD: branch `master`, HEAD remained `676ed24b2d32543c3b9356ed359e280f2b36a309`.
- Preserved pre-existing dirty A3h/A3i renderer work; nothing was staged, committed, or pushed.

## Interpretation

The controller-to-chassis setter is confirmed statically; the reset-output-to-controller Broker relationship is not. Four wheel records receive bounded field cleanup, but wheel pose/suspension/contact and velocity invariants remain unproven. The phase is therefore `PARTIAL / EXACT_CONSUMER_GAP_IDENTIFIED`, not `NATIVE_RELOCATION_CHAIN_PROVEN`; teleport is not ready for runtime validation.
