# Surprise findings

## Startup key mismatch

Menues/Enabled is the proven startup consumer and gates both the menu/application path and a second capability-checked Debug-window path. The owner now reports that `Menues/Enabled=true` opens the native Debug window and toggling `DebugWindow/Enabled` has no observable effect (**CONFIRMED_BY_RUNTIME**, build details unspecified). The latter remains an **ORPHANED_OR_REDUNDANT_KEY** hypothesis because indirect or unobserved use is still possible.

## Hidden dispatcher behind a two-item menu

The retail main menu contains only Game → Reset / Exit, while the WM_COMMAND switch includes editors, Scene/Game file operations and BuildData. This materially lowers ordinary UI reachability; string/case presence cannot be used as a runtime-reachability claim.

## BuildData reuses ordinary cache paths

Retail BuildData recursively scans DataGx assets and calls ordinary loaders. It does not prove a forced rebuild. A valid cache can be reused and normal model/texture cache writes may overwrite.

## Help paths have no supplied files

Four DataEditors help references are used by constructors, but matching files are absent from supplied corpus views. This may be omitted dev data or stale references; it is not proof of cut content.
