# Projects, saving and safety

Import an existing SDK author project, a converted vehicle family, or a supported
stock vehicle. Source inputs are hash-pinned. Workshop creates working copies;
it does not edit the retail executable, graphics DLL or donor resources.

Save persists authoring recipes. Undo and Redo recover edit history. Restore
returns to the imported baseline, including texture and surface assignments.
Restore selected surface removes its RGB, environment and texture-binding recipe.

The library lists local projects. Private GT/MR inputs remain local. A source
review archive contains SDK source and documentation, not game resources.

F1 opens this offline help. Topic IDs and locale folders permit translation;
missing translations fall back to English. No network service is required.

## First project tutorial (stock copy-on-write)

1. Choose New stock. Select your local unpacked retail data root, choose a
   supported vehicle and create the private project. The original files stay put.
2. Select Frontend, expand its hierarchy and select a physical draw. Read its
   source ID, native flags and textures. Select a different draw if independent
   vertex RGB editing is disabled because of shared ownership.
3. Set a modest RGB multiplier, such as 0.5 / 1 / 1, and apply the selected-surface
   edit. Compare the GPU capture. This is vertex modulation, not semantic repaint.
4. Save and Validate. Configure build inputs using your existing qualified SDK
   roster candidate, retail Data.sma and unpacked data root. Build creates an
   isolated candidate; it does not replace the installed stock vehicle.
5. Inspect the build report and open its folder. Launch only that candidate for
   a separate gameplay test. Offline preview is not gameplay qualification.
6. Undo, Redo and Restore surface/all are reversible. Restore then Build should
   emit zero stock resource overrides when no other edits remain.

For an imported addon, use Open project and select its existing SDK author folder.
Its source assets, resource namespace and build settings remain independent.
