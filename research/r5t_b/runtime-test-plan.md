# Human runtime test plan (R5T-B)

The original Demo 9.10.0 runtime was used only through its normal UI. The owner
selected France1 for two forced identical-source rebuilds in the isolated
clone; the screenshot logs show the course reached `Loaded Successfully`.
Separate owner-provided reports say old-source France1/Italy1 recooked this way
load with AI, retain old start/grid behavior, and can show foliage occlusion
and map-edge flicker.

No new modified-source candidate is ready. The current GXM table recovers node
names/hierarchy/spans, but not source geometry arrays or transforms. Editing a
source mesh span, guessing a vertex offset, or adding material directives to
opaque bytes would not be a controlled experiment.

## Candidate order once the source grammar is sufficient

1. **Foliage alpha-test probe:** isolate one small old source foliage material,
   make exactly one cooker-understood `$alphatest()` / `$shader(tree)` semantic
   change, force DX/DXT regeneration, then compare flags, draw splitting,
   render-sort messages, and all other output hashes. Only prepare a runtime
   candidate if the compiled difference stays localized. Ask whether the
   dynamic-object disappearance changes at that tree.
2. **Startpoint probe:** translate one parsed source startpoint component by a
   visible but safe offset, cook, and inspect which generated data changes.
   Only then ask whether start placement/orientation follows.
3. **Raceline probe:** change one safe section after its source points are
   decoded and shown in Blender; require a localized compiled diff before
   asking about AI behavior.
4. **Bounds/BSP probe:** use a small developer oracle, not France1, and trace
   all generated resources before considering any runtime test.

No candidate from this list was cooked in R5T-B. The two completed unchanged
France1 cooks test repeatability only, not source semantics.
