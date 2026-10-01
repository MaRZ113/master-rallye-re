# Development configuration map

## Bootstrap

At 005AFB20 the application queues Game.xml before reading Menues/Enabled. The application service vtable 0068F4AC has a callback at +0x20 to 00403A40, which queues Game, options and PlayerState under DataGame. 00522810 composes the DataGame path.

XML callback 0052D830 parses the payload and updates the broker. On successful load, 00522B10 calls 00522BD0. That function walks broker entries with 0x1c stride, selects Type 0x0B (XmlFilename), applies a key predicate at 005D1660, builds a DataGame filename through 00522B60, and queues an asynchronous read with 005FC950. Game.xml Load/Dev and Load/Editors are corpus anchors for this generic follow-up path. This report does not claim the predicate is exactly a literal Load/ prefix test.

The resource path uses loose requested files before Data.sma fallback. A missing/malformed config logs a parse error; the completion callback records Default and does not walk the nested XmlFilename branch. Exact startup fallback behavior is UNKNOWN.

## Keys

Corpus values are not guaranteed effective runtime state after defaults, failed loads or later edits.

| Key | Type | Compiled fallback | 8.4.1 shipped XML | 9.3.1 shipped XML | 9.10.0 shipped XML | retail shipped XML | Consumer evidence |
|---|---|---:|---:|---:|---:|---:|---|
| DebugWindow/Enabled | Bool | true | true | true | false | false | default registration at 004D7BD0; no consumer xref found; no observable effect in owner's flag-isolation runtime test |
| Menues/Enabled | Bool | true | true | true | false | false | startup consumer at 005AFB20; gates Debug window in the owner's runtime test |
| ModelCaching/CachingDisabled | Bool | unknown | true | false | false | false | model/texture cache families in all builds |
| Camera0/SwitchTarget | Bool | unknown | false | false | true | false | camera/development consumers; effect untested |
| Camera0/SwitchType | Bool | unknown | false | false | true | false | camera/development consumers; effect untested |
| Scene/HatchEggsOnLoad | Bool | true | true | true | true | true | Scene open/load path |
| Scene/ResetSceneOnLoad | Bool | true | true | true | true | true | Scene open/load path |
| Scene/StartScene | String | unknown | absent | absent | frontend | frontend | runtime consumer not fully reconstructed |
| Editing/EditorsOpen | UNKNOWN | unknown | absent | absent | absent | absent | camera/editor list accessors; do not infer type |

Selected Load/Dev and Load/Editors entries, development/editor keys and DataEditors presence are recorded in dev-config-corpus-inventory.json/.md; unrelated XML values are intentionally omitted.

The shipped XML values above are **HUMAN_CORPUS_VERIFIED** against fresh original build data. Source XML paths, byte sizes and SHA256 values for the supplied corpus files are recorded in `dev-config-corpus-inventory.json`. These values are distinct from compiled fallback registration and the effective runtime value after parsing or later mutation.

## Gating interpretation

005AFB20 reads Menues/Enabled. Static control flow connects that value to application/menu construction and a second capability-checked Debug-window creation path. The owner reports that setting Menues/Enabled true opens the native Debug window, while toggling DebugWindow/Enabled had no observable effect. Thus Menues/Enabled is the Debug-window gate (**CONFIRMED_BY_EXE**, **CONFIRMED_BY_RUNTIME**); DebugWindow/Enabled remains an **ORPHANED_OR_REDUNDANT_KEY** (**STRONG_HYPOTHESIS**), not proven absolutely dead. The tested build and exact runtime staging details were not supplied.

Editor/tool owners are constructed in 005AF5C0 before the menu decision. Disabling the development UI therefore does not remove their constructors from the program.

ModelCaching/CachingDisabled=false permits normal cache lookup/generation. It does not show that BuildData forces a fresh cook; a valid cache may be reused.
