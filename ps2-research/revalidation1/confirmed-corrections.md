# Corrections applied

**No code or historical research correction was applied.** This audit found
no reproducible source-level error that meets the correction rule in the
request.

The audit does make two evidence-provenance refinements in this new report:

1. `0x005867a0` has a file mapping in REA but no Ghidra-defined procedure in
   the current project. The state map is corroborated by GNU objdump over the
   same immutable PC PE bytes, not by a fresh REA decompilation.
2. The PILOT1.3 runtime counts, state restoration, frame ordinals, and visual
   outcomes are carried as `USER_RUNTIME_OBSERVATION` because the original
   log/screenshots are absent from this checkout.

These are provenance qualifications, not silent rewrites of prior
conclusions. No additional tests were necessary for documentation-only
qualifications.
