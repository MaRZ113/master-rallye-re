# Master Rallye Vehicle SDK — Source Garage Hardening
## Cross-Game Fidelity, WARN Resolution & Universal Native Bridge Qualification

I want to begin a major technical consolidation milestone for Rally Workshop and Master Rallye Vehicle SDK.

We have already recovered authentic vehicles from several different games, and I do not want to continue adding new source games until the existing conversion architecture is thoroughly qualified.

**The goal is to resolve remaining source-format and rendering WARN conditions wherever possible, fix actual bugs, and make the Universal Vehicle Scene → Master Rallye native bridge reliable across different donor engines.**

This should be an implementation and validation milestone, not merely a new research report.

Use the latest committed repository, the complete Master Plan v7.7 or its current successor, and all existing source research.

Preserve the full historical project documentation.

## 1. Scope and priorities

The three main donor engines are:

**4x4 Evolution 2**
- Toyota 4Runner SR5 Sport Package.
- Existing Evo2 SMF/TRK/TIFF source adapter.
- Already demonstrated as a playable Master Rallye vehicle.

**Dakar 2 — Original Xbox**
- Mitsubishi Pajero.
- Hino Ranger.
- Nissan Pickup.
- Existing RBB/SBB/HIR/XMD/XTX decoder and renderer-state reconstruction.
- Neutral source models recovered successfully.
- Native MR import not yet qualified.

**Michelin Rally Masters**
- Toyota RAV4 — `Car25A.PDO`.
- Renault Mégane F2 — `Car06A.PDO`.
- Existing PDI1/PDO/XOBJ/PTOC/TEA and texture decoding.
- Complete neutral static scenes already reconstructed.
- Native MR import currently unqualified.

Also use the accepted PC Paris-Dakar Pajero Silver and existing Master Rallye vehicles as regression/reference cases.

Do not begin research into any additional game.

Do not start Blender Bridge, new fleet imports or vehicle-roster expansion during this milestone.

---

# PHASE A — Comprehensive Qualification Audit

## 2. Build a single Source Garage Qualification Matrix

Inspect all existing source adapter reports, implementation, tests and unresolved issues.

Create and maintain:

`docs/sdk/SOURCE_GARAGE_QUALIFICATION_MATRIX.md`

This document must track each donor format and each representative vehicle.

For every unresolved issue, include:

- Source game and exact resource family.
- Original evidence and source hash.
- Relevant module/function.
- Current implementation behavior.
- Expected behavior.
- Exact remaining uncertainty.
- Reproduction procedure.
- Source Fidelity impact.
- Native MR import impact.
- Severity.
- Whether the issue is shared or game-specific.
- Proposed fix.
- Verification requirements.
- Final status and supporting evidence.

Use explicit classifications:

- `PASS`
- `WARN`
- `UNSUPPORTED`
- `BLOCKED`
- `NOT TESTED`

Also track separate qualification levels:

- L0 — Source identification and integrity.
- L1 — Structural decoding.
- L2 — Source scene and rendering fidelity.
- L3 — Native Master Rallye conversion qualification.
- L4 — Actual owner-tested D3D8 gameplay.

Do not promote one level because another level passed.

Do not equate a valid neutral D3D9 preview with successful Master Rallye gameplay.

## 3. Establish meaningful severity rules

Classify defects into:

**P0 — Fundamental correctness**
- Corrupted geometry.
- Invalid source references.
- Incorrect transformations.
- Data loss or nondeterministic builds.
- Destructive changes to original resources.
- Regressions in existing accepted projects.

**P1 — Native import blocker**
- Incorrect wheel orientation or attachment.
- Missing critical mesh surfaces.
- Body panels incorrectly transparent.
- Invalid material or triangle ownership.
- Broken native damage or brake-light construction.
- Unsafe native resource or roster changes.

**P2 — Source Fidelity limitation**
- Incomplete original shader reconstruction.
- Unknown dynamic LOD or equipment policy.
- Approximate original lighting.
- Missing original source-game effects that are not required by MR.

