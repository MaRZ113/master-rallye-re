# Source Garage — first adapter decision for review

28 October 2026. **PROPOSED; implementation has not started.** The audit is the
review boundary requested by the owner. No cross-game vehicle has been authored,
compiled, assigned a CarID, installed or gameplay-qualified in this phase.

## Selected bounded pilot

**4x4 Evolution 2, Toyota 4Runner SR5 Sport Package 2WD, model year 2000.**
This exact display name/year comes from the local `TRUCK/T4RSR52.TRK` record;
it is not a claim of four-wheel drive or a model identity inferred from a mesh.
The goal after review would be one source adapter producing a conservative
Universal Vehicle Scene inspection, followed by a separately reviewed MR bridge.

| Input | Exact evidence |
|---|---|
| Local root | `E:/RallyWorkshop_Sources/sources/4x4 Evo 2` |
| Executable | `4x42.exe`, static Windows file/product version `1.00.139`; exact SHA256 in corpus manifest |
| Container | `TRUCK.POD`, POD2, 144691121 bytes, SHA256 `5669509d709193621802a43c2c63b32e537fcf93ea3fd5d94af8c66947be6a41` |
| Body | `MODELS/4RUNNERSR5.SMF`, text C3DModel, 171308 bytes, SHA256 `a7f71e0ae1cae2fb64438ce8614bf7db47eb9dfc813d926388da4dfef7b6a11e` |
| Catalog | `TRUCK/T4RSR52.TRK`, SHA256 `d2ff6c5914e8102116e56704dac800442fed3adfbf42326c6b3311517e8bbcb4` |
| Recovered structure | 33 objects,2089 source vertices,1967 triangles; UV/material records retained; six `4RUNTIRE{08,12,16}{L,R}.SMF` wheel variants; four explicit TRK wheel placements |
| Texture | `ART/4RUNNERSR5.TIF`,512×512 RGBA decode; observed alpha255 only, which does not resolve glass/reflection semantics |
| Existing tool knowledge | PyPOD1.1 MIT archive reader; Dummiesman SMFImportExport1.1.1 source-reviewed, CC BY-NC-SA3.0; independent bounded probes already ran, no third-party implementation vendored |

The installation also contains TRIHook and other local modifications. Neither
this POD nor either Evolution installation is authenticated against an original
publisher distribution. Pinning exact bytes makes the experiment reproducible;
it does not prove pristine retail provenance. Any replacement source requires
a fresh qualification. Edition/region remain unknown where unsupported.

## Why this first, and what stays important

Personal/historical priority and technical readiness remain separate:

| Candidate | Personal / historical priority | Actual technical evidence | Decision |
|---|---|---|---|
| Paris-Dakar Pajero targets | Highest historical interest; possible prerelease MR link is unproven | Both Pajero TC resources exist; embedded object names confirmed; section/mesh/texture decoder unresolved | Keep first historical research track. Not ready for a bounded vehicle adapter. |
| Michelin RAV4 / Megane | Elevated personal priority | Catalog/script association and PDI1 directories validated; payload flags require TEA/LZSS and model decoding | Keep early focused follow-up: Car25A/RAV4 and Car06A/Megane F2. Do not rename F2 as proven Maxi geometry. |
| Evo2 4Runner | Technical opportunity and relevant SUV character | Actual body, UVs, material records, textures, separate wheel geometry and placement records available | Best bounded adapter candidate, with explicit alpha/pose/units unknowns. |
| Evo1 same 4Runner | Technical opportunity | RAW/ACT/OPA and SMF recover; local installation explicitly community Build58/2020 patch-bound | Valuable sibling regression fixture; avoid presenting it as unmodified2000 retail. |
| Screamer Pajero | Relevant SUV and technical opportunity | COD plus body/wheel DAT streams and texture decode work | Strong runner-up; material-ID→texture bindings, native transforms and axes still unresolved. |
| V-Rally2 PC block1 | Technical opportunity | Real CRC-checked PAK decode, indexed OBJ/MTL and texture pages | Wheel/node assembly unresolved; local exporter redistribution license unclear. Physical block is not yet an exact named vehicle. |
| Sega Rally2 Delta | Rally interest | Partial root geometry/UVs and texture decode | Hierarchy/material binding incomplete; not preferred over wheel-qualified source records. |
| DiRT2007 / DiRT2 | High-value unusual vehicles; separate priorities/builds | Distinct PSSG dictionaries and separate published converter paths | Higher scene/shader complexity; actual glTF export not qualified in this audit. |

## Success criteria for a future approved implementation

1. Read only the exact configured POD; validate all table ranges, sizes and
   selected member identities. Preserve original indices, visibility flags,
   material values, UVs, frames and source-member provenance.
2. Recover one catalog-selected 4Runner body and explicitly selected left/right
   wheel variants into the proposed scene. Preserve all four source placements
   and record local/world transforms without silently fitting an MR donor.
3. Establish source axis/units and wheel rest pose from independent format/source
   evidence. The community feet→metres convention and TRK comments are evidence
   leads, not runtime measurement. Render a complete selected assembly before
   declaring L1 complete.
4. Preserve TIFF channels, original material associations and unresolved alpha,
   reflection, lamp/glass/accessory/variant semantics. Do not infer opaque glass
   from an alpha255 image or repair the upstream Evo2 alpha issue automatically.
5. Qualify body sibling/color/LOD selection; `4RUNNERSR50.SMF` is currently only
   discovered. Do not label it an original colorway or LOD until joined to the
   source selection records. Retain source animation/equipment unknowns.
6. Produce deterministic private scene outputs, malformed-input regressions and
   source hashes. Test an assembled textured preview with explicit renderer
   limitations. No original rendering parity follows from that preview.
7. Reuse the existing MR authoring systems only after a separate qualified
   translation/profile decision. Classic v2 currently accepts GT3/GT4 only;
   extending its source gate requires evidence, not a new format-name alias.

No success criterion expands the30-entry roster or changes accepted Subaru,
Lancer, Pajero, Trooper or Clio alternatives. Physics/audio/camera/shadow/damage/
frontend decisions belong to existing shared authoring, not source parsing.
Gameplay is a later independent gate. **Stop here for audit review.**
