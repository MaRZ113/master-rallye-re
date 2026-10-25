# R5V-J.2 combined runtime bundle and re-entry candidate audit

## Candidate identity

The 2026-10-09 gameplay captures were produced by the existing J.1
**combined two-addon** candidate: one plan, one runtime resource root and one
native patch operation table, not separate one-addon launches. The J.2
re-entry candidate below is a static derivative of that exact bundle; it has
not yet been used for the supplied captures or human-tested.

| Artifact | Location under checkout | SHA256 / value |
|---|---|---|
| Original retail `MRallye.exe` | `D:\Game\Master Rallye\MRallye.exe` | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, 3,121,214 bytes |
| J.1 launcher | `.research-output/vehicles/sdk/j1/launcher-release-final/mr-runtime-launcher.exe` | `9d4a98d01166362933974f8c376f3a42323feecfdfd021af7df0a3b1aceb31b5`, 141,312 bytes |
| Combined J.0 semantic addon plan | `reference-runtime-final/addon-plan.json` | `357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989` |
| Native patch manifest | `reference-runtime-final/native-patch-manifest.json` | `78c1070f2e656677f02d22f5d4fdff457e43c7ba74c67bb4e5a5c1488ca53179` |
| Sealed RVP1 operations | `reference-runtime-final/native-patch-ops.rvp` | `f4938b1a997364e371af6b1aee4798ca1865d67b22752bead9849c5d216a34ce` |
| Resource manifest | `reference-runtime-final/resource-manifest.json` | `b7e0fd4f785ed3f7a94dc6a0632cd8c16d7311478470087ad42bd73c0b871948` |
| Resource index | `reference-runtime-final/resource-index.tsv` | `2fc7121c3d4f66c407cedbcb47dc223c580301971e3d12d16aa197c7a70a3384` |
| Native reconstruction reference | analysis artifact only | `dd03adbd9f45c679e59d09e0a9f09337bd99c787d81f4ce018edb654c1cec881`; not a launched executable |

The J.0 reference plan was rebuilt from the two canonical addon manifests in
both input orders and is byte-identical to the pinned reference hash. Its
`runtime_installable=false` status remains intentional. The J.1 runtime bundle
is a distinct artifact type and is statically verified separately.

## Combined profile

| Physical ID | Class / local | Runtime and physics identity | Model package | Other independent policies |
|---|---|---|---|---|
| 26 | T1 / 7 | `Mercedes`; `Vehicles/Mercedes` | `DataGx/Vehicles/Mercedes` (28 resources) | audio profile 0; stock-like ID3 unlock; red `[1,0,0,1]`; Results `JEAN-PIERRE STRUGO`; dynamic T1 pools |
| 27 | T2 / 7 | `R5VQualifier`; `Vehicles/R5VQualifier` | `DataGx/Vehicles/R5VQualifier` (98 resources) | audio profile 7; stock-like ID10 unlock; magenta `[1,0,1,1]`; Results `R5V TEST DRIVER`; dynamic T2 pools |

The plan retains stock records and sparse maps:

* T1: `[0,1,2,3,4,5,6,26]`
* T2: `[7,8,9,10,11,12,13,27]`
* T3: `[14,15,16,17,18,19,20,21,22,23,24,25]`
* registry: 28 records, stride `0x34`; RaceTest base `0x5B4`, count 39,
  stride `0x2C`; allocation `0xC68`.

Native DriverID selection is not bound to either fixed Results display name.
Challenge remains authored and is not automatically populated. Player unlock
and AI eligibility remain separate.

## Resource closure

The 243 indexed resources are grouped as follows:

| Resource family | Count | Proof location / meaning |
|---|---:|---|
| `DataGx/` | 126 | Model/wheel and DXT packages, including 28 Mercedes files and 98 independently named R5VQualifier files. |
| `DataAudio/` | 109 | Existing qualified stock audio inputs; addon policy selects stock profiles 0 and 7. |
| `DataGame/` | 3 | `vehicles.xml` (778,407 bytes, SHA `6442df4d043517dd87ed31c82e2bfa7065aff4cc8154c7f3db5f5e9c4239c75a`), `Modifications.xml` (139,996 bytes, SHA `e41053998c75fe411c666b7e5ee623163ab5e73cc5d464eeb86e1265f840b6d2`), and options XML. `vehicles.xml` contains the named `Vehicles/Mercedes` and `Vehicles/R5VQualifier` physics/config families; no separate `Vehicles/<family>/` loose file is expected. |
| `DataScene/` | 1 | Effective `FrontendScreens/VehicleSelect.xml`, 155,756 bytes, SHA `0b8c61efd2959a5b3b5dcef0d3810c2b445e021c465816627e87b9e3da2b4490`. |
| `DataVideo/` | 3 | Indexed video resources. |
| `Data.sma` | 1 | Qualified package root copy is hash-verified; the retail installation copy is untouched. |

The launcher’s existing `--verify` validates the external root inventory before
launch. For `--integrated`, its documented process working directory is the
external `resource-root`; the J.1 runtime closeout and vehicle materialization
provide human runtime qualification of this route. The Observatory captures
themselves do not encode the launcher SHA or full resource-root path, so those
values remain candidate/handoff provenance rather than Broker-derived facts.

## J.2 Vehicle Select re-entry derivative

