# V-SDK4A.1 → V-SDK4C delivery index

Branch `research/vehicles`; local development only, no publication or push.

## Run

- Studio: repository `Rally-Workshop.cmd`, or
  `.research-output/rally-workshop/Launch-Rally-Workshop.cmd`.
- Isolated Subaru glass candidate:
  `.research-output/vehicles/vsdk4c/candidate-glass/Launch-SDK-Roster.cmd`.
- Qualified texture-binding demonstration candidates are indexed in
  `.research-output/vehicles/vsdk4c/binding-release/gui-validation.json`.
  They are separate authoring demonstrations, not the Subaru damage candidate.

## Findings and evidence

- VSDK4A1_RESULTS.md — display-only zoom, original artwork and texture invariance.
- VSDK4A2_RESULTS.md — slot-0 subset, native persistence and offline Help.
- VSDK4C_RESULTS.md — native instructions, root cause, repair, approximations,
  reproduction and targeted owner gameplay checklist.
- COMMIT_LEDGER.md — resolved local phase IDs.
- `.research-output/vehicles/vsdk4c/tests-release.txt` — 814/1 skipped, PASS.
- `binding-release/` — actual Windows picker with image preview, addon/stock GPU
  changes, Undo/Redo/Restore and three candidate builds.
- `help-windows.json`, `offline-help-release.png` — actual F1 event, search and
  context help.
- `glass-acceptance/` — 64 GPU captures and source/native CPU validation.
- `candidate-resource-regression.json` — only Subaru car.dx differs; native
  extension, patch operations and addon plan unchanged.

All private evidence paths above are relative to
`.research-output/vehicles/vsdk4c/` unless otherwise specified. Diagnostic captures
and private runtime resources are deliberately excluded from public source review.

## Source review archives

`.research-output/vehicles/vsdk4c/review/` contains individual changed-source phase
archives and `rally-workshop-vsdk4c-source-review.zip` (clean source/documentation/
test tree), with SHA256 manifests. The supplied SVG/ICO/PNG application artwork is
original CC0 work. Retail/GT models, textures, audio, screenshots, EXEs, DLLs,
archives, compiled launchers and REA snapshots are excluded.

## Remaining acceptance boundary

Run the isolated candidate and test actual front/side/rear damage and race
re-entry. Independent native **zones** are qualified offline; separate front/rear
side-window control and a third shattered state are not claimed. Native game
sorting, trigger thresholds and collision classification still need the owner's
gameplay pass. Other imported cars, fitment, physics, audio, UI and PERF2 paths
remain unchanged.
