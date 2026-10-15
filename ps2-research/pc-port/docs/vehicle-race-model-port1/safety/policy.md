# X-Trail CAR chassis pilot safety policy

Review is source inspection, not new runtime acceptance. Frozen renderer is unchanged. This workstream performs no builds, deployment, private native object creation, or physics changes.

## Smallest viable policy

Replace only an independently verified XTRAIL/CAR.PSM chassis subset under the current native chassis WORLD; retain native wheel, driver, animated lamp and glow packets. COMPLETE is not a race source. A source PS2 wheel can only replace a current native wheel draw after a separate owner and its steering/suspension/rotation transform are proved; do not batch those wheels with chassis WORLD.

Admission requires supported EXE, current race generation and chassis owner lifetime, current compiled model/mesh membership, matching current native buffer pair, ranges, generation/revision, exact source geometry identity, and finite WORLD/VIEW/PROJECTION matching effective native state. The existing global live-race certificate alone proves race admission, not which player/AI car owns a draw. No persistent raw owner pointer, draw ordinal, or texture-only identity.

Warmup must collect a complete unique chassis suppression set before any replacement. Before first replacement in a frame, revalidate all constituent upload tokens, owner/race lifetime, and current draw transforms. Changed revision, source hash, missing member, second owner or unsupported transform means the whole target set remains Stock that frame. Never discover damage only after some original records were already suppressed. If race geometry is world-baked rather than chassis-local, preserve its proven conversion/pose contract; copying the frontend local transform assumption is unsafe.

## Damage boundary

Existing reflection damage fallback in reflection_pilot.cpp is explicitly Terrano bumper (324 faces / 330 vertices) and its source UV/topology digest. It does not establish X-Trail damage deformation correspondence to PS2 CAR. For this first CAR pilot, reject any current geometry differing from the certified undamaged source; restore all affected original PC records and allow existing stock/material paths. Record a bounded damage/changed-upload fallback. Do not render undamaged private body over damaged native body or substitute UV equivalence for deformation proof.

## Material and lamp separation

Existing X-Trail decal and glass overrides depend on original PC geometry identities. Private PS2 geometry requires explicit authored mode-to-render-policy mapping; old PC hashes must not classify private PS2 material. Mode 4 capture/environment source remains existing code, with source paint mode 3 selecting reflection and source glass/flat/rubber/lamp modes excluded unless independently supported. Stock animated brake/glow packet should remain native and follow the original brake-state selection; no new per-frame controller reads. brake_glow_native.hpp currently targets Terrano only, so it does not automatically supply X-Trail behavior.

Before suppression, prove whether lamp surfaces live in a separate packet or within the proposed body suppression record. If inseparable and no verified subrange exists, retain that PC record Stock and omit overlapping private PS2 surfaces. Do not leave duplicate lamps or suppress the original brake-on/glow state. Preserve current body/decal reflection path outside accepted replacement.

## Native state, Reset and MSAA

Reuse FrontendTransaction narrow capture, effective-only notification (render state slot 50), dirty-before-set rollback and DrawPrimitiveUP stream restoration. Never alter logical game state. Restore texture refs, shaders, stream, texture transform and every altered render/TSS field; preserve original WORLD/VIEW/PROJECTION unless a separate checked temporary-transform transaction is required. Pending race transaction must join PS2PortExtension::native_states_pending, repair_reflection, normal Reset preflight and final teardown. Failed restore must block further dependent API/reset work, not release retained resources and pretend Stock.

Normal Reset invalidates race identity/upload certificates and owned capture/resources after successful repair. Internal window-mode reset echo must preserve resources and certificates exactly as existing infrastructure does. Failed Reset/device loss disallows private drawing until valid native device and new certificate exist. Managed texture loading is bounded and complete before suppression; partial texture failure releases owned refs and fails closed. Preserve existing mixed_capture MSAA resolve behavior: unsupported capture means Stock, no implicit AA disable.

Frontend batches all private meshes at first original record; this is not automatically race-order safe. Restrict first pilot to verified opaque chassis materials in the corresponding native body interval; keep transparent windows/lights Stock if their ordering/pose is unresolved. Failure after private GPU submission is not atomically rollbackable: report actual HRESULT and disable replacement; do not silently issue original geometry again over a partial private model.

## Required focused verification

Unknown build/owner, same topology wrong car, missing current member, reused resource pointer/new generation, revision change, restart, owner destruction, device reset echo versus real reset, MSAA capture failure, partial texture creation, partial state apply/restore, draw failure, Stock mode, adjacent wheel/glass/glow draws, multiple AI copies and one-per-owner/frame replacement. Confirm suppression excludes every stock wheel and animated lamp packet.

User runtime acceptance must separately cover moving chassis, turns/steering, suspension, front/rear/side cameras, braking, damage Stock fallback, restart, window Reset and MSAA 4x. Unit tests do not establish vehicle contact/pose/visual parity.
