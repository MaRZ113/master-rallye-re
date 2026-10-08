# Next decision

**Recommend exactly one next phase: PS2-GEOM1.**
Read-only cross-platform visual geometry reconstruction and delta mapping offers
the best return for the current broad PS2 presentation survey. WATER1 proved
useful landscape draw geometry and Turkey3 content deltas; REFL1 now proves
vehicle visual/material subsets with additional wrapper tags. A bounded shared
geometry map can separate authored platform content from renderer differences
across these already established cases. Do not begin it in REFL1.

1. **Static or dynamic reflections?** The body source is a mixed static image
   plus framebuffer-written target. Glass uses an independent static highlight.
2. **What produces the distinctive appearance?** Supported candidates are the
   framebuffer mixture, normal mapping, local-normal grayscale and additive body /
   glass weights. Their visible contribution is not independently captured.
3. **Major resources?** ENVSOURCE supplies the static mix input; RENDERTARGET is
   initialized then written and sampled; WINDSCREEN-REFLECT supplies glass;
   STATICRENDERTARGET is unused in the traced path, other ownership UNKNOWN.
4. **Is coordinate math reproducible?** Yes with explicit normal, matrix endpoints
   and weight, in declared host float32 precision. Live state/FPU parity is pending.
5. **Cross-vehicle?** Tata and Kia use the same handler and packet contract with
   different geometry. Named-child/LOD live activation is not inferred.
6. **Body/glass/chrome?** Body mixed target/FIX128 addition; glass static highlight /
   alpha primary/FIX96 addition; selected chrome lead shares carshiny override.
7. **Shared WATER1 infrastructure?** Real tag2/material/cache/texture/GS/VIF upload
   functions are shared. Body/glass have different modes, source overrides and
   normal selector; the framebuffer writer is separately recovered here.
8. **Known enough for future implementation?** Main static material/source/math /
   blend contract is specified. PC material identity and faithful feedback timing
   still need an implementation design and captured state. No port started.
9. **Required PCSX2 parity capture?** Actual target/source image, two-frame update,
   selected body/glass handles and complete GS state, object/view matrices, weight,
   live VU code and a correlated visible mesh. See offline-validation.md.
10. **Why GEOM1 now?** It advances the requested broad survey without spending the
    next phase on already bounded residency questions. The targeted reflection
    capture remains deferred validation, not another recommended phase here.

Turkey3's proved PS2 puddle content remains a particularly valuable comparison
target in the broader geometry map. Water/grass/reflection runtime limitations
remain visible; no deferred phase is silently declared complete or begun.
