# Isolated retail cook workflow — current blocker

## Status

No cook workspace was populated or launched. No command-line cooker entry
point was identified in the retail executable strings; the observed loader is
normally entered through model resource loading. The source GXM texture
references use an absolute `D:/projects/MRallyeTNG/...` root, while the
available corpus is under `D:\Game\Master Rallye\corpora`. The texture writer
uses file output, so a read-only archive fallback cannot be assumed to provide
a writable DXT destination. Until path mapping is validated, staging a clone
would either miss source dependencies or risk writing outside the intended
workspace.

The ignored static-analysis work products are under
`research-output/r5v_f_2a/`. They are not a runtime candidate or cooked package.

## Safe next experiment

1. Work only in ignored `research-output/r5v_f_2a/cook-workspace/` and keep
   `corpora/retail` and `corpora/demo-8.4.1` read-only.
2. Copy the exact hash-locked retail EXE and retail `Data.sma` into the isolated
   workspace. Any extracted or repacked archive must also remain there.
3. Keep the vehicle registry unchanged. Use an existing stock resource path in
   that isolated copy to enter the native loader; treat it only as a cook
   trigger, not as an ID26/Mercedes integration test.
4. Before copying GXM, establish a length-aware rebase for each serialized GXI
   path that maps source reads and generated DXT writes inside the workspace.
   Validate the rewritten files with the current GXM parsers and a byte-level
   assertion that all geometry/hierarchy bytes after the material prefix are
   unchanged. Do not implement a broad GXM writer from the current prefix
   parser alone.
5. Remove only the isolated output cache or otherwise prove its invalidation.
   Capture DebugView output and file-access evidence for each role. Require the
   `Reading GXM` → `Making dx model` → `Saved cached model` chain and matching
   GXI/DXT evidence for source-backed textures.
6. Force `complete` through a preview load and `car`/`wheel` through an offline
   race load in the isolated copy. Do not create an ID26 candidate or use the
   Mercedes UI identity during this asset-only test.
7. Repeat from the same clean input state for Cook B. Hash every DX/DXT and
   validate outputs before packaging.

This is a proposed experiment, not a demonstrated workflow. In particular, the
GXM path-rebase transform and actual cache invalidation have not been proven.

## Data.sma and loose files

Static analysis of `0x0064D530` shows an initial direct `CreateFileA` attempt
followed by a conditional archive fallback for recognized resource roots.
This is sufficient to identify loose-file precedence for an open attempt, but
it does not establish every retail loader call's arguments or a writable
archive path for cook outputs. The exact `.gxi` string → texture stem mapping
also remains incompletely traced. Treat case-folding and path normalization as
unverified; do not claim Windows filename case-insensitivity proves the
engine's internal key semantics.

## Historical cooker context

The beta `research/r-bridge/r-bridge2-demo-910-bridge.md` (beta branch commit
`0fb0a6ff6d89f2fbca5f6600578a2614b9b8f91a`) records owner-reported runtime
success for older-demo source assets cooked by the original Demo-9.10.0
executable, then loaded by retail in existing slots. The available
`corpora/demo-9.10.0/MRallye.exe` is 2,883,646 bytes, SHA-256
`13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78`; it is a
separate historical source-cooker executable, not the retail runtime tested in
this phase. The report contains no exact Mercedes inputs/outputs and no
reproducible command. It is useful as a separate historical bridge, but does
not prove that the retail executable cooked these Mercedes files and is not
substituted for this phase's retail-native evidence.
