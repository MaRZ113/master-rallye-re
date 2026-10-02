# XML/persistence function map

Retail proposed names; mapped operations `CONFIRMED_BY_EXE`. Calling conventions
and complete argument types remain provisional where Ghidra signatures are untyped.

| VA | Proposed name | Evidence |
|---|---|---|
| 00522810 | RequestDataGameXml | path constructor, job/source metadata |
| 005FC950 | QueueResourceRead | links request; optional immediate pump |
| 0054A360 | PumpQueuedResourceReads | loose/archive reader and callback dispatch |
| 0052D830 | OnDataGameXmlRead | parse→Game conversion and status callback |
| 005FDD40 | ParseXmlBytes | buffer XML parser entry |
| 005FDE30 | ParseXmlNodeStream | XML tree construction |
| 0052EEB0 | LoadGameXmlTree | Game/Broker dispatch, merge/replacement |
| 005FE060 | LoadBrokerXmlValues | temporary manager and Value loop |
| 005FE120 | ConvertTypedBrokerValue | typed parser chain, flags/scope/SaveFile assignment |
| 004DFA00 | ParseXmlDataValue | registry class lookup, virtual factory/load |
| 004DEE20 | FindXmlDataFactoryByClassId | factory vector class-ID compare |
| 004D98E0 | GetXmlDataFactoryRegistry | lazy 006F9414 wrapper |
| 00522BD0 | RequestXmlFilenameDependencies | type B plus source SaveFile predicate |
| 00522910 | ResetGameRuntimeAndBroker | owners/reset/defaults/factory reconstruction |
| 005FE460 | SerializeFilteredBrokerTree | mode predicates and entry serializer |
| 005FE580 | SerializeBrokerValue | typed Value and two save annotations |
| 004E0ED0 | SerializeXmlDataValue | class name plus object virtual ToXml |
| 0052EFB0 | BuildGameSaveXmlTree | Game root around Broker tree |
| 005FDCA0 | SerializeXmlTreeToOwnedBytes | formatted text sink and result bytes |
| 005229B0 | RequestDataGameSave | relative DataGame XML target and mode |
| 0052D700 | PrepareGameXmlWriteJob | build tree, bytes, queued ownership |
| 005FC9C0 | QueueOwnedResourceWrite | byte copy and write request |
| 0054A4B0 | PumpWritesWithHashSuffixBackup | probe, CopyFileA, truncating open, WriteFile |
| 0064D030 | CopyLooseFileReplacingBackup | CopyFileA(source,dest,FALSE) |
| 0064D530 | OpenLooseOrReadArchiveCandidate | mode-specific CreateFile/archive fallback |
| 0064D830 | WriteResourceBytes | WriteFile and length check |
| 005B16C0 | SaveRegisteredGameGroups | sentinel exclusions and mode1 requests |
| 005B18A0 | SaveDataGameAsSelectedMode | dialog normalization/retag/request |
| 00403A40 | LoadStartupGameOptionsPlayerState | three immediate read requests in order |
| 0042EE30 / 0042EE40 | ReturnNoXml / IgnoreXmlLoad | vehicle-output virtual stubs |

Old source names are not claimed. Exact build correspondences are in
[build-evolution.md](../persistence/build-evolution.md).
