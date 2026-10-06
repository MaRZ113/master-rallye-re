# Native anchors / INTERNAL adapter

CONFIRMED_BY_EXE: byte-identical bounded windows, section/RVA checks and fresh
Ghidra12.1.4/ghidra-bridge function exports. Local import projects are ignored;
scratch transactions roll back. Original inputs remain unchanged.

| Owner | VA | RVA | Comparison / semantics |
|---|---|---|---|
| Resource file opening | 64D530 | 24D530 | same CreateFileA resource wrapper; not the Broker singleton |
| Broker Editor Dump route | 65EC40 | 25EC40 | native command2 -> singleton -> walker |
| Broker singleton accessor | 4D8EC0 | D8EC0 | same lazy creation and6F9410 owner |
| Debug logger | 4D0620 | D0620 | same active sink6F7B7C/virtual dispatch |
| Dump walker/formatters | 601D00 | 201D00 | same stock NULL-unsafe StringList/xmlData path |
| Main loop entry | 5AFE30 | 1AFE30 | same bounded native entry |
| Debug sink vtable | 69CEA8 | 29CEA8 | same pointer table, object size30 |
| Active sink slot | 6F7B7C | 2F7B7C | .data zero-fill tail; runtime pointer validated separately |
| Broker manager slot | 6F9410 | 2F9410 | .data zero-fill tail; same accessor references |

The global slots' file/zero-filled initial values are not live pointer evidence.
Native accessor/logger code establishes ownership. Debug helper+0C points to
HWND at helper+4; buffer fields +20/+24/+28/+2C are unchanged. The pinned reader
still validates vtable, pointer ordering, bounds, window and consistent repeated
reads. See machine-readable fingerprints/layout for lengths/hashes.

The existing external four-file implementation is still hash-pinned. For this
one exact Mercedes profile, an INTERNAL in-memory AST derivative changes only
two basename comparisons in broker_observatory and two in mr_observe to recognize
MRallye.exe/MRallye_merc.exe. It retains exact process/file hash and size checks,
native UI command guards, JSON/raw selected-block integrity and unknown
implementation rejection. Four expected comparisons must match; no disk copy
of the public implementation is edited. dev_command_trigger stays original.
The stock/prior research adapter paths continue to use their original imports.

Capabilities and exact profile/registry provenance are attached to captures.
No WriteProcessMemory, injection, debugger, suspension or breakpoints were added.
The public v0.1.0-beta remains pristine-only; this is repository research support.

Mercedes keeps stock60201E dereference and602153 xmlData call. A NULL post-results
PointsList can still crash native Debug->Dump. Active-race only protocol below;
textual empty-list semantics and earlier hardening conclusions are unchanged.
The stock464F69 legacy D:\\SETUP.DLL loading failure->Attract path also remains.
No native hardening patch is applied to Mercedes.
