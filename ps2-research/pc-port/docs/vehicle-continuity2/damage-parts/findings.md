# Damaged headlight and upper rear OFF lamp

Read-only bounded evidence; no source/build changes. Newest race-damage PID6404 frames17052/26615 are already sufficient to confirm the headlight rejection. PID14520 healthy14178 supplies a source-hash-verified healthy control; its pointer addresses are not reused as identity.

## Headlight: exact failed gate proven

PC source10,22vertices/18faces maps to PS2 CAR root19/mode20. Healthy full geometry SHA `fad797c65838c39d359767a9ef06d0d5579d847fa2b23a9ee8febe8c171b361c` is the exact `kRaceParts[0]` profile.

| Capture | Full XYZ geometry SHA | XYZ vertices changed | Current native owner |
|---|---|---|---|
| 14178 / PID14520 | `fad797c65838c39d359767a9ef06d0d5579d847fa2b23a9ee8febe8c171b361c` | 0 | context7, matching owner, certified=true |
| 17052 / PID6404 | `d6dac6b5cb2a82ad73ad0e64248ffd826f1fd71551b73abc4b4ee656faf5cf8c` | 2 | context7, matching owner, certified=true |
| 26615 / PID6404 | `c50b37167b1359de61d46286843b2dd658bc7dd63118432004208db2e9e13a92` | 1 | context7, matching owner, certified=true |

All three captures preserve exact ordered UV SHA `386abd4d4b7bc87a3ce96c951ec12e6df6274934eec1a5aab5fae70d526667e7` and normalized original winding/index SHA `863e57880d5adbc15276a4cc38e9c41c30633bad14a0baac4b92589a00012f6d`. Native damaged copies retain current selected ownership; this is not a context5 clone-membership failure.

`renderer/race_model_native.hpp::draw_race_part` first resolves unmatched cache entries by full `source_hash(g)==kRaceParts[i].source.hash`, then repeats that healthy full hash when rebuilding the cached part record. Current damaged XYZ differs, so part0 is rejected before its private mode20 submission and native PC headlight geometry remains Stock. The main13-record damage certificate does not cover this separate part.

Safe fix prerequisite is a separately pinned part ordered-UV/winding certificate plus source-derived deformation correspondence and healthy reference, with exact owner/currentupload checks. Do not merely remove fullhash checks or render undeformed PS2glass over deformed native headlights. These samples prove2/1sourcevertices changed; they do not alone prove every future damaged state.

## Upper rear OFF: source-bound candidate, runtime bytes missing

PC source23 OFF has10vertices/6faces and original full geometry SHA `a6d34ae167a6e81a9a411bd4856c5c5152fbd34ab37163cb76fd2079e1f59393`. It maps to PS2root.20.0.0 mode3. PC24ON has identical XYZ/topology but differentUV; source25glow is22faces and independent.

Current `reflection_pilot.cpp` requires both the healthy full XYZ hash and `position_uv_corner_sha==49c1ec25031b36c03036b2b796e07fa0d45fc16ac32a59cf9df9cd6934fd9c9f`. Both checks include positions and will reject deformation. This is a code-supported candidate explanation, not yet measured rear OFF damage proof. Existing race-damage probe selects13body layouts plus10parts and does not include10v/6tri conditionalOFF; no rearOFF bytes occur in the newest two probe files. Ordinary F10 alone does not provide the required full current XYZ/UV/index bytes.

Minimum additional capture: extend only the opt-in bounded damage probe to include10vertex/6triangle candidates, record current selected subtree/conditional-leaf membership, complete XYZ/UV/index bytes and binding/generation/revision identities, plus OFF/ON branch discrimination. Capture healthy brake-released F10, impact then brake-released F10 in one race. A held-brake control identifies the sameXYZ/differentUV ON branch. Reuse existing capture file/frame limits; do not add per-frame resource reads or broaden capture to all draws.

PID6404 session and transition files were still buffered/zero-length during this inspection. No later session gate outcome is invented. `headlight-damage-evidence.json` carries exact original artifact hashes and measurements without embedding source geometry.

## Exact source correspondence draft

The pinned generator maps all 26 referenced PS2 root19 global vertices to PC source10 within 1e-5; every vertex has exactly one native candidate and none is unmapped. Ordered UV+winding SHA is 502345f8abbf60ba1016ab1f29d98f74ea35c9c3e85fc260c405cf28a475f24d. The header contains indices and hashes only. Source tolerance is offline correspondence construction, never runtime identity or positional acceptance tolerance. Runtime must keep exact source/healthy certificates and fail closed on unknown revisions, missing references or candidate disagreement.

