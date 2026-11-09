# SDK authoring hash policy

Authoring inputs are editable; SHA-256 records provenance rather than granting permission to edit.

## Changes

- UI asset compilation accepts edited author PNGs, decodes and validates them, and records declared/current hashes and `source_modified` in its report. Native frame layout, safe paths and CRC checks remain enforced.
- Texture Studio accepts compatible externally edited package texture payloads after FEED header (except refreshed CRC), dimensions and catalogue validation. The original baseline remains pinned for Restore Original and model identity.
- Edited active artwork is accepted at native dimensions and recorded as Custom, never as a historical original. External source PNGs are decoded and rehashed. Archives remain separate.
- Legacy Workshop generated artwork can be retouched externally before Apply; the final native pixels are pinned with `source-pixels-v1`, avoiding a second composition.
- Artwork capture inherits the live viewport reflection setting. Standard reflection lighting is enabled by default.

## Retained checks and audit boundary

Searched Python authoring/build/validation tools, Qt/legacy Workshop, addon SDK, native previewer, runtime launcher and setup for hash comparisons and fixed SHA constants. This is a source review, not proof of all possible execution paths.

| Owner | Why verification remains |
|---|---|
| Workshop service / Universal Scene / source baselines | Restore Original, immutable geometry/UV baseline and source attribution. Edit through existing journals, imports or a new project rather than silently replacing baseline files. |
| Texture batch manifests | Bind a replacement to the intended original atlas/family/variant; prevent accidental glass/glow or PC/PS2 cross-target application. Image pixel hashes are not import gates. |
| Preview cache | Corruption causes cache regeneration automatically; it does not prohibit authoring. |
| Classic/source approvals | Bind approval to the report actually reviewed; changed inputs require refreshed evidence. |
| Frontend calibration / qualified HUD marker extraction | Fixed original resource layouts and evidence-based crop coordinates; changing the donor requires recalibration. User-authored icon import remains available. |
| Applied artwork pins / Workshop overrides | Detect damage to internal content-addressed undo resources; import/apply captures new author inputs. |
| Loose/runtime packages | Sealed build output and resource ownership, not editable source. Rebuild after editing. Existing options.xml exception is preserved. |
| Native patch builders / runtime ABI | PE layout, exact instruction preimages, hook ownership and serialized operations. Historical reproduction tools may still pin their reference EXE SHA; this is not a creative texture gate. |
| Renderer / Extra Options | Separate checkouts and runtime ownership; no modifications in this phase. |

Existing dirty runtime/setup changes were excluded from this commit. No installed files were changed.
