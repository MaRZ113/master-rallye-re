# V-SDK3 regression and acceptance matrix

Evidence root: `.research-output/vehicles/vsdk3/`. Private captures/candidates
are not shipped in the source archive. Final commands/results are recorded in
the delivery report; failed intermediate GUI runs remain private diagnostics.

| Area | Automated / visual check | Runtime boundary |
| --- | --- | --- |
| Prior tree | Precommit778 synthetic tests,1 skip;43 local phase commits | No historical intermediate revision reconstruction |
| Workshop core | Synthetic source preservation, additive PNG edit contract, alpha, row orientation, invalid parameters, drift, undo/reopen/restore, stock changed-only, resource-only non-installability | No game launch |
| Windows GUI | Actual Tk buttons/dialogs and background SDK operations for one addon and one stock vehicle | Native GUI behavior, not MR gameplay |
| Visible edits | GPU capture differs after edit; original capture restored byte-for-byte | D3D9 diagnostic renderer |
| Builds | GUI compiles author resources and complete sealed external candidate; launcher verification/environment/allocation preflights | User still tests race/menu/AI/re-entry |
| Stock identity | Qualified Megane18/Pajero1 core; zero-edit/restore emits zero overrides; one selected resource changes | No unlock/class/AI/save identity edits |
| Navigation | Native Windows messages exercise orbit, MMB pan, zoom, F3, focus/pick, bookmarks, reload and presets | Not native gameplay camera calculations |
| Renderer regressions | Existing generated asymmetry/UV/culling/glass-depth GPU smoke suite | World lighting/fog/sorting remain approximations |
| Baselines | Compare GUI candidate to input candidate: unchanged DX/wheels, UI/audio/physics/native payload; only chosen DXT differs | Repeated gameplay must be checked by owner |
| Original files | EXE, graphics DLL, source project/resource/archive hashes | Original retail files are never output destinations |
| Privacy | Local build/preview files ignored; source archive excludes retail/GT models/textures/audio/icons and compiled artifacts | No push/publication |

## Owner acceptance checklist

1. Launch Rally Workshop; select a stock/addon project or import one using GUI
   file pickers. Verify status/provenance, Race/Frontend/Wheel views and real
   material/texture fields.
2. Open interactive3D; drag MMB, orbit/zoom, geometric pick, F/Home, F3,
   Ctrl1–6 bookmark/Shift1–6 recall. Verify highlight and texture inspection.
3. Apply a clearly visible whole-texture edit (including baked content warning),
   Save, Validate, Build. Launch the generated candidate yourself.
4. Restore texture/all, reopen the project and rebuild. Confirm stock/addon
   identity and unrelated cars remain intact.
5. Exercise actual game reflections, damage/glass, lights, audio, camera modes,
   UI, AI, finish/Results/re-entry. Prior qualification does not automatically
   cover each newly edited candidate.

Do not mark native gameplay acceptance from the GUI harness or GPU smoke output.
