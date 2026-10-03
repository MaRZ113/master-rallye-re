# Vehicle Preview V3: semantic assertions and approximation

`PreviewMaterialCache.material_for_draw` uses the canonical read-only
`MaterialSemantics` projection for vehicles. The prior unscoped implementation
remains separate for course imports; this phase makes no course material claim.
Cache keys include ordered slots, raw flags/mask/variant, images and Reflections.

## Exact annotations

The material preserves raw `mr_texture_slots_json`,
`mr_serialized_flags_0x20_hex`, `mr_serialized_texture_mask`, and existing
properties. `mr_preview_source_slot` is 0 when the base binding is enabled,
otherwise -1; a helper is never promoted to the primary image. Structured
`mr_material_semantics_json` includes family, stage bindings, operations,
flag/feature roles, confidence and state scope. The object adds
`vehicle_material_semantics_version` and per-draw `runtime_material_semantics`
alongside, not in place of, canonical raw writer metadata.

`mr_runtime_environment_enabled` describes feature capability;
`mr_preview_reflections_enabled` is the selected global-gate projection.
Import defaults to Reflections ON. A cache with `reflections=False` suppresses
env binding/nodes and projects the base family, retaining raw slots and mask.

## Node behavior

- Slot0 supplies stage0 texture. Byte2 enables MR Vertex Color modulation;
  otherwise white/alpha1 is the display approximation for absent diffuse.
  Byte3 enables MR UV0; absent source UV uses a labelled zero-coordinate
  approximation. The two stock byte3=0 draws have no textures.
- Every observed slot1 name follows the same stage1 path. Display normal is
  transformed WORLD->CAMERA, scaled by0.5 and offset by(0.5,0.5). A separate
  unlit Principled contribution approximates `current.rgb + current.a*env.rgb`;
  stage1 alpha multiplies current alpha by env alpha. There is no filename
  strength, no special chrome shader, and no helper mixed into Base Color.
- NULL slot0/nonnull slot1 preserves bound stage1 metadata, but suppresses its
  preview contribution under HIGH_CONFIDENCE_INFERENCE of the NULL cascade.
  Textureless draws show diffuse, not the first available helper texture.
- Raw byte0 selects blended/opaque preview regardless of DXT pixel alpha.
  Synthetic alpha-test uses a GREATER_THAN node at128/255; Blender5.2 uses
  DITHERED, older supported APIs use CLIP/BLEND when available. This does not
  promise equal filtered/rasterized coverage to the D3D8 GREATER128 integer test.
- Missing textures produce scoped warnings; unobserved variants produce an
  explicit UNKNOWN reason and conservative fallback rather than fabricated
  ordinary shader behavior.

## Limitations recorded in material properties

`mr_preview_confidence` is APPROXIMATE for classified families and UNKNOWN for
unsupported branches. Small machine-readable notes cover Principled lighting,
Blender-calculated display normals, camera coordinate conventions, composite
runtime sorting, instance Z overrides, unloaded/missing textures, and unknown
variant branches. The source-space normal attribute/custom-normal workaround
is unchanged. Generic env preview is not physical emission or additive
framebuffer blending; glow-name materials remain ordinary source-alpha layers.
The fixed-function clamping/color pipeline is not raster-equivalent to
Principled lighting, color management, or the unlit helper contribution.

Coverage: 1092 env bindings, 1089 effective previews; whitepaint222, chrome145,
perspex219, rubber220, glass219, silverpaint60, lightshine2, lights2. The two
remaining perspex and one glass bindings are the NULL-base cases. All five
NULL-base records and all stock draws are classified.

## Authoring separation

Preview nodes are not a writer input. Existing fixed-field alpha/env edits,
same-topology attributes, supported DXT content edits, and template/raw-byte
preservation remain the existing contract. Byte1/2/3 interpretation adds no
new writer capability, texture string editing, material creation or new draw.
Blender audit verifies 78/78 zero-edit exports, preserved controls/flags/slots,
save/reload and a byte-identical export after deleting preview nodes. Synthetic
tests exercise alphatest, OFF gate, attribute gates and unsupported fallback.
This is automated semantic/export evidence, not a visual or in-game PASS.