**P3 — Optional artistic improvements**
- Additional reflections.
- Custom cabin enhancements.
- Exterior spare-wheel positioning.
- New decorative suspension geometry.
- Historical livery recreation.

Fix P0 and P1 issues before promoting a donor family to native import readiness.

Investigate P2 issues where source evidence makes a genuine solution feasible.

Keep P3 work outside this milestone.

A documented unresolved original rendering effect can remain WARN if it demonstrably does not compromise native MR conversion.

However, do not relabel unresolved defects as PASS merely to finish the milestone.

---

# PHASE B — 4x4 Evolution 2

## 4. Close remaining Evo2 source-format questions

Revisit:

- `EVO2_SOURCE_ADAPTER_RESULTS.md`
- `EVO2_SOURCE_SEMANTICS.md`
- The qualified SMF/TRK source adapter.
- Original executable loader research.
- The accepted Toyota 4Runner project.

Known remaining areas include:

- Original TIFF secondary sample semantics.
- Source alpha and transparency policy.
- Original bump mapping.
- Source reflection materials.
- Nine original body color configurations.
- Auxiliary `Light*` objects.
- `Axler` and other non-body-pass components.
- Source runtime LOD/material behavior.
- Wheel and suspension dynamic transforms.
- Static initial position versus gravity-settled vehicle pose.

Investigate the original executable and source resources to resolve these wherever practical.

The TIFF second sample has not been established as alpha. Do not invent alpha semantics based on the number of samples or library conversion behavior.

The original static wheel positions are not proof of settled runtime suspension.

Preserve original left/right wheel geometry and detail variants.

Do not confuse wheel detail resource suffixes with tyre diameter.

Do not automatically apply the low-detail axle adjustment to the high-detail wheel configuration.

## 5. Qualify Evo2 rendering and scene ownership

Determine which original components belong to:

- Opaque body rendering.
- Windows and transparent surfaces.
- Lamp and auxiliary-light rendering.
- Axle or suspension rendering.
- Additional lighting/reflection stages.
- Dynamic or optional equipment.

Recover exact material/mesh ownership wherever possible.

Implement reusable source-semantic mappings rather than hardcoded Toyota-specific polygon overrides.

Keep unsupported components with original provenance.

Do not generate fake opaque glass or fake reflections to hide uncertain source rules.

The accepted 4Runner must remain unchanged unless an independently verified bug fix is explicitly required.

The prior unsuccessful visual additions — fragmented reflections, incorrect rear glazing, duplicate steering wheel and disconnected static frame — must not return.

## 6. Validate Evo2 beyond one static view

Where possible, use original 4x4 Evolution 2 runtime screenshots or qualified executable behavior.

Compare:

- Front/rear/side geometry.
- Original colors.
- Window rendering.
- Wheel facing.
- Wheel attachment.
- Auxiliary equipment.
- Material response.

Distinguish original game rendering from our neutral interpretation.

Keep source-only differences from becoming unexplained native MR modifications.

---

# PHASE C — Dakar 2 Xbox

## 7. Complete original rendering semantics

Review:

- `dakar2_fidelity.py`
- `DAKAR2_RENDERER_RESULTS.md`
- `DAKAR2_SOURCE_RESULTS.md`
- The existing Xbox executable research.
- MRPV v2 source-renderer transport.

The accepted decoder already handles:

- Original geometry.
- Indices and triangle strips.
- Source node transforms.
- Texture resources.
- Original vertex colors.
- Basic per-draw culling.
- Depth-write state.
- Blend state.
- Source pass order.

Do not reimplement these working parts without a demonstrated defect.

Investigate the remaining areas:

- UV1 and secondary UV use.
- Multiple Xbox texture stages.
- Pixel-combiner behavior.
- Vertex processing and lighting.
- Alpha-test activation conditions.
- Alpha blending versus alpha testing.
- Texture sampler addressing and filtering.
- Original equipment visibility.
- LOD selection rules.
- Source transparency and wheel interior rendering.
- Dynamic lamp and wheel presentation.

