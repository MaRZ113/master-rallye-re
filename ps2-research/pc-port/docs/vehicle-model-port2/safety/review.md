# PORT2 frontend safety review

Read-only review of the accepted source and current frontend evidence. No native hooks, builds, original source edits or runtime mutation were performed.

## Admission decision

Current evidence supports 24/24 Xtrail COMPLETE upload identities and coherent native world rotation, but still explicitly lacks the current CarMover/Egg/en3d/cache-to-VB/IB join. Replacement remains conditional on that bounded investigation. Another COMPLETE candidate has the same missing ownership layer; changing vehicle cannot independently remove this gate.

A usable admission certificate must include current menu scene/selection generation, exact model path/cache owner, current device/reset generation, current upload generations/revisions and exact source draw set. Menu selection can change before en3d cache replacement completes. A selected vehicle ID alone is insufficient.

## Smallest replacement architecture

1. Prepare and validate the complete private PS2 X-Trail resource before suppression: all meshes, materials, texture identities and supported modes must be available. Mode 0 performs no private asset loading.
2. On the verified current frontend owner, inherit its exact finite native WORLD/VIEW/PROJECTION and viewport. Do not reuse fixed translation (8,-2,189) as a transform policy. That value is evidence, not an implementation constant. Validate source local scale/origin before claiming alignment.
3. Suppress only exact current COMPLETE source records belonging to that owner. Wheels inside COMPLETE belong to frontend model; race CAR wheels retain separate native ownership.
4. Render the complete PS2 replacement once at a proven model boundary before later UI, with an explicit material order. Do not replay original PC draws. Avoid incrementally enabling suppression while merely accumulating partial source matches.
5. Retain original menu camera, native lights/material conventions, rotation and selection behavior. A lighting-disabled sprite preview is insufficient.
6. Bind only private visual resources; never mutate native model cache, Egg, physics or original files.

## Reusable components and limits

`frontend_geometry_native.hpp` is diagnostic-only and deliberately cannot suppress. Its current generation/mirror/hash and native transform checks are reusable but its F10 admission and lifetime cap are diagnostic policy, not replacement authority.

`CourseObjectTransaction` is a useful restoration pattern: marks pending BEFORE each setter, restores in reverse order, retains COM references, retries pending restore, emits native-only tracker updates. It is NOT directly suitable for vehicle replacement: it forces WORLD identity, disables lighting/fog, sets transparent/cull-none sprite state, and does not capture material, lights or index binding. Do not widen this class into a global vehicle framework or silently reuse those defaults.

Smallest private frontend transaction should change only required states and retain all native values it changes. Preserve native WORLD/VIEW/PROJECTION when drawing local geometry. A non-indexed DrawPrimitiveUP with private expanded triangles avoids index-binding changes, but still requires stream-0 restoration after successful or failed draw. DrawIndexedPrimitiveUP also changes stream/index state and requires capturing/reinstating original IB and base vertex. Native mock tests must cover side effects after failure. Native state updates must use the established effective-only trace writer; game logical tracker state must remain unchanged.

Existing reflection Scope must not process private frontend draws as native vehicle draws. Place the replacement handler before generic reflection interception and use direct native submissions under its dedicated transaction. Preserve previous body/decal/glass/brake handling for all unrelated submissions.

## Reset and lifecycle

Use existing reset bridge; real Reset must repair/release private resources and invalidate upload/owner certificates. Internal window reset-echo is not a new native device generation. Do not introduce an independent Reset interpretation. Even managed resources should follow the existing release/recreate convention where consistency requires it. Device release/menu exit/vehicle change must clear admission. Resource pointers and numeric IDs must never persist as authority across lifetimes.

If state restoration fails, do not silently return Stock equivalence; preserve pending state for existing pre-submission repair and disable replacement safely. Replacement failure after native suppression requires explicit error handling: do not silently draw nothing. Validate resources/native preconditions before suppressing; mid-submission GPU errors cannot be described as a guaranteed atomic visual swap.

## Focused validation requirements

- Mode 0 does not suppress, load private textures or change states.
- Exact current owner/draw identities accept; same texture/count, wrong cache/scene, stale generations/revisions, selection transition and reset reject.
- All required resources present before suppression; malformed/missing texture or unsupported material keeps Stock.
- Native WORLD/VIEW/PROJECTION preserved; rotation changes across frames; no fixed-camera substitution.
- Successful/private failed draws restore stream and all changed native states, preserving original native HRESULT semantics where applicable.
- Partial setter failures restore attempted slots and retained COM references.
- Device reset/echo/menu changes and MSAA configurations preserve working reflection/grass/water/UI paths.
- In-game Mode 0/1 rotating X-Trail comparison is still mandatory; parser tests or GPU upload are not completion.

Race CAR remains a separate admission and animation/damage contract. COMPLETE replacement must not authorize CAR replacement implicitly.