The ignored candidate under
`.research-output/vehicles/sdk/j2-reentry/runtime-candidate/` preserves the
J.0 plan, all 246 parent J.1 operations, and all 243 resources. It appends only
the constructor-convergence XY republish hook and its stub, producing 248
operations. Its dedicated Windows launcher is 141,312 bytes with SHA256
`c10c27a72387004a3696a1eab3d25f24e777ea2c566bf0a5f642f68e1085765c`. The
J.2 patch manifest SHA is
`53c5b1deccfaee1e798a7ff271db8232028eab501060186b582b04974e41b489`; the
operation payload SHA is
`945012567528fbe1b2794ed48b6d17473bcca340cc4e35d60d41a0fdd1c4fd9e`.
Native launcher `--verify` accepted the exact retail executable, 243-resource
inventory, and all 248 operations. This is static/package verification only;
the constructor hook still requires the human re-entry test.

## Critical hotfix disposition

The candidate above was later **FAILED_BY_HUMAN_RUNTIME** because opening
Vehicle Select crashed. It is retained unchanged as the failure record. The
static root cause was both post-`0x004D0580` LEAs using `[ESP+0x14]` after that
callee's `RET 4`; both must use `[ESP+0x18]` to address the constructor local
at `S+0x14`.

The separate repaired candidate lives at
`.research-output/vehicles/sdk/j2-reentry/repaired-candidate/`. Its launcher
SHA256 is
`4a91217c7fcb1e78f2165d12634ee7fd1746ae28a5855c9698f10b8904a0afd4`, patch
manifest SHA256 is
`09d2852ff8c439bb102d5b6a351860101fc7094175ab79bd2faeefe79c9b891c`,
operation-table SHA256 is
`aac0f887227c64ca4a591f542d9eda8a170b8b76f16687145c23e33664d57c17`, and
reconstructed reference-image SHA256 is
`a2170bdbdd1bc951862bc9fd6c93fc9a26d9eeba2b4b014810fc85474055dc2f`. It
retains exactly the parent 246-operation body, adds the same two J.2
operations, and still verifies 243 resources. The 86-byte stub SHA256 is
`f39f33838e0e7d3d276fbec03af0439c6c36a4807224ebe8cfc7ce14e70324ee`.

The emitted-byte symbolic verifier confirms both path-object addresses equal
`S+0x14`, call order/targets, `RET 4` / plain `RET` / `RET 8` stack effects,
balanced flags, final ESP and exact continuation. A negative test changes the
two displacements back to `0x14` and is rejected. Native launcher `--verify`
passes for the repaired bundle. The owner later confirmed that this
stack-fixed candidate opens Vehicle Select and restores ID26, but ID27 still
returns as Navara. It is superseded for the current retest by the
root-cause candidate below.

## Verification and scope boundary

The final existing bundle passed both the native launcher verifier
(`RUNTIME_BUNDLE_VERIFIED patch_operations=246`) and Python static runtime
verifier (`PASS_STATIC_RUNTIME_BUNDLE`). The full operation set is 246 records:
244 byte-changing memory ranges, one no-op canary, and one file-only PE-header
record that is not written into the mapped process. The reference reconstruction
is never launched and no replacement EXE is present in the bundle.

`tools/addon_runtime.py` intentionally pins the two runtime-qualified
reference profiles and composes the audited H.2/I.1 patch layers. This is a
fail-closed two-profile capability, not generic arbitrary-addon runtime
execution. The J.0 compiler remains manifest-driven and unchanged. ID28 and
broader ID allocation runtime support are outside J.2.

## Current root-cause candidate — ID27 reverse-map correction

The stack-fixed candidate above was subsequently tested by the owner: Vehicle
Select opens, ID26 restores, but ID27 still becomes Navara. Exact decoding of
its effective reverse mapper found that the ID27 arm wrote T2/local7 into the
T1 ordinal slot at `this+0x14`; T2's field is `this+0x18`. The latest separate
candidate is under
`.research-output/vehicles/sdk/j2-reentry/root-cause-candidate/`. It is
derived from the same 246-operation J.1 parent, corrects one inherited
displacement byte, and retains the two stack-fixed J.2 publication
operations: 248 operations total and the same 243 resources.

| Artifact | SHA256 |
|---|---|
| Launcher | `1fb190ae85d2b7b119576a650e4723abb1130ef4bbdee6d353357087e3de66c7` |
| Native patch manifest | `162de9762c070fd970731da030f03150b303ecf2f8886bd4f25ca357b9129f11` |
| Native operation table | `44c139de5b211947857bcb4e70ac84a6b9f1adc23cc9b0fe2a520978a5282f5a` |
| Reconstructed reference image | `2f3b1d95d05c997bb13d6a8e235327098e344b75b46d0432c4a3a7ecf289ab64` |
| Constructor publisher stub | `f39f33838e0e7d3d276fbec03af0439c6c36a4807224ebe8cfc7ce14e70324ee` |

The operation-table correction changes the inherited ID27 store at VA
`0x0068E895` from `C7 46 14 07` to `C7 46 18 07`; only the displacement byte
at file offset `0x28E897` changes within that inherited operation. Exact
candidate verification checks the emitted reverse and forward mapper bytes,
ID27's T2/local7 state, ID26 and stock mapper preservation, operation count,
resource hashes, and unchanged J.0 plan. The corrected candidate is
`READY_FOR_HUMAN_RUNTIME`, not runtime-qualified. Use
[`root-cause/human-retest.md`](root-cause/human-retest.md); the previous
stack-only candidate is not the candidate to test.