Use actual original executable instructions and data where possible.

Do not assume that source shader words correspond to standard PC Direct3D fixed-function materials.

Do not globally disable culling.

Do not reverse all triangles to make one viewpoint appear correct.

Do not insert generic reflections into the original source scene.

## 8. Validate across three different vehicle types

The same decoder must be validated on:

**Mitsubishi Pajero**
- SUV body and wheels.
- Original equipment hierarchy.
- Glass and rear lamps.
- Interior spare-wheel nodes.

**Hino Ranger**
- Heavy truck proportions.
- Multiple wheel assemblies.
- Large body and cabin structures.
- Different materials and transforms.

**Nissan Pickup**
- Qualified nonidentity rotational transforms.
- Correct hierarchy and component placement.
- Original wheel geometry.
- Equipment and model variations.

Do not assume that passing Pajero tests proves that the entire format works.

Include source-derived structural tests and D3D9 visual comparisons for all three.

Preserve the current explicit rejection of unsupported Nissan transforms.

Do not relax safety checks merely to achieve a successful preview.

## 9. Resolve original variant and equipment policies

Previous research found numerous named resource variants and LOD/equipment members.

Investigate actual original loader dispatch and source metadata.

Where qualified, determine:

- How the game selects body variants.
- Which parts are visible in the default race configuration.
- How wheel and equipment states are selected.
- Whether some model members represent damage states.
- Whether spare-wheel visibility changes at runtime.
- How original LOD switching operates.

Do not infer semantics solely from resource names or counts.

If exact dynamic behavior cannot be recovered, preserve the original variants and provide an explicit static selection policy.

## 10. Preserve the established spare-wheel findings

The Xbox Pajero contains three genuine spare-wheel nodes:

- `PAJ_SPAREWHEEL1`
- `PAJ_SPAREWHEEL2`
- `PAJ_SPAREWHEEL3`

They belong to `PAJ_REARROLLCAGE` and are located inside the rear cage, consistent with the owner's PS2 gameplay observation.

An optional fourth externally mounted spare was created as a reversible MR Beta-inspired scene overlay.

Preserve that experiment, but do not promote it to Source Fidelity.

The original wheel-backing issue is still unresolved.

Research whether apparent wheel openings result from original geometry or source renderer semantics.

Do not add black discs without proving that they improve the intended native representation.

No additional artistic spare-wheel work is required during this milestone.

---

# PHASE D — Michelin Rally Masters

## 11. Finish original static scene qualification

Review:

- `michelin.py`
- `michelin_research.py`
- `MICHELIN_ASSEMBLY_RESULTS.md`
- The existing Michelin original-executable research.
- RAV4 and Mégane Universal Vehicle Scene projects.

The established foundation includes:

- Correct body LOD records.
- Original indexed geometry.
- Original palettes and textures.
- Material references.
- Initial wheel hub coordinates.
- Catalog-selected wheel geometry.
- Separate source damage-target vertex streams.

Preserve these findings.

Do not blend intact body positions with damage-target vertices.

Do not modify original XOBJ geometry for visual convenience.

## 12. Resolve wheel and coordinate semantics

Investigate:

- Original source coordinate system and handedness.
- Source unit interpretation.
- Left/right wheel orientation.
- Runtime wheel transform construction.
- Steering rotation.
- Wheel spinning.
- Suspension rest versus settled positions.
- Original wheel selection policy.
- Wheel attachment hierarchy.

Use original loader behavior or directly qualified source evidence.

If the complete Michelin runtime transform cannot be reproduced, implement a distinct, verified conversion to the existing Master Rallye native wheel system.

Record what is original source behavior and what is an MR adaptation.

Test both RAV4 and Mégane.

Do not silently rotate one wheel by 180 degrees or mirror a wheel simply because it looks better.

## 13. Resolve material, alpha and glass behavior

Investigate:

- Palette index conventions.
- Qualified magenta-key transparency.
- Alpha test and alpha blend.
- Original cutout filtering.
- UV orientation.
- Original glass material classification.
- Triangle winding.
- Material draw order.
- Source lighting/shading ownership.

