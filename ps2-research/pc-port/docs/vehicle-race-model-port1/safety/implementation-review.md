# Implementation review - initial CAR chassis integration

Inspected race_model_native.hpp, race_model_registry.hpp, FrontendModel race-role parsing, extension pending-state/reset wiring and staged integration patch. Source review only; runtime still pending.

The proposed 14-record subset (PC 0,1,4..15 excluding 2/3) keeps native trim, drivers, lamp/conditional glass packets and wheels. Its explicit PS2 root map is preferable to COMPLETE reuse. Current source hashes/ranges, buffer generation/revision, queue owner, native matrices and race certificate combine independent evidence; same-camera race admission alone is not the body owner.

Before final submission, add a second complete 14-token validation after capture/preflight and immediately before committed state. Re-read current race generation/lifetime and WORLD; rejoin current queue owner/packet. The existing first-frame token sweep happens earlier than mixed framebuffer capture and material preflight. Reject without suppression if the complete set is stale by commit time. This is especially important for deformed/recreated race buffers. Exact source digest rejects damaged body, but the fallback must be recorded and described as original PC damaged geometry, not PS2 damage transfer.

Check selected private meshes are opaque/source mode 3 or 1. If mode 20 is selected, batching glass at the first original body record needs independent order proof; otherwise leave its native counterpart Stock and omit overlapping private glass. Retained conditional native windows and lamps need an explicit disjoint-surface manifest. Asset role is exact separately pinned CAR.PSM and not frontend COMPLETE.

Pending race state is included in extension, repaired before frontend operations, and normal Reset preflight includes both model transactions; window echo remains before reset_begin. This addresses the principal Reset/resource lifetime concern. Transaction effective notifications remain slot 50 and DrawPrimitiveUP stream restoration is retained. Authored wheel physics are untouched. Existing Terrano brake glow is not a new X-Trail brake implementation.

Runtime acceptance must show genuine moving chassis, native steered wheels and no doubled glass/lamps. The pilot can be accepted as chassis-only even when damage falls back Stock and wheels remain PC, provided those limitations are explicit. No physics safety claim is made by this visual replacement.

## Final review resolution

The final implementation reduces admission to 13 opaque source records, excludes PC record 10 / PS2 root 19 headlight glass, and retains native glass/lamp/driver/wheel packets. Selected roots are 0,1,3,4,6,7,9,10,12,13,14,16,17; source modes 1/3 only, 1,712 private faces. No transparent reordering is introduced by this subset.

race_model_native.hpp now repeats complete 13-token validation, current race generation/lifetime, native WORLD equality and current owner/mesh join after framebuffer capture/material preflight and before committing the private draw. The previously identified stale-precommit gap is addressed. No additional concrete blocker found in this focused source review. This does not substitute for user driving, damage fallback and Reset/MSAA observations; actual chassis pose and retained adjacent geometry require runtime validation.
