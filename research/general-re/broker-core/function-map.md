# Principal retail functions

Proposed names only; original FUN names/annotations are not rewritten in shared
Ghidra projects. Evidence is `CONFIRMED_BY_EXE` for the listed operations, not
proof of recovered original source names or complete prototypes.

| VA | Proposed research name | Evidence / contract |
|---|---|---|
| 004D8EC0 | GetSharedBrokerManager | singleton allocation/read at 006F9410 |
| 004D4460 | InternExactString | hash candidate lookup, owned copy, numeric ID |
| 004D4B30 | FindInternedExactString | collision-chain byte equality |
| 004D0570 | ResolveInternedText | ID→pool record text |
| 004DD980 | ConstructEmptyBrokerEntry | C tag, scope1, __NO_SAVE, zero revision |
| 004DDC20 | ResetBrokerEntry | payload release then empty state |
| 004DE7B0 | DestroyBrokerPayload | typed release and XmlData virtual deletion |
| 004DEAA0 | CopyBrokerEntry | typed payload copy/clone plus metadata |
| 004D6520 / 004D6650 / 004D6760 | ReadBrokerBool / Float / Int | indexed lookup, type check, default |
| 004D7AA0 / 004D7ED0 / 004D8000 | WriteBrokerBool / Float / Int | grow indexed vector, typed setter |
| 004D84C0 | ReplaceBrokerXmlData | type A replacement/ownership |
| 004D8260 | WriteBrokerXmlFilename | type B interned-name payload |
| 004D8D40 | RemoveBrokerKey | reset slot without ID shifting |
| 004D5DF0 | AssignBrokerRevision | explicit counter assignment |
| 004D5AF0 | AssignBrokerScope | direct metadata field assignment |
| 004D58F0 | AssignBrokerSaveFile | unconditional metadata assignment |
| 004D5FF0 / 004D6200 / 004D6410 | SetGame / Options / PlayerStateFlag | low-bit toggles |
| 004D54A0 | RegisterBrokerSaveFile | linked-list textual dedup/insertion |
| 004D5350 | RegisterLiveEntrySaveFiles | enumerates entry +18 |
| 004D5400 | RetagBrokerSaveFileGroup | old-group compare/new assignment |
| 004D7690 | MergeBrokerManager | nonempty source entries by key ID |
| 004D78C0 | ReplaceBrokerManagerEntries | reset/copy source manager |
| 004D7830 | ClearBrokerStorage | whole reset path |
| 004D7A60 | ClearBrokerEntriesForScope | exact scope predicate; caller UNKNOWN |
| 00601D00 | DumpBrokerDiagnostics | formatted typed values/metadata, skips C |
| 0065EC40 | DispatchBrokerEditorCommand | local IDs and exact Dump case |
| 0065F170 | AcceptBrokerValueDialog | typed live write plus flags/revision/scope/file |
| 006608A0 | ApplyBrokerBranchMetadataDialog | prefix-selected flags/SaveFile mutations |
| 00671570 | DispatchBrokerValueDialog | local parameter commit/cancel notifications |
| 006645C0 | DispatchGenericEditorWindow | nine-slot menu table; only Exit active |
| 00664440 | CloseGenericEditorWithProviderChoice | dirty question and virtual +34/+38 |
| 00674600 / 00674610 | EditToolCommitStub / CancelStub | empty return functions |
| 00676580 / 00676590 | GameEditorCommitStub / CancelStub | empty return functions |

Adjacent maps: [XML functions](../xml-core/function-map.md),
[save pipeline](../persistence/save-pipeline.md), [save modes](../persistence/save-modes.md).
