# Mercedes model conversion gate

## Chosen source revisions and hashes

The distinct demo-8.4.1 source is `DataGx/Vehicles/Copy of Mercedes`:

| Role | Revision | Bytes | SHA-256 |
|---|---:|---:|---|
| `car.dx` | 127 | 112,501 | `989905468d528bb35dec7901b03a08367b37a1fa4f8a32143428a782253d0791` |
| `complete.dx` | 127 | 122,138 | `000735aabd54dd6d6e3146ee981c5739616ad9169fbffe7bb9bbb3f461498c91` |
| `wheel.dx` | 127 | 12,932 | `9a331627ce44dc24ed9e3a3e4d92882e22b34cf4ef8fe561c1ee293e41d35661` |

Each role has a corresponding source GXM and TXT sidecar. The package root has 25 DXT files; the complete-model sidecar references 25 unique textures and resolves all of them. The nested `lpha` folder is a separate partial Alpha variant and was excluded from the selected package.

## Converter checks

The current release SDK parser does not parse these revision-127 vehicle draw records as retail. For the exact source car, complete, and wheel files it reports an unreasonable draw texture-slot count. The project's `upgrade_dx_131_to_135_with_report` fails closed on each with:

```text
unsupported DX revision 127; expected 131
```

The supported project transform is revision131→135. It does not accept revision127, and R5V-F.2 does not extend it speculatively.

The beta branch's R-COOKER closeout documents a different bridge: an original Demo-9.10.0 cooker can emit revision135 DX/DXT from source assets, and selected other vehicles loaded in retail. However, the historic Trooper/Rav4 transfer lacks exact old source-build identity, source/output hashes, and a recorded exact command/output recipe. It is not a deterministic, source-specific proof for `Copy of Mercedes` or its textures. The corpus's `Copy of MercedesAlpha` pair is only a partial two-role revision125 variant, with no documented cooker invocation or complete DX.

## Gate result

**BLOCKED.** No already-tested retail-compatible Mercedes package or exact conversion output exists in either project branch or the supplied retail corpus. R5V-F.2a has since statically confirmed that retail itself contains a GXM-to-DX cache-miss path whose writer emits revision 135, plus a separate GXI-to-DXT cache path. This establishes an available architecture, not a reproducible cook of these Mercedes files.

The source GXM embeds absolute GXI paths rooted at `D:/projects/MRallyeTNG/DataGx/Vehicles/Mercedes/`. A safe, writable mapping for those source and generated-cache paths has not been proven in an isolated retail workspace, and there is no runtime trace proving cache misses for all three roles. No DX/DXT was generated, staged, or committed. The precise missing item is a deterministic, hash-recorded retail-native build of all three distinct Mercedes roles and their textures, followed by strict SDK validation, authentic collision retention checks, and texture/material dependency validation.

See [R5V-F.2a findings](../r5v_f_2a/findings.md), [retail model cooker evidence](../r5v_f_2a/retail-model-cooker.md), and [texture cooker evidence](../r5v_f_2a/retail-texture-cooker.md). The 9.10.0 cooker remains separate historical evidence and was not substituted for retail.
