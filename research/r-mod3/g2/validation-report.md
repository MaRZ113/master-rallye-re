# R-MOD3-G2 validation report

**Status: `READY FOR HUMAN GAMEPLAY TESTING`.** There is no owner gameplay test or G2 Broker capture in this checkout.

## G1 development baseline

The owner reports a complete T2 race with eight participants, seven AI, repeated physical CarID 8 in two participant slots, distinct DriverIDs, all participants finished, and eight results. This is owner-confirmed G1 runtime evidence. It is not a G2 runtime result. The exact historical G1 capture and candidate package identities were not supplied with this source tree, and historical G1 manifests remain unchanged.

## G2 native and package identities

| Item | SHA256 / value |
|---|---|
| Pristine retail EXE | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |
| G2 runtime DLL | `df6e6e002fbe98e237265c986eb7665d96c74f58106e257e3b550f83a0bd5fbb` |
| x86 DirectInput proxy | `bf0165d77cfd0430e0cd18f4397ddfa45ff09e5b48a3290db032c96a455b2dc3` |
| Generated 19-operation plan | `877c487213bab9f5be501558a6adc3999f59680d2227f6fdbb98015968c007df` |
| Candidate ZIP | `066ffc4577e3af69559e584a5b8f5e9c171b65d74950c09ce55bf40612d7164e` |
| Operation count | 19 (17 preserved G1/F3 + 2 G2 player-car sites) |

The candidate manifest pins the retail EXE and labels the package `READY_FOR_HUMAN_GAMEPLAY_TESTING`. It explicitly says it is not human-runtime-qualified. G1's older plan hash and generation-time status are not rewritten by G2.

## Automated checks

The following were rerun after the G2 tests and documentation were updated:

| Check | Result |
|---|---|
| Focused native-plan suite `PYTHONPATH=src python -m unittest discover -s tests/synthetic -p test_r_mod1_native_plan.py -v` | 21 passed, 0 failed |
| Full synthetic suite `PYTHONPATH=src python -m unittest discover -s tests/synthetic -q` | 652 run; 651 passed; 0 failed; 1 opt-in Windows suspended-child test skipped |
| G2 C++ core harness `tools/r_mod1_core_tests.ps1 -G2` | 344 checks, 0 failures |
| `python -m compileall src tools tests` | PASS |
| `git diff --check` | PASS; only Git LF-to-CRLF notices for pre-existing dirty files |
| G1 candidate verifier | PASS; 17 operations and original G1 package hashes reproduced |
| `build_rmod3_g2_candidate.py --verify` | PASS; exact retail identity, all package hashes, ZIP file set/content, DirectInput export audit, regenerated plan |
| Independent deterministic G2 rebuild | PASS; runtime DLL, DirectInput proxy, native plan, package manifest, profile/resource file set, and ZIP identities match |
| Candidate bootstrap harnesses | PASS; DirectInput 6/6 named+ordinal, one-time initialization and invalid-host rejection, host-qualified 15-op preflight, runtime-image difference diagnostics |

The test outputs and candidate/build evidence are included in the source-only review archive. MSVC printed the existing `LNK4104` export warnings for COM-style DirectInput proxy exports; the PE export audit still found all six expected names and ordinals. A native G2 gameplay run remains a human gate.

## Qualification boundaries

- Forced and random modes are implemented for Quick Race player 0; neither has been tested in-game in G2.
- Manual left/right navigation behavior is not statically attributed to a precise input owner. See [native-ownership.md](native-ownership.md); the handoff requires display-to-race identity comparison.
- No add-on IDs, Vehicle SDK, other-mode player overrides, or new AI behavior are part of this candidate.
- Bootstrap/build harness success is static/package evidence, not proof the proxy and game behave correctly in an owner's Windows runtime.
