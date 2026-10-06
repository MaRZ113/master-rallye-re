# `retail-broker-v1` compatibility family

The family fingerprints only the retail executable structures needed by the internal Observatory reader and Broker Editor Dump route. The reusable family definition and required anchor list are in `research/r-observatory-modded-builds/build-profiles.json`; bounded registry fingerprints are separate in `registry-profile.json`.

| Anchor | Role | Family requirement |
|---|---|---|
| `resource_file_open` at `0x0064D530` | Resource/open layout used by the pinned reader | Exact 544-byte fingerprint |
| `broker_editor_dump_route` at `0x0065EC40` | Broker Editor `WM_COMMAND` route, command 2 and call chain | Exact 384-byte fingerprint |
| `broker_singleton_accessor` at `0x004D8EC0` | Native Dump entry / singleton accessor to manager at `0x006F9410` | Exact 144-byte fingerprint |
| `debug_logger` at `0x004D0620` | Logger dispatch through active sink global `0x006F7B7C` | Exact 272-byte fingerprint |
| `native_dump_walker` at `0x00601D00` | Entry iteration and typed formatter | Exact 1,536-byte fingerprint; stock NULL-list behavior is unsafe after Results |
| `main_loop` at `0x005AFE30` | Native UI message loop context | Exact 320-byte fingerprint |
| `debug_sink_vtable` | Expected read-only sink vtable | Exact 32-byte fingerprint |
| `debug_sink_global`, `broker_manager_global` | File-backed/BSS slots; runtime pointer values are not trusted from disk | Zero-filled slot plus exact accessor/logger owners |
| `loading_legacy_failure` | Legacy `SETUP.DLL` load-failure-to-Attract path | Exact 32-byte fingerprint; reports presence, does not patch it |

All addresses are PE VAs at ImageBase `0x00400000`; the report also includes each derived RVA and file-backed section. The route/accessor/logger anchors validate code references and ownership; no on-disk process pointer value is treated as a live pointer.

The PE must be x86 PE32 with the audited timestamp, ImageBase, SizeOfImage, entry RVA, and same section count/order/names/RVAs/raw offsets/raw sizes/characteristics. Only `.text` VirtualSize may differ, and it must remain within its raw extent and below `.rdata`. Anchor bytes are exact; one required mismatch rejects the family. Future families can be added as separate records without weakening this definition.

Broker compatibility is not registry compatibility. A family match may yield `vehicle_registry_profile=unknown`; only the separate registry fingerprints can grant `merc-id26` semantics.
