# Vehicle Select color presets — separate native UI gate

Status: native in-game selector not implemented in the first editor slice. Existing GT colorways and Evo2 nine-color source scenes remain preserved; Workshop-only selection is not a native menu button.

Proposed identity contract: one physical vehicle identity, stable preset IDs and separate frontend/race resource sets; driver/Results names and HUD marker colors remain independent. A native proof must trace original Vehicle Select input/widgets, resource reload/lifetime, thumbnail/model updates and selected-preset persistence before race entry. AI, Results and re-entry require their own checks. Do not spend one CarID per color as an unqualified shortcut.

Use one already qualified existing vehicle only after the editable/native material boundary is accepted. No new button hook, runtime slot, save rewrite or roster allocation was installed here.
