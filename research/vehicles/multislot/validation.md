# R5V-I.0 validation record

## Baseline

The full synthetic baseline before adding I.0 tests was **350 tests passed**.
The I.0-focused test module covers sparse identity mapping, record and
RaceTest layout, AI pool membership, native append/exclusion control flow,
unlock/audio identity, overlay generation, code-cave bounds, 39 initializer
and 11 consumer relocations, non-overlapping patch ranges, exact inverse-to-H.2
and fail-closed retail hashes.

Final closeout run: **363 tests passed, 0 failed, 0 skipped**. `compileall`
completed successfully. Candidate verification returned `VERIFIED`, the
Vehicle Select overlay returned `VERIFIED_EXISTING`, the 143-resource runtime
package returned `VERIFIED`, and `git diff --check` exited 0. The retail
executable and unpacked retail/demo corpus remain external read-only fixtures.

## Deterministic candidate

| Artifact | Profile / source | SHA256 | Size |
|---|---|---|---:|
| Source EXE | pristine retail | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` | 3,121,214 |
| Parent EXE | H.2 `mode-aware-natural-t1-id26` | `de5e81c0b126619574834f25ac941cd491139235fd2f89086d8e125f063dcac9` | 3,121,214 |
| I.0 EXE | `i0-two-addon-slots-id27-t2-diagnostic` | `50ff267d2758c1ff894d91bcdafd7dba4a2fa278d678a075e7767120727abbea` | 3,121,214 |
| I.0 scene | `T2_Car8` diagnostic overlay | `0b8c61efd2959a5b3b5dcef0d3810c2b445e021c465816627e87b9e3da2b4490` | 155,756 |

Candidate rebuild and inverse verification restore the exact H.2 parent. The
EXE has 81 non-overlapping operations. The local staged runtime package has
143 inventoried resources (including the qualified H.2 Data.sma) and passed
automated package verification. No proprietary candidate, game resource,
save, capture, screenshot or package file is tracked.

## Evidence grade

Static Ghidra/PE mapping and byte-level patch verification are separate from
synthetic emulation, package integrity, and human runtime. At this point the
first three have a prepared/automated path; I.0 human runtime is pending and
I.1 real-vehicle qualification is blocked by the absent independent payload.
