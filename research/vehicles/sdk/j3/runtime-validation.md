# J.3-B runtime compiler validation — 2026-10-09

## Exact inputs

Retail executable SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
(3,121,214 bytes; original file is external to the bundle).

J.0 two-addon plan SHA256:
`357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989`.

Qualified I.1 resource package manifest SHA256:
`1880d850da88ab57b66a4ad996c68efded31e8fd5c237bfd641cb5d9064baebf`.
Its `Data.sma` SHA256 is
`131d61ee8241df9cee4885db046e4e68d4df8177df40638bab01662ee12dc736`
(282,687,977 bytes). This is the already-qualified external runtime package
archive, not the pristine retail authoring archive.

Glacier author manifest SHA256:
`a1860562cb99c035f08887898b97f2646e317038bd0488d45e8041e5f8ffd436`.
Its independently verified author build has 47 declared artifacts and plan
SHA256 `1d64c320cc104d177db3c012986631590183175cdd167051267e68568ad5f492`.

## Deterministic collection results

| Artifact | Mercedes + R5VQualifier reference | Mercedes + GlacierSprint |
|---|---:|---:|
| Addon plan SHA256 | `357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989` | `1a242651f78fbe7d528d1f078be35573a37fb78abb955c53ad5d438af1b20dff` |
| Native operation count | 248 | 247 |
| Process-memory operation count | 247 | 246 |
| RVP SHA256 | `44c139de5b211947857bcb4e70ac84a6b9f1adc23cc9b0fe2a520978a5282f5a` | `3f18db5ab4f3d635f743868d3649b4f5b41d5198f31d26fb8f2e7a7be3076e0e` |
| Native manifest SHA256 | `3f1fc8b78582a2c5fcd639d3929e11c5f64b91957746a5970673417a292edac4` | `539ec636e7294eda561a819c89c416d15fb0aee49cd64f9dad37c048840e4a47` |
| Reconstructed reference image SHA256 | `2f3b1d95d05c997bb13d6a8e235327098e344b75b46d0432c4a3a7ecf289ab64` | `3cdf0db5ef579c27a04bc83d58a019cd5866329a254e5e34ece4ba74dff1cb46` |
| Staged resources | 243 | 187 |
| Runtime family for ID27 | `R5VQualifier` | `GlacierSprint` |
| Runtime qualification | false | false |

The reference operation table and reconstructed image match the human-tested
J.2 corrected candidate. The reference output retains the old J2 cave at
`0x0068EB40`. The Glacier manifest has longer identity payloads; a verified
zero-fill `.text` cave at `0x0068EFA0` is used without overlapping the parent
operations or leaving the audited code page.

For the reference collection, the compiler verifies the existing qualified
R5VQualifier DataGame family and reuses its exact bytes. The generated
`DataGame/vehicles.xml` SHA256 is
`6442df4d043517dd87ed31c82e2bfa7065aff4cc8154c7f3db5f5e9c4239c75a`, and
`DataGame/Modifications.xml` is
`e41053998c75fe411c666b7e5ee623163ab5e73cc5d464eeb86e1265f840b6d2`;
`DataScene/FrontendScreens/VehicleSelect.xml` has SHA256
`0b8c61efd2959a5b3b5dcef0d3810c2b445e021c465816627e87b9e3da2b4490`.
All three files are byte-equal to the qualified I.1 package. The reference
resource index therefore remains the exact I.1 index SHA256
`2fc7121c3d4f66c407cedbcb47dc223c580301971e3d12d16aa197c7a70a3384`.

The Glacier resource composition removes the old ID27/R5VQualifier package,
stages 42 project model/texture files under `DataGx/Vehicles/GlacierSprint`,
adds `Vehicles/GlacierSprint` DataGame rows (147 vehicle values, 26
modification values), and preserves the Mercedes rows. The SmallCarSheet frame
13 asset is present in the pinned `Data.sma` at SHA256
`5ad785dac2d5e41eb491cad852b93fc115f62b814d90e40ca74db28c78bb7fd1`;
it is not staged loose. Stock `Data.sma` is not rewritten.

The exact x64 launcher build used Visual Studio 18 2026 / MSVC 19.50.35729.0.
Build metadata SHA is recorded in the ignored runtime output; launcher SHA256
is `f93cb2c1dc92285fb268a99ff462dce63276c0be772fbba41be653fc6f473d1b`
(141,312 bytes). Its `--verify` command accepted the Glacier bundle, reporting
187 resource files and 247 native operations. The retail EXE still hashes to
the pristine SHA above after verification.

Both collections were compiled a second time into fresh output directories and
verified again. The reference pair reproduced the same operation manifest,
RVP, reconstructed image, 243-resource index, and plan hashes. GlacierSprint
reproduced the same operation manifest, RVP, reconstructed image,
187-resource index, and plan hashes. The machine-readable comparison is
`runtime-compiler-determinism.json` in the ignored J.3-B evidence directory.

## Focused tests

`tests.synthetic.test_addon_collection_runtime` covers the exact sparse pair,
explicit T2-only rejection, RGBA record bytes, family composition, bounded
VehicleSelect scene generation, J2 cave selection/ABI audit, and CLI command
registration. In the complete checkout, the focused J.3/J.2 regression group
ran **63 passed, 0 failed, 0 errors, 0 skipped**. The same module group from an
extracted source-only review archive ran **42 tests: 40 passed, 0 failed,
0 errors, 2 skipped**. Those skips are the two test classes requiring the
excluded retail executable / verified J.1 runtime bundle; the archive includes
the small JSON fixtures needed by the remaining tests.

## Status boundary

`PASS_STATIC_COLLECTION_RUNTIME_BUNDLE` means deterministic native/resource
planning and package verification only. `STATIC_BUILD_ONLY_NOT_RUNTIME_QUALIFIED`
means the launcher compiles; it does not mean it has launched the game. No
GlacierSprint runtime, rendering, physics, AI, lock-state, or re-entry result is
claimed until a human tests this exact candidate.
