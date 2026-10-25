# Pajero rear brake-light qualification

The explicit `native_brakes.source_shapes` profile selects off shape24, on core27 and blended lens26 from the genuine `mits0038` race callback0 branch. Other callback-dependent passes remain outside this switch. Selection is validated against the actual branch difference; absent, duplicate, Boolean, empty or malformed selectors fail closed. Omitting this optional selector preserves the existing Lancer selection behavior.

The source core is an alpha-tested, depth-writing surface, not an opaque full rectangle. Preserve its cutout and existing shared off/core atlas. Only the genuinely blended lens receives the generated lit texture and halo. MR's `ScenePart.alpha` includes cutouts, so testing that flag alone incorrectly treated the core as a blended lens; the builder now distinguishes `alpha_test` explicitly. Both on-state materials bypass damaged diffuse RGB, matching the qualified native light family.

The resulting native `blight` envelope contains one off draw and three on draws (core, lit lens, halo). Source core geometry, UVs and atlas are unchanged. Halo geometry duplicates the lens with 1 mm normal displacement and the same triangle count; it is not an expanded body quad. The glow image intersects stock MR falloff with the original source lens alpha mask. This is a controlled MR approximation; source alpha edges are quantized for native cutout illumination.

`halo_max_edge` optionally bounds only the generated MR halo effect. Pajero uses32, matching the original blended source image width before guarded atlas expansion. The64-wide guarded lit atlas remains unchanged. This avoids a redundant128-wide core copy and oversized packed halo, preserving all previous texture quality settings. Defaults leave Lancer generation unchanged. The generated halo uses deterministic nearest sampling; its visual softness still needs gameplay confirmation.

## Evidence and validation

Private reproducible outputs under `.research-output/vehicles/vpajero3/`:

- `source-profile-r2.json`: explicit callback/shape selection and generated halo ceiling.
- `build-final-r2/assets` and `balanced-final-r2/assets`: qualified source-fidelity and existing Balanced outputs.
- `brake-tests.txt`:11 focused synthetic tests, including malformed selectors, separated cutout/lens ownership and unchanged lit dimensions under the optional halo ceiling.
- `brake-final-validation.json`: actual DX envelopes, material flags, source-aligned lamp bounds and alpha ownership. On-state draws119–121; halo maximum displacement0.001000052 m (serialized float tolerance). No prior DXT changed.
- `native-brake-controller.json`: original retail x86 controller and setter replay. Brake values0,0.099,0.1 select case1;0.101 and1 select case2. Two resource getters are mocked. This is CPU qualification, not live scene registration or gameplay.

Balanced family is13,086,724 bytes,20,480 bytes above the prior Pajero family. Previous sponsor/number textures and normalization choices remain unchanged. The synthetic whole-roster cache sequence is near the32 MiB budget; it is not proof of world/race residency or frame rate.

Human validation must check release/brake/release switching, both rear lamps, halo containment, damaged lamps and normal non-braking appearance. This implements rear stop illumination and halo, not heated wheel discs or front brake effects. Original executables, physics, wheel fitment, UI and audio are outside this change.
