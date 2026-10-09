# R5V-J.2 combined runtime bundle audit

## Candidate identity

The tested bundle is the existing J.1 **combined two-addon** candidate. It is
one plan, one runtime resource root and one native patch operation table; it
is not a pair of separate one-addon launches.

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
