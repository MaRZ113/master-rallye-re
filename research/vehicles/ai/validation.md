# R5V-H.0 validation record

## Starting point

* Checkout: `master-rallye-re-vehicles`.
* Branch: `research/vehicles`.
* H.0 correction base: `bd7caf4` (`feat: add ID26 AI materialization proof`).
* The first H runtime run is recorded as a failure in
  [runtime-results.md](runtime-results.md); this correction does not promote
  it to a pass.

## Preserved stock-pool evidence

Ghidra 12.1.4 analysis of exact pristine retail `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
found two `FUN_00458090` callers in `FUN_0047B780`: split-screen at
`0x0047B93D`, starting AI at slot 2, and single-player at `0x0047B96E`,
starting AI at slot 1. No natural pool edit is part of H.0.

At the publication seam `0x00458428`, the live values support a minimal guard:

| Guard/input | Value | Evidence |
|---|---:|---|
| ESI, current AI slot | 1 / Car1 | Re-derived from the chooser loop and both mapped callers |
| EBP, exclusive end slot | 4 / Car0..Car3 | `start + active AI count` at `0x0045836E` |
| class argument `[ESP+0x8C]` | 0 / T1 | Read for pool construction; no write to this slot in the analyzed function |
| selected CarID local `[ESP+0x14]` | normal chooser result, replaced with 26 on guard match | Read and used at the publication seam |

The chooser frame is 0x80 bytes below its incoming return address at the
publication point. The driver-selection helper preserves ESI and EBP and
returns the stack to the expected baseline before the hook. The player
exclusion and second-exclusion inputs are copied/reused as scratch and are not
late guard inputs. The caller return address is unnecessary after the call
graph, slot, end-slot, and class are checked. These claims are grounded in the
latest Ghidra listing and raw retail bytes; see the ignored
`.research-output/vehicles/ai/ghidra-h0-stack-evidence.txt`.

## Corrected candidate

* G.1 base: `722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7`.
* G.2 profile-0 base: `636422d0a21b5f75abd3d6233ab0fcbae26cb0dce79c1a8d40d60ad2e8ca488f`.
* H.0 candidate: `dc821c096dea1db00c91ddf41e85cfac1f5369eaf56bd821ed0b904cbe246e13`, 3,121,214 bytes.
* Patch manifest: `68ee11ae153daf4a48974676dd9f1bb31245cb774a4beee53ec165134d537fca`.
* Hook: VA `0x00458428`, file offset `0x58428`, retail bytes
  `8B44241450` replaced by a five-byte relative jump.
* Stub: VA `0x0068E690`, file offset `0x28E690`, 50 bytes, ending at
  `0x0068E6C2`; original cave bytes were zero-filled.
* Stub guards: ESI==1, EBP==4, and class==0. Match changes only
  `[ESP+0x14]` to physical ID26, then replays `MOV EAX,[ESP+0x14]; PUSH EAX`
  and resumes at `0x0045842D`.
* The stub does not require player CarID 0, caller return address, or either
  exclusion argument. It does not change `NumCars`, `CarClass`, `DriverID`,
  Car0/Car2/Car3, or natural pool membership.
* `.text` VirtualSize is `0x28D6C2`; `.rdata` begins at RVA `0x28F000`.
  The payload remains inside `.text` raw data and has no overlap with the G.1
  or G.2 payloads.

The corrected candidate was deterministically rebuilt and its candidate
manifest and patched ranges verified. Ghidra 12.1.4 decoded the hook and all
three guards from the output candidate in
`.research-output/vehicles/ai/ghidra-h0-candidate-evidence.txt`.

## Runtime package and checker

The ignored runtime package at
`.research-output/vehicles/ai/forced-id26-proof/runtime-package/` contains
the exact candidate, the verified G.1 resource profile, VehicleSelect XML
SHA256 `6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d`,
and 28 Mercedes asset files. It excludes generated PlayerState and backups.
The prelaunch verifier passed all five checks: EXE, Root layout, VehicleSelect
XML, Mercedes assets, and mode/audio profile. This verifies staged files, not
which root a launched process actually uses.

The capture checker requires `source.image_sha256`, `source.image_path`, and
`source.active_root`, each matching the exact H package. Its highest automated
result is `HUMAN_AI_CONFIRMATION_REQUIRED`; a wrong Car1 is classified
`FORCED_ID26_NOT_OBSERVED`, while executable/root provenance mismatches are
`RUNTIME_PACKAGE_MISMATCH`. It cannot claim visible rendering or gameplay.

## Synthetic/static verification

* Forced-stub x86 interpreter tests cover the positive Car1/T1/three-AI case,
  each rejected slot/count/class guard, changed player/exclusion values,
  unchanged DriverID, replayed instructions, and preserved control flow.
* Runtime-package tests cover missing/wrong VehicleSelect XML, wrong EXE,
  missing Mercedes assets, mismatched candidate identity, and staging without
  PlayerState.
* Broker-checker tests cover exact provenance, missing/mismatched source
  metadata, forced identity agreement, and incomplete state.
* Full-suite and compile counts are recorded after the final closeout checks.

## H.0.1 candidate build and package verification

From exact retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, both
profiles reproduce deterministically and pass `--verify-existing`:

| Profile | Output SHA256 | Forced hook | Randomizer |
|---|---|---:|---:|
| `ordinary-hardened` | `391d5d864699b6e945eed43fd8e7bc28b28639b24b222428ab79231e7cc3a819` | no | no |
| `forced-id26-ai-hardened` | `9255c9d7cb27336d0a5324bd193719c768f09f5bb7d37e30bab384031b0de0e7` | Car1 proof only | no |

Both separate runtime packages pass verification with 145 staged files, the
pinned VehicleSelect scene, and no generated PlayerState. Neither package
contains a DLL. The ordinary package reports no forced proof and no
randomizer, making it the stock-path hardened control requested for tests.
The forced package is reserved for the ID26 Results-name and hardening retest.

Final repository validation for this correction pass:

* `python -m unittest discover -s tests/synthetic -v`: **325 passed, 0 failed,
  0 skipped**.
* `python -m compileall src tools tests`: **passed**.
* Both candidate `--verify-existing` commands: **passed**.
* Both hardened runtime package verifiers: **passed**.
* `git diff --check`: **passed**.

## Corrected H.0 runtime status

The first failed H run remains a separate failure with unknown effective
resource root and Car0 ID. The corrected H.0 candidate was later human-tested
from its verified package. The supplied active-race capture confirms
`NumCars=4`, `NumPlayers=1`, and Car1 `CarID=26`, T1, DriverID8,
`CarType=Mercedes`, `WheelType=Mercedes`. The human confirmed visible model,
AI behavior, progress, finish, and a Results row. This is
**CONFIRMED_BY_RUNTIME** for the forced Car1 materialization path.

The initial H.0 Results row showed `GALOCAL UNKNOWN`. H.0.1 substituted the
already-selected DriverID as the group-`0x39` selector for AI CarID26 only;
the two later Results captures and human-visible names confirm that policy for
the tested rows. This H.0.1 behavior is `CONFIRMED_BY_RUNTIME`. H.1 uses a
separate fixed ID26 display identity and has not inherited that runtime status.

H.0.1 also composes neutral Loading->Attract and native StringList/XmlData
Dump guards. Human runtime confirms the forced-ID26 Results-name policy and
post-Results NULL StringList Dump survival. The XmlData guard and exact
Loading->Attract trigger were not isolated by that runtime test and remain
`UNKNOWN`. The separate ordinary hardened EXE remains available at
`.research-output/vehicles/ai/hardened-ordinary-no-randomizer/runtime-package/MRallye.exe`.
The H.0.1 handoff is historical; the current H.1 handoff is
[natural-t1-runtime-plan.md](natural-t1-runtime-plan.md).

## H.1 natural T1 candidate verification

The H.1 candidate builder composes exact retail through the verified ordinary
hardened G.1/G.2 base, then changes only the native T1 loop exit and the ID26
Results display branch. Static checks verify the exact source/base hashes,
original instruction bytes, native exclusion-body re-entry, preserved
publication hook, fixed Results string, zero-filled non-overlapping caves,
`.text` bounds, deterministic reconstruction, and inverse restoration.

The demo group-`0x39` extractor pins both input SHA256 values, selects the
verified group rows, rejects duplicate selectors or malformed pointers, and
records both demo Mercedes ID2 -> selector 2 -> `JOSE MARIA SERCIA` mappings.
Historical Stage 5/7 results independently list the Mercedes T1 crews used to
classify this selector association as a developer placeholder; see
[historical-driver-selector.md](historical-driver-selector.md).

The H.1 Results fix returns fixed display text for physical ID26 only. Other
AI keep stock CarID -> group-`0x39` lookup; human branches are untouched. The
helper neither reads nor writes native DriverID, and the native driver chooser
and participant publication remain unchanged. H.1 is
`STATICALLY VERIFIED / READY_FOR_HUMAN_RUNTIME`; it has not established
natural ID26 selection or visible Results text in a human run.

H.1 final verification:

* `PYTHONPATH=src python -m unittest discover -s tests/synthetic -v`:
  **341 passed, 0 failed, 0 skipped**.
* `python -m compileall src tools tests`: **passed**.
* `git diff --check`: **passed**.
* H.1 candidate `--verify-existing`: **passed**; candidate SHA256
  `e59895776dd53acb3ac4a25e1973c8de341da815b90407ec372b696be06d363a`.
* H.1 runtime-package verifier: **PASS**, 145 files, no PlayerState.
* Exact demo group-`0x39` data rebuild: **passed** for both pinned demo EXEs.
* H.0.1 ordinary and forced candidate verifiers: **passed**. The ordinary
  package verifier passed. Rechecking the forced package was refused because
  the human-tested package now contains generated `DataGame/PlayerState.xml`
  and `PlayerState.xml#`; those runtime state files were preserved.

These checks establish candidate/package/static correctness, not natural
ID26 AI selection, visible Results name, or race behavior. Those remain
`READY_FOR_HUMAN_RUNTIME` under the handoff.
