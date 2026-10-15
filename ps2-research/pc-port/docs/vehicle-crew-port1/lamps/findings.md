# Rear lamp identity and fleet brake-glow admission

Read-only original source reconstruction; no integration, build, assets or renderer modified by this subtask. `audit.py` rereads canonical PackFS and protected retail DX, checks PS2 source SHA against the established 29-family inventory, decodes with the existing decoder, and emits compact metadata only. Five focused tests pass. No new runtime success is asserted.

## X-Trail upper rear light is a conditional source

The exact marked rear region is consistent with original `root.20.0.0`, node175558, six faces, PC compiled source record23. Its model-local bounds are X[-.780604,.768747], Y[1.169747,1.489145], Z[-2.202560,-2.018070]. Both upper rear lamps are contained here. Existing unconditional roots5/11 are at Z[1.905,2.167], the FRONT light family; their successful 28/14-face replacement does not cover this upper rear region.

| Native selected source | PS2 source | Final mode | Treatment |
|---|---|---|---|
|23 brake released|root.20.0.0, six faces, BL/perspex|3 carshiny|Private PS2 source at current native draw only; existing Mode4 mixed source, source normals/UV|
|24 brake held|root.20.1.0, six faces, breaklightson/lightshine|1|Do not force reflection; preserve native selected branch until separately ported|
|25 glow|root.20.1.1,22 faces, breaklightsonglow|14|Original RGB-fade texture and ONE/ONE, no body environment pass; original engine selects emission|

Source23/24 have EXACTLY THE SAME position bounds and topology. The existing `source_hash` is position-only and cannot admit a particular branch. Their UVs differ. Use the position+UV current-upload corner SHA below alongside the existing current chassis/queue owner, resource generations/revisions, native WORLD and range checks. A texture name or six-triangle count is insufficient.

Position+UV corner signature algorithm: for every emitted source index, append original little-endian XYZ float32 (12 bytes) then UV float32 (8 bytes). Sort the 18 complete 20-byte corner strings lexicographically as unsigned bytes, concatenate and SHA256. Native FVF0x142/24 UV offset16; FVF0x152/36 offset28; FVF0x112/32 offset24. Preserve duplicates; do not hash only unique vertices. Normal/diffuse bytes excluded so the signature works across the admitted source layouts. Continue independent position hash and exact native bindings checks.

OFF signature `49c1ec25031b36c03036b2b796e07fa0d45fc16ac32a59cf9df9cd6934fd9c9f`.
ON signature `33d039633b69e082adcff43cf0a024ea90a4ffeb8b273eca398d9cc1d59dcfc5`.

The private CAR asset already stores all3292 original vertices including conditional vertices. OFF six triangles can be expanded from the compact `source_indices` in source-registry.json (3170..3179), without changing the pinned asset bytes. Primary texture is already resident: CAR root10 has texture index13 BL, authored secondary8 perspex. Reuse the texture by semantic verified root10, not a new filename match. Apply accepted primary V correction exactly once. Its carshiny handler substitutes the mixed render target; do not retain perspex merely because that was the authored secondary. ON is a different handler outcome.

## Existing R5900 contract retained

No new broad executable analysis was necessary. `docs/xtrail-brake-followup/brake-contract/findings.md` independently byte-verified final mode14: textured strip, ABE1, fog OFF, TCC1/TFX1 DECAL, ALPHA `(Cd-0)*128/128+Cs`, depth writes masked, inherited ZTE/DATE. Preserve PC depth convention, never force GEQUAL. Mode1 default setup has blend OFF and depth writes allowed; the primary name override runs after shader handling. The literal carbrakelights name is not proof of a registered carshiny handler.

`docs/vehicle-fidelity-fix/glow-source/findings.md` established the original shared16x16 GXI SHA b6350f92f674bf2b63200ce4bb39c0c26f03fd99856ac0b89e7fc0797861af09: fading RGB, alpha zero. Existing Terrano additive texture/state path is the correct reusable mechanism. The original PC texture instead fades via alpha; ONE/ONE over its unmodified RGB produces hard polygons. Do not repeat that old mismatch.

## Fleet source candidates

29 original CAR families contain28 final-mode14 glow meshes; FORKLIFT has none. Source geometry AND UV correspondence under .001 position / .000001 UV produces20 uniquely matched PC candidates: ASTERO30, BRUNO19, CHEVYBLAZER35, ICECREAM28, KAMAZ26, KANGOO27, KIASPORTAGE32, LANDCRUISER31, MEGANE25, NAVARA30, NEWRAV33, PAJERO26, PATROL31, SEATBUGGY26, SIMMBUGGHINI24, TERRANO31, UFO10, WILDCAT27, WOOLDAND25→PC Forester, XTRAIL25. These numbers are compiled-source record indices, never native draw ordinals.

Eight source glow families are not admitted by this strict geometry+UV join: PS2 FORESTER (distinct model, no PC alias), FRONTERA, JUMP, MATTSERATI, MOONBUGGY, RMONSTER, TANK and TATA. A failed join is a precise candidate exclusion, not a license to relax source geometry. WOOLDAND alone maps to PC Forester. Native current-owner/source-upload admission for the19 newly listed families still must be implemented and tested; this source registry does not establish live material identity by itself. Existing Terrano is the accepted runtime case.

Suggested bounded A/B: same X-Trail rear camera, brake OFF / held / released; original emitted OFF draw gets six private reflective faces only, ON and22-face glow preserve their independent transitions and native draw boundary. Capture F10 at all three states, inspect no extra lamps, no glow reflection, exact state restoration, Reset and MSAA4x. Do not call parity from these source tests.