The neutral scenes currently retain opaque windows where original glass semantics remain unresolved.

Do not assume that black pixels represent transparency.

Do not replace entire body materials with transparent variants.

Identify actual window surfaces before mapping them to native MR glass.

Preserve pillars, frames, doors, decals and body opacity.

If true source glass behavior cannot be recovered, permit a conservative native MR adaptation only when glass boundaries and damage zones are demonstrably correct.

No invented rear interior boxes or arbitrary transparent triangles.

## 14. Clarify original damage behavior

Previous research established that Michelin `_VERTEX.BIN` streams contain deformation targets rather than alternative intact body geometry.

Investigate the actual runtime relationship sufficiently to distinguish:

- Default body vertices.
- Damage target vertices.
- Interpolation or deformation control.
- Detachable body components.
- Non-body damage behavior.

Do not require full original Michelin damage playback for MR conversion.

Instead, establish which geometry can safely use the qualified MR-native damage system.

Preserve original Michelin damage data as source research metadata.

Do not generate fake damage controllers or unsupported glass breakage regions.

---

# PHASE E — Universal Vehicle Scene and MR Bridge

## 15. Review the common scene contract

This is the most important architectural part of the milestone.

I want one shared and predictable path:

**Donor Source → Qualified Source Adapter → Universal Vehicle Scene → Master Rallye Native Bridge → Reversible Native Candidate**

Review the existing contract for:

- Source coordinate systems.
- Handedness and winding.
- Normals and transformations.
- Original and normalized scale.
- Mesh hierarchy.
- Material ownership.
- UV0 and UV1.
- Texture stage metadata.
- Glass surfaces.
- Brake-light surfaces.
- Wheel roles.
- Wheel attachment transforms.
- Original equipment and LOD states.
- Damage metadata.
- Provenance.
- Unknown semantics.

Avoid adding assumptions that happen to work only for one source engine.

Each format adapter should declare its own qualified source semantics while reusing shared scene and native conversion operations.

Unknown source rules must be explicit and fail safely when they are required for an output.

## 16. Implement reusable semantic validation

Add a common validation system for vehicle parts and materials.

Important reusable semantic categories include:

- Opaque body.
- Transparent glass.
- Window frames and pillars.
- Lamp OFF surfaces.
- Lamp ON surfaces.
- Reflection-eligible painted surfaces.
- Mirror body and mirror inset.
- Wheel tyre.
- Wheel rim.
- Wheel interior.
- Wheel attachment/hub.
- Optional equipment.
- Damage-eligible geometry.
- Cabin or crew-related components.

These should be evidence-based mappings, not mandatory guesses.

Preserve original source identifiers and source-to-derived mappings.

A source format may legitimately leave a role unknown.

Do not force all vehicles into the same material classification merely to simplify conversion.

## 17. Qualify native MR rendering compatibility

The source scene can look correct in D3D9 while its native Master Rallye conversion is wrong.

I want specific checks for that boundary.

Investigate and validate:

- DX/DXT output.
- Original texture preservation.
- Correct opaque body rendering.
- Native material and environment-reflection compatibility.
- Correct UV and atlas ownership.
- Glass transparency and damage states.
- Brake-light OFF/ON assignments.
- Wheel culling and handedness.
- Wheel controller compatibility.
- Resource determinism.
- Race versus frontend geometry.
- Shadow and frontend framing.
- Source mesh and triangle conservation.

Avoid the earlier 4Runner failure where reflection polygons were selected through rectangular texture-atlas regions, producing torn reflective islands.

Do not substitute a fragmented reflection overlay for a complete base material.

Only use qualified native MR reflection mechanisms with suitable complete material groups.

When an imported material cannot support safe reflections, retain its correct opaque diffuse appearance.

## 18. Qualify wheel and suspension conversion

This requires special attention because our donor cars have very different physical proportions.

Ensure that the universal bridge can handle:

