# Referenced, development, and potentially unused content

## Evidence grading

- **CONFIRMED_BY_EXE/CORPUS**: name/path and consumer or file both exist.
- **DEVELOPMENT_CANDIDATE**: executable editor/cooker/debug code or clearly named test resource exists, but ordinary availability is unknown.
- **UNUSED_CANDIDATE**: evidence of a reference without a known ordinary consumer or matching data file.
- **CUT_CONTENT_CONFIRMED**: requires corroborated reference/data/registry or build-difference evidence. No item reaches this grade in R-EXE1.

## Findings

| Item | Evidence | Grade | Interpretation / next evidence |
|---|---|---|---|
| `BuildData` command family | Retail-only strings, wrapper at `005B2F80`, recursive walk `005B2DA0`, type dispatch to GXM/GXI/image-bank callbacks, and a pointer-table-like reference at `00692F8C`; absent from earlier catalog inventories. | DEVELOPMENT_CANDIDATE | Strongest new development-tool remnant. Owner/dispatch and UI reachability remain unknown; retail code presence is not proof of hidden user access. |
| `DataEditors` / Broker Editor | Editor help path, Broker Editor strings, recursive broker editor node builder and game/scene XML open/save routines in retail; related editor/debug strings survive all four builds. | DEVELOPMENT_CANDIDATE | Development/editor facilities survived. Whether all dialogs open in unmodified builds remains untested. |
| `DataGame/Test.txt`, `DataGame/Test.xml` | Direct string xrefs from test-related executable code in all builds. | UNUSED_CANDIDATE | A test path alone does not show that the packaged asset is missing or that the path is unreachable. Inspect consumer and corpus presence before labeling it unused. |
| RaceTest `Template`, `TemplateNew`, `smash`, `TestFrance1` | Names appear in retail Data.sma inventory alongside ordinary course and test-scene families; executable course-name table has only selected course names as direct references. | DEVELOPMENT_CANDIDATE | May be authoring templates or test assets. No registry-disabled or missing-consumer proof; do not call cut content. |
| Unlock keys `UnlockCars`, `UnlockCups`, `UnlockMasterRallyes`, `UnlockChallenges`, `UnlockInvitation`, `WonAll`, `UnlockAll` | Retail function `004AF030` reads these broker keys; Progress schema contains unlock state. | CONFIRMED_BY_EXE/CORPUS | Confirms an unlock/cheat gate vocabulary, not specific hidden cars/courses or content cut from retail. |
| `Race/RecordReplay`, `Race/CarN/RecordSpline` | Strings survive all four builds, while retail has a concrete GhostPlayback consumer. | UNUSED_CANDIDATE | Recording producer/file format is not mapped. The strings are not proof that a complete replay recorder is reachable. |
| `Editing/EditorsOpen`, `DebugWindow/Enabled`, `Debug/Limits` | Editor/debug setting registrations; Debug/Limits is present in retail. | DEVELOPMENT_CANDIDATE | Configuration registration does not prove the UI is enabled or that the facility is hidden. |

## Conclusion

No vehicle, course, game mode, or retail registry entry is classified as cut or disabled based on the current evidence. Future work should require at least one additional corroborating chain: data file plus consumer, registry exclusion plus otherwise complete content, or a build-to-build removal with matching behavior evidence.
