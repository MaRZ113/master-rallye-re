# Validation and proof boundary

| Check | Result |
|---|---|
| Branch/worktree | master, primary re-general; unrelated edits preserved |
| Frozen renderer | exact tree e33386bcf682db6983380c499e4928726c758fe0; zero source changes |
| Immutable staging source | 0bddf7c7bc5e95831f98714ff6231da05ab073ea |
| Baseline Win32 Release | PASS, serial incremental MSBuild |
| Baseline CTest | 24/24 PASS |
| PS2-enabled Win32 Release | PASS, serial incremental MSBuild |
| PS2-enabled CTest | 31/31 PASS |
| Port Python unittest | 123/123 PASS, zero failures/skips |
| COMPLETE/R5900 metadata and synthetic tests | 18/18 PASS |
| Frontend source/layout/native metadata tests | 12/12 PASS |
| Race partition source/control tests | 5/5 PASS |
| Compileall | PASS |
| Available default-interpreter pytest | BLOCKED: C:\Python315\python.exe: No module named pytest |
| Proxy exports | Both PE32/Win32 proxies PASS; existing three exports retained |
| Interface generator | Both variants, two executions each, deterministic/seam preserved |
| Exact patch application | PASS, no fuzzy matching |
| R5900 verification | 2032 words,197 compact probes,51 lamp probes; original ELF/EER/Rabbitizer |
| PC native verification | Canonical SHA,31 original instruction windows and vtable PASS |
| Source integrity closeout | Canonical4PS2 inputs,26COMPLETE+6CAR hashes,29private model artifacts PASS |
| Course SDK | Clean unchanged4244fa0c4d878523c9947f54816bf377cdfb2589 |
| New native runtime / screenshots | NOT_PERFORMED; user A/B pending |
| COMPLETE live owner/suppression | BLOCKED, exact missing join documented |
| Lamps/glow | Research only; no implementation |

Final DLL hashes:

```
baseline 011dd9a94155d216d0c0dde28e0af97f5b72226aae5be97016f2d767ebdf7138
ps2      1f7c99dae931955f2c6441f5959aee7a11fa405eb1f8f935c81dcedd6aed2c79
```

The baseline hash equals the accepted previous release. Existing grass/shrubs,
water, Mode4/MSAA capture, Reset, HUD cache, Free Camera and wrapper tests pass.
This is automated regression evidence. New live Reset/MSAA/menu rotation/race
restart behavior still requires user evidence for this DLL. Mock tests cannot
establish pixel parity or runtime source identity.

New native tests cover exact registry multiplicities, native index reordering,
unknown faces, bad indices/nonfinite positions, missing/recreated generations,
Reset mismatch, race/context/state rejection, Stock and version defaults,
contiguous full coverage validation before submission, each face once, first
failed native HRESULT/no replay, state restoration between adjacent runs,
partial state failure even when a failed write mutated native state, and bounded
frontend diagnostics. Existing Mode4 transaction tests cover texture references,
capture/target formats, native restore failures and Reset/device-loss semantics.

The first exploratory COMPLETE format probe used an unavailable Ghidra iterator;
it failed before execution, was corrected, and the final probe/byte verifier passed.
Builds were repeated incrementally after actual source/test/diagnostic corrections.
No broad unrelated fixes or software installation were performed.

Standalone archive verification and extracted-test results are recorded separately
in `handoff-validation.json` and SHA256SUMS; they are not a runtime validation.