- Passenger rally cars.
- SUVs.
- Pickups.
- Heavy trucks.

Distinguish visual wheel geometry from:

- Physics wheel radius.
- Wheel hub rest position.
- Suspension travel.
- Steering controller.
- Wheel spin.
- Wheel collision/camera relationships.

Never assume source-game suspension constants can be copied directly into MR.

Use dedicated, reversible native physics profiles.

Inspect accepted MR donor families and identify which parameters require manual tuning after import.

Do not automatically change accepted vehicle physics or the Paris-Dakar Silver suspension.

Its overly stiff suspension is an existing owner-reported tuning issue, not permission to modify an accepted candidate during this research.

## 19. Validate the common bridge against representative source scenes

Use at least:

- Evo2 Toyota 4Runner.
- Michelin Toyota RAV4.
- Michelin Renault Mégane F2.
- Dakar 2 Xbox Pajero.
- Dakar 2 Xbox Hino Ranger.
- Dakar 2 Xbox Nissan Pickup.

Also retain PC Paris-Dakar Silver and accepted MR vehicles as regression references.

For each source, run the shared conversion preflight and report:

- Import-ready geometry.
- Supported materials.
- Supported wheel mapping.
- Supported glass/damage mapping.
- Unsupported source behavior.
- Any required manual adaptation.
- Whether the output can safely enter the native pipeline.

Do not bypass a failed check merely to demonstrate a successful conversion.

When qualified, build isolated offline native resource candidates or validation fixtures.

Do not install them into the game or allocate new roster IDs during this milestone.

A native-output dry run is not a completed gameplay test.

If a heavy truck requires unsupported native wheel or collision structures, report the exact blocker rather than simulating a successful import with inappropriate SUV mechanics.

---

# PHASE F — Tests, Regressions and Evidence

## 20. Add meaningful cross-format regression tests

Create source-free synthetic tests and original-source validation checks for:

- Geometry conservation.
- Triangle index validity.
- UV conservation.
- Winding and normal transforms.
- Coordinate handedness.
- Source scaling.
- Wheel-side orientation.
- Wheel transform composition.
- Material ownership.
- Multiple texture stages.
- Transparency and alpha policy.
- Glass geometry boundaries.
- Brake-light assignments.
- Original versus derived scene separation.
- Damage-target isolation.
- LOD and equipment variants.
- Deterministic scene serialization.
- Deterministic DX/DXT output.
- Resource allocation limits.
- Path safety and allocation budgets.
- Undo/Redo/Restore.
- Immutability and rollback.
- Existing accepted native vehicle compatibility.

Tests must detect incorrect shared assumptions, not simply encode the current implementation's behavior.

A hardcoded vehicle-specific correction should not pass as a generic-format implementation.

## 21. Add real visual evidence

Use the existing D3D9 Previewer and actual Windows GUI.

For each representative source vehicle, generate:

- Front view.
- Rear view.
- Left and right views.
- Top view.
- Three-quarter view.
- Wheel and window close-ups.
- Material diagnostic view.
- Original versus corrected comparison.

Use consistent normalized camera views when comparing geometry.

Preserve original dimensions and transforms.

Do not nonuniformly scale source models to conceal discrepancies.

Where source-game gameplay references exist, compare with them explicitly.

My original Dakar 2 inspection used PCSX2, while our decoder is based on Xbox resources. Do not claim exact Xbox runtime parity from a PS2 screenshot.

For actual native MR candidates, distinguish:

- Offline compiler validation.
- D3D9 Previewer validation.
- D3D8 owner gameplay validation.

Do not mark an untested candidate as gameplay-qualified.

## 22. Cross-game protection audit

Preserve all existing accepted vehicle projects:

- Subaru Impreza GT3.
- Mitsubishi Lancer Evolution IV GT4.
- Mitsubishi Pajero Rally Raid '85 GT4.
- Heritage Isuzu Trooper.
- Renault Clio V6 GT3.
- Toyota 4Runner Evo2.
- PC Paris-Dakar Pajero Silver.
- Existing RED/Silver source scenes.
- Dakar 2 Pajero, Hino and Nissan source scenes.
- Michelin RAV4 and Mégane source scenes.

