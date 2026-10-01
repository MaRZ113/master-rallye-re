# Surprise findings

## Startup key mismatch

Menues/Enabled is the proven startup consumer and gates both the menu/application path and a second capability-checked Debug-window path. DebugWindow/Enabled is default-registered but has no consumer string xref across four builds. Stale/redundant/indirect use is a STRONG_HYPOTHESIS; independent gate UNKNOWN.

## Hidden dispatcher behind a two-item menu

The retail main menu contains only Game → Reset / Exit, while the WM_COMMAND switch includes editors, Scene/Game file operations and BuildData. This materially lowers ordinary UI reachability; string/case presence cannot be used as a runtime-reachability claim.

## BuildData reuses ordinary cache paths

Retail BuildData recursively scans DataGx assets and calls ordinary loaders. It does not prove a forced rebuild. A valid cache can be reused and normal model/texture cache writes may overwrite.

## Image-bank failure counter may accumulate

005B2F80 clears globals through 006FE03C but uses 006FE040 in its summary without visibly clearing it; 005B2C40 increments 006FE040 on a bank failure. Missing clear in this wrapper is CONFIRMED_BY_EXE. Cumulative behavior is a STRONG_HYPOTHESIS pending complete xref audit or runtime evidence.

## Help paths have no supplied files

Four DataEditors help references are used by constructors, but matching files are absent from supplied corpus views. This may be omitted dev data or stale references; it is not proof of cut content.
