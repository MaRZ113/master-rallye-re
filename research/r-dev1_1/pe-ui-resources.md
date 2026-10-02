# PE UI resource audit

All four supplied EXEs contain only resource type ID 5 (`RT_DIALOG`) in the resource directory. There are no conventional `RT_MENU`, `RT_ACCELERATOR`, `RT_STRINGTABLE`, `RT_ICON`, `RT_RCDATA`, or custom resource types. This agrees with code xrefs: menus are created dynamically with menu APIs.

| Build | Dialog templates | Dialog controls | Hidden global IDs found as control IDs |
|---|---:|---:|---:|
| 8.4.1 | 24 | 306 | 0 |
| 9.3.1 | 24 | 307 | 0 |
| 9.10.0 | 24 | 307 | 0 |
| retail | 24 | 307 | 0 |

Resource IDs are the same in all builds: `1001, 1002, 1005, 1008, 1009, 1010, 1016, 1018–1028, 1091, 1093, 1094, 1096–1098` (24 IDs total). No dialog control uses an ID in the inclusive `0x26–0x58` range, which covers the hidden editor, generic editor, Game/Scene I/O, and BuildData commands.

The pristine 8.4.1 and 9.3.1 corpus identities are recorded in `research/corpus/executable-provenance.md`. PE resource observations were checked against those pristine `.rsrc` ranges; the previous Ghidra analyses used research-modified copies. Exact resource counts/IDs were parsed from PE data; no binary was modified.

Machine-readable inventory: `pe-ui-resources.json`.

Reproducible scanner: `tools/scanner/r_dev1_1_pe_ui_resources.py` (requires `pefile`; analysis used version `2024.8.26`). It reports the EXE hash, resource types, dialog/control totals, and control IDs within the tested command range. Its pure standard/extended dialog-template parser has synthetic tests.