Do not modify original MRallye.exe, clean retail Data.sma, installed d3d8.dll, original donor installations, unrelated Randomizer files or protected user assets.

Respect the currently qualified 30-entry roster boundary and alternative CarID29 configurations.

No 31-car capacity experiment.

No copyrighted proprietary game assets in distributable source-only archives.

---

# PHASE G — Results and Acceptance

## 23. Deliver a comprehensive qualification report

Create:

- `SOURCE_GARAGE_QUALIFICATION_MATRIX.md`
- `SOURCE_GARAGE_WARN_RESOLUTION.md`
- `UNIVERSAL_NATIVE_BRIDGE_QUALIFICATION.md`
- Updated Evo2 source and native-compatibility reports.
- Updated Dakar 2 source renderer and native-readiness reports.
- Updated Michelin fidelity and native-readiness reports.
- Source-preserving visual comparison results.
- Reusable cross-format validators and tests.
- Exact regression and preservation reports.

For each previously documented WARN, show one of the following:

**Resolved**
The actual cause was established, fixed and validated.

**Bounded**
The remaining unknown behavior is precisely documented and does not prevent the required MR-native result.

**Unsupported**
The necessary mechanism is genuinely not implemented, with a clear explanation.

**Blocked**
The remaining issue prevents safe import, including a reproducible failure case and the exact missing evidence or implementation.

Do not simply delete warnings from reports.

Maintain a historical record of status changes.

## 24. Documentation and delivery

Update:

- Full Master Plan.
- CAPABILITIES.
- REGRESSION_MATRIX.
- COMMIT_LEDGER.
- Workshop Help.
- Source adapter documentation.
- Native bridge documentation.

Deliver:

1. Unified WARN inventory and resolution matrix.
2. Qualified source adapter fixes.
3. Shared Universal Vehicle Scene improvements.
4. Shared native bridge improvements.
5. Updated representative vehicle previews.
6. Deterministic cross-format preflight results.
7. Explicit remaining unsupported behaviors.
8. Full regression and protection audit.
9. Source-only `source-review.zip`.
10. `changed-files.zip`.
11. A concise recommendation for the next owner-tested native vehicle.

Run focused tests and the full available Windows regression suite.

Use a separate research branch or worktree if appropriate.

Local scoped commits after successful validation are authorized.

Do not push, publish, release or merge unrelated changes without explicit permission.

## 25. Stop conditions

This milestone is focused on existing source engines and the universal conversion pipeline.

Do not automatically start:

- New donor-game research.
- Additional fleet extraction.
- New native CarID imports.
- Blender Bridge implementation.
- Manual beta-livery painting.
- New exterior spare-wheel art.
- Major source-game physics emulation.
- A Master Rallye engine remake or remaster.

Do not expand the scope to complete reproduction of three unrelated original rendering engines.

Spend effort first on actual correctness defects and common MR conversion blockers.

If an original source effect is not needed for native MR conversion and cannot be qualified with available evidence, retain a precise bounded WARN and move to the next blocker.

## Definition of success

Rally Workshop has a thoroughly tested and reusable cross-game vehicle pipeline covering 4x4 Evolution 2, Dakar 2 Xbox and Michelin Rally Masters.

Every remaining critical correctness or native-import issue is either resolved or explicitly reported as a reproducible blocker.

Source Fidelity limitations are separated from native Master Rallye requirements.

The shared bridge handles qualified original geometry, UVs, opaque materials, windows, wheels, lights, transforms and damage-compatible parts without source-specific hidden hacks.

Previously accepted vehicles and source scenes remain unchanged.

At the end, I can confidently select the next vehicle for an isolated Master Rallye gameplay import without discovering basic conversion mistakes that should have been caught in Source Garage.

The objective is not to make all three original games run inside Master Rallye.

The objective is to make **their authentic vehicles transfer correctly and predictably through one reusable SDK architecture**.