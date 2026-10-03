# R-AI1 validation

Evidence labels retain their scope: **CONFIRMED_BY_EXE** for static selection
and consumers, **CONFIRMED_BY_CORPUS** for stock records/resources/physics,
**SOURCE_EVIDENCE** for the historical frontend capture, and **UNKNOWN** for
this phase's actual mixed-class race.

Baseline before research edits:254 synthetic tests PASS;
`python -m compileall src tools tests` PASS; `git diff --check` PASS.
Baseline logs stay ignored under `.research-output/r-ai1/`.

Final complete suite: **269 tests PASS** (254 baseline +15 new synthetic tests).
`python -m compileall src tools tests` PASS; `git diff --check` PASS.
The project README prescribes the synthetic unittest suite; no material/Blender
or other implementation was touched requiring additional subsystem tests.

## Native selector verification

Latest Ghidra12.1.4 + installed ghidra-bridge Python executed the final actual
x86 bytes through `EmulatorHelper`: **1503/1503 PASS**. Cases cover ten possible
T3 choices, ten driver values, three AI slots, all five possible pool-tail
scratch values, and each failed retained-argument guard. Checks cover the live
frame except the permitted chosen-ID local, displaced PUSH argument, all
general registers and the modeled CF/PF/AF/ZF/SF/TF/IF/DF/OF flags. EAX/ESP retain
the displaced stock instruction effects. Sleigh models flags separately and
omits reserved bit1 in its PUSHFD packing; this is an emulator boundary.
No game execution or project save occurred.

Reproduction:

```powershell
& '<ghidra-bridge Python>' tools/scanner/r_ai1_emulate.py --install '<latest Ghidra>' --project _ghidra_project --candidate .research-output/r-ai1/human-candidate/MRallye.exe --output .research-output/r-ai1/selector-emulation-final.json
```

An earlier static prototype guarded on exclusion argument slots that had become
scratch; the final instruction audit found this before handoff. That prototype
was never game-tested and is not a supported profile. The final55-byte selector
uses only retained firstAI/count/class arguments and ESI. Only the final hash
in [intervention](intervention.md) is accepted. The final emulator explicitly
uses scratch values9 and20/22/23/24/21 at the corresponding old argument slots.

## Integration and oracle

The final source-to-candidate build is reproduced twice byte-identically, with
identical manifests. Inverse verification restores exact pristine; unrelated
byte changes and patched-as-source inputs reject. Exact-profile import, basename/
size/hash gates and vendor-change rejection pass. Original external files remain
hash-identical. A historical frontend JSON/raw pair re-parses identically via
the audited parser and is rejected as mixed-runtime evidence. This tests capture
binding without pretending to have a race capture.

Fresh protected LandCruiser/WildCat car, complete and wheel parsing succeeds:
**6/6 DX PASS**, with body collision sections present. Protected pristine EXE,
Data.sma and vehicles.xml hashes remain unchanged. This proves stock corpus
compatibility, not gameplay contacts. Ignored final evidence reports:
`selector-emulation-final.json`, `static-integration-final.json`,
`final-synthetic.log`, `final-compileall.log`.
Synthetic oracle tests reject wrong count, IDs, classes, driver/type, wheels,
physics, lifecycle gate, stale/recovered/other-build snapshots, ambiguous paths,
aliases and JSON/raw edits. A matching synthetic snapshot returns state-only.

## Human runtime status

**NOT RUN / UNKNOWN.** No mixed-front/mixed-race/mixed-return captures have been
provided. AI movement, intended runtime collision, HUD/results and stable exit
remain pending. Do not record MIXED-CLASS OPPONENTS CONFIRMED_BY_RUNTIME yet.
