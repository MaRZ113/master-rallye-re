# R4D findings and decision

## Completed evidence

- CONFIRMED_BY_CORPUS: 26 vehicle families, 78 valid DX resources, 1,478 physical draw/material bindings inventoried. Three ordered slots per draw; slot 2 always Null.
- CONFIRMED_BY_CORPUS: 18 neutral structural signatures; 1,365 unique TXT tuple matches, 99 multiple, 14 unmatched. TXT association is not runtime classification.
- CONFIRMED_BY_CORPUS: 808 vehicle-local referenced DXT instances, 100 with alpha below 255. On unique draw/material matches, HasAlpha/UsesAlpha/actual-alpha combinations include 48 Yes/No/Yes and four No/Yes/No bindings.
- CONFIRMED_BY_CORPUS: second-slot helpers recur across vehicle families: whitepaint, perspex, rubber, glass, chrome, and silverpaint. Their blend equations remain unknown.
- CONFIRMED_BY_EXECUTABLE: PE imports d3d8.dll Direct3DCreate8; shader registry includes base, alpha, alphatest, environment, noise, water, and particle variants. The shader selector reads distinct alpha and alpha-test bytes, an environment option, and global reflection/detail options.
- HIGH_CONFIDENCE_INFERENCE: D3D8 COM wrappers at 0053F8B0 and 0053F930 match SetRenderState and SetTextureStageState by argument shape and vtable offsets. A particle shader method demonstrates specific calls. Vehicle-specific state setup is not yet traced.
- CONFIRMED_BY_CORPUS: raw +0x20 flag families correlate strongly with glass/glow alpha. Exact semantics are unresolved. See draw-control-fields.md.

## Unresolved material model

No direct path yet proves that DX slot 0 maps to stage 0, DX slot 1 maps to stage 1, or any precise combine operation. Neither TXT boolean has been tied to a D3D state. Material-name runtime significance is unproven. Glass depth/sort/test behavior, paint/decal layering, environment coordinates, damage fade, and glow blending are unknown. There is no evidence for a production material writer.

Blender preview remains first-non-Null and approximate. It preserves existing source metadata but does not claim stage fidelity. No R4D runtime material experiment has been executed. The small controlled matrix is ready for original-game testing.

## Phase gate

**R4D VERDICT: MORE WORK NEEDED. NEXT: R4D.1 — MATERIAL SEMANTICS HARDENING.** The key texture-stage map and main alpha/envmap blend equations still block safe authoring and a faithful preview. A focused Ghidra continuation should trace the DX draw loader into the material object read by 00580360, then inspect base/env shader vtable methods. Runtime tests M1–M4 should resolve only the remaining ambiguities. R4E has not begun.

The project owner reported on 2026-09-23 that the R4C tag-101 collision translation was CONFIRMED_BY_RUNTIME. This correction is recorded separately from new R4D material evidence; detailed R4C observation logs were not provided in this chat.

## Regression performed at this checkpoint

- Python synthetic suite: 64/64 PASS.
- Real DX visual writer: 78/78 byte-identical zero edits and 78/78 safe one-position edits; 28/28 tag-101 payloads preserved.
- Real tag-101 writer: 28/28 zero edits byte-identical, 27/27 finite translations pass, one Forklift static-only skip.
- DXT round-trip: 1,143/1,143 byte-identical.
- Blender 5.2.2 synthetic import/save/reload/positions-only export: PASS.
- Blender 5.2.2 diverse real-resource import/save/reload: 22 validated resources; existing zero-edit exports PASS.
- R4D corpus output regenerated deterministically; git diff --check PASS.
- No R4D material preview code or production material writer changed; source-byte invariants continue to be covered by the existing tests.
