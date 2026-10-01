# Development-tool evolution

## 8.4.1 → 9.3.1

- Flow Builder survives as a matching window/menu family.
- FL-to-SFL menu item is absent in the inspected 8.4.1 menu and present in 9.3.1.
- Supplied data changes from .fl examples to .sfl later, independently supporting converter/format evolution.
- Broker Editor, Game/Scene XML handling, and model-build diagnostics remain.
- Menues/Enabled is default-registered, but its direct consumer string xref is absent in 8.4.1 and 9.3.1. This does not prove the gate was absent.

## 9.3.1 → 9.10.0

- Flow Builder, Broker Editor and model/debug families persist.
- FL-to-SFL remains.
- Camera0/SwitchTarget and Camera0/SwitchType change from false to true in corpus configs.
- Menues/Enabled has a direct consumer xref in 9.10.0.
- The supplied Game.xml load list expands.

## 9.10.0 → retail

- Retail values set Menues/Enabled and DebugWindow/Enabled false, while editor/debug code remains.
- BuildData is confirmed in retail by its string family and the complete ID 0x58 → vtable → recursive walker path. Earlier structural equivalents were not identified; string absence alone cannot disprove one.
- Flow Builder, the converter, cache/model stages and shader diagnostics remain.
- Feature implementation can survive while normal retail configuration disables its UI.

Address matching uses strings, call neighborhoods, UI structure, file filters and equivalent behavior, never raw address correspondence. See dev-tool-correspondence.json.
