# V-MESH4.6 — solid seals, selective reflections and reusable wheel conversion

## User runtime evidence for V4.5

The user reports a substantial improvement and supplied five captures on 2026-10-22. This qualifies improvement of the V4.5 appearance in the photographed situations, not all rendering paths. Remaining observations: hard reflection patches at the front bumper edge and rear lamp/lower bumper; a translucent opening below the windshield; gaps at window edges; donor silver wheels.

Screenshots: MRallye_alcXh9qPC3.jpg, MRallye_BwCSM3CJQk.png, MRallye_Jk7ep5SytV.jpg, MRallye_uATts3BeAS.png, MRallye_6bx8ub931q.png in the user's ShareX 2026-10 directory. They are observations, not instructions or reference geometry.

## Candidate changes

- Optional solid coverage now includes classified trim as well as paint. Nonzero source alpha becomes solid coverage; zero holes and actual glazing remain protected. This is a conversion policy, not a reconstruction of GT3 material semantics. It addresses translucent cowl/window-frame surfaces without moving or welding the source body.
- Reflection is assigned by source role independently of opaque coverage: paint 0.58, technical trim/interior 0, opaque tail lamps 0.14. Per-island alpha and gutters carry this control in reflective donor pools; alpha-test pools keep binary coverage. Ordinary glazing and existing headlamp routing remain separate.
- The private GT3 Wheel/Model OBJ contains only a header/object declaration (45 bytes, zero geometry), and its MTL is empty. A source mesh import cannot be claimed. The supplied source disc PNG is usable. The chosen mode reconstructs the donor wheel with radial rings, one curved-edge subdivision and a 36-segment disc carrying that texture. Tyre width, local X axis and hub origin are retained. Donor fixed-size texture slots are authored in place; tread content is retained.
- Frontend embedded wheels are rebuilt from the same local mesh as race, matched through slot-0 texture identities. Each right-hand wheel is mirrored in X with normals and winding corrected. No local offset is baked into a spinning wheel.
- `tools/vmesh_wheels.py` has no Subaru coordinates or material numbers. The builder chooses this donor's rim draw explicitly, accepts `--rim-texture`, and records the input hash and conversion report.

## Evidence boundary

A material-caused gap can be reduced by making its existing trim opaque. Actual missing geometry is not filled by this stage: no arbitrary seal strips or body expansion are introduced. Any remaining geometric seam, clipping or sorting issue requires the user's next captures. Reflection improvements remain candidate hypotheses until viewed in the game; the software preview does not emulate environment mapping, lighting or mipmaps. Gold disc imagery is source-derived, wheel geometry is reconstructed donor geometry, and dark spoke openings remain opaque in this mode. Race hub/track mapping remains H1, with no suspension qualification.

## Build and handoff

Use `tools/build_vmesh46_impreza_experimental.py` with the private `CarModelSet` directory, retail root/exe and V4.5 family as `--before-candidate-dir`. Candidate output: `.research-output/vehicles/vmesh46/v46-exp-002`. Launcher verification only; the user runs the game. No original executable, installed graphics proxy or Randomizer changes. No push/publication. Private inputs and derived assets remain ignored. See VALIDATION.md for final results and package hashes.
