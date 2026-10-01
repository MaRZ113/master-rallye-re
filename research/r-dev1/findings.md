# R-DEV1 findings

Status: static archaeology complete for gating → dispatch → tool objects → file operations → internal loaders/writers. No runtime action was performed by the research agent; the owner's later flag-isolation result is recorded below and in `runtime-test-plan.md`.

## Architectural result

CONFIRMED_BY_EXE: application startup queues DataGame/Game.xml, parses it into the typed broker, and enumerates XmlFilename broker entries to queue further DataGame XML. CONFIRMED_BY_CORPUS: Game.xml contains Load/Dev and Load/Editors in all four supplied data views. Retail loose-file lookup precedes Data.sma fallback, as recorded in R-EXE1.

The bootstrap reads Menues/Enabled. Static control flow uses it for the application/menu path and a second capability-checked path that creates the separate Debug window. The owner reports that Menues/Enabled=true opens the native Debug window and toggling DebugWindow/Enabled has no observable effect (**CONFIRMED_BY_RUNTIME**; tested build not specified). DebugWindow/Enabled is registered with compiled fallback true but has no consumer string xref in any of the four EXEs; it is an **ORPHANED_OR_REDUNDANT_KEY** (**STRONG_HYPOTHESIS**), not conclusively dead.

The mapped retail main menu is only Game → Reset… / Exit. Its WM_COMMAND procedure routes into a much larger switch with editor, Game/Scene XML and BuildData cases. Thus switch presence and command mapping do not prove a native menu item or normal retail UI reachability.

Retail command 0x58 constructs a command object, installs vtable 00692F88, registers it in a dynamically growing object list, and immediately invokes virtual slot +4 at 005B2F80. That command recursively walks a starting directory and dispatches DataGx .gxm/.gxi/.gxb/.gxp to ordinary model, texture and image-bank loaders. Model/texture cache writers use CREATE_ALWAYS. Existing cache files may be reused; BuildData is not proven to force a rebuild.

Command 0x30 opens Flow Builder. Its own native menu has disabled New/Open/Save/Save As controls, enabled Clear, Speed Matrix, FL-to-SFL and three build modes. The converter reads .fl and writes a sibling .sfl via CREATE_ALWAYS. The main menu builder does not expose the parent Flow Builder command.

Game and Scene XML saving share broker serialization and deferred resource writing. Save flags are 0x1 for Game, 0x4 for Options and 0x2 for Player State. The generic writer opens with CREATE_ALWAYS after a read-only check; no application backup mechanism was found.

The Debug window is a custom GDI window fed by the global formatted logger, not DebugView/OutputDebugString or an Edit child. GXM loader/build stage and shader-selection messages are tied to producer xrefs and calls; equivalent message families survive all four builds.

## New conclusions

1. Development XML is in the ordinary resource/broker startup path and remains present in retail.
2. Menues/Enabled is the only proven startup consumer for the relevant main/debug window path. The DebugWindow/Enabled name alone is misleading.
3. The mapped menu is much narrower than the command switch.
4. Embedded tools are constructed before the menu gate; constructor existence does not imply open/reachable UI.
5. BuildData and Flow Builder reuse normal engine loaders/generators rather than a distinct external toolchain.
6. Flow Builder's FL-to-SFL item is absent in 8.4.1 and present from 9.3.1 onward, matching supplied .fl → .sfl data evolution.
7. Four DataEditors help paths are embedded, but no matching files occur in the supplied corpus views.
8. Retail assembly proves that all nine BuildData counters, including 006FE040, are reset before the recursive walker.

## Principal retail anchors

| Role | Addresses |
|---|---|
| App bootstrap and tool-object construction | 005AFB20, 005AF5C0 |
| XML completion and dependent-config queue | 00522B10, 00522BD0 |
| Main window and dispatch | 005B0880, 005B0990 |
| Main menu builder | 005B1320 |
| BuildData command, walker and callbacks | 005B2960, 005B2F80, 005B2DA0, 005B29C0, 005B2AD0, 005B2C40 |
| Debug sink/window/paint | 0064E4C0, 0064E5C0, 0064EC50 |
| Flow Builder open/menu/dispatch/converter | 00662D90, 00662FB0, 00662E00, 006635B0 |
| Broker Editor | 0065E990, 0065EC40, 0065F170 |
| Game/Scene XML save | 005B16C0, 005B2480, 005FE460, 0064D530 |

## Corpus identities

| Build | EXE SHA256 |
|---|---|
| 8.4.1 | bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be |
| 9.3.1 | 931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680 |
| 9.10.0 | 13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78 |
| retail | bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4 |

Retail Data.sma SHA256: 03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f.

The two demo EXEs in the current supplied corpora folder no longer match the R-EXE1 verified SHA256 values for 8.4.1 and 9.3.1; see R-DEV1.1 provenance/correction notes. This does not change the historical XML values recorded below, but those binaries must be reconciled before treating new cross-build EXE analysis as verified.

## Analysis environment and provenance

R-DEV1 is isolated on branch research/r-dev1-embedded-tools, based on committed R-EXE1 HEAD 27583d3629081a69382609c17171cca59d310113. The active R5T checkout was consulted read-only and was not changed.

Static work used Ghidra 12.0.4 with PyGhidra 3.1 and the local ghidra-bridge exporters. Retail and cross-build project programs were opened without re-running whole-program analysis for export; central functions were selectively decompiled and checked against xrefs, strings, vtables, P-code/CFG and assembly where useful. Conservative function labels were applied only to the ignored R-DEV1 Ghidra project. The raw Ghidra project and proprietary binaries are not part of the commit.

Project evidence reused from R-EXE1 includes the broker/resource architecture, loose-file-before-Data.sma fallback, cache behavior and the retail Data.sma hash. The current phase adds startup/editor gating, menu/dispatch, tool file operations, and cross-build Flow Builder evidence. Project README/docs and R-EXE1 findings were reviewed; R5T course work was not edited or re-concluded.

Committed analysis helpers: tools/scanner/r_dev1_config_inventory.py inventories supplied XML/config and DataEditors corpus metadata; tools/scanner/r_dev1_debug_capture.py lists Win32 windows and optionally OCR-captures the owner-drawn Debug window. OCR needs external Tesseract, absent from this analysis environment. No runtime capture was made.

Limitations: no source/PDB; exact capability implementations and hidden command senders remain unresolved; indirect image-bank writes and several editor internals were not reconstructed; no game runtime operation was performed. Existing whole-program Ghidra analysis options were not retroactively normalized or independently fingerprinted in this phase.

## Evidence boundary

- CONFIRMED_BY_EXE: static strings, xrefs, instruction/control-flow, decompilation and selected assembly.
- CONFIRMED_BY_CORPUS: XML names/values and supplied file presence.
- CONFIRMED_BY_RUNTIME: owner-reported flag isolation: Menues/Enabled=true opens Debug; changing DebugWindow/Enabled has no observable effect. Build/staging details were not supplied.
- UNKNOWN: whether DebugWindow/Enabled affects an unobserved path, normal retail route to hidden IDs, several editor semantics and indirect image-bank writes.
