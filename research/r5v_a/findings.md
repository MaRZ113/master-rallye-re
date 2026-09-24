# R5V-A — vehicle registry / slot archaeology

## Result

The final executable builds a heap singleton containing a fixed array of **26 records of 0x34 bytes**. Its constructor explicitly fills **25 named vehicles, IDs 0-24**; the 26th is default constructed and has no confirmed playable meaning. Every named entry has a matching vehicle folder and per-car physics block. `vehicles.xml` supplies physical parameters but does not enumerate the playable registry. Forklift has a resource folder and localized text, but no named registry initializer or physics block.

This is a **mixed, partly hardcoded** system. A new independent slot has **not** been demonstrated. Feasibility class **E — UNKNOWN** pending cross-reference work on the default record, class lists, AI and save bounds. An isolated duplicate of a stock vehicle is the safest first eventual slot payload; Forklift is a separate asset/physics validation problem.

## Evidence levels and method

- **CONFIRMED_STATIC:** EXE constructor instructions, fixed constructor counts, record stride, heap allocation size, and string-to-record associations. Extracted with `objdump` and the two scanner scripts.
- **CONFIRMED_DATA:** shipped XML fields, scene `Car Name` values, asset folders, hashes and file roles.
- **HIGH_INFERENCE:** localization rows at 0x6B99E8 correspond in order to the 25 records plus Forklift. The last three map directly to Icecream, Ufo and Forklift.
- **UNRESOLVED:** actual meaning of record 25; all registry consumers; exact frontend list generation; campaign unlock mapping; savegame binary format; runtime viability of an extra slot.

No EXE, game archive, demo file, asset or Ghidra project was modified or copied into Git. The local Ghidra project exists, but no callable Ghidra installation was available for this run; targeted disassembly and PE string xrefs were done with local `objdump`. Runtime behavior was not tested.

## Read order

- `final-vehicle-registry.md/json`: canonical final indices, folders, physics and source hashes.
- `forklift-analysis.md`: leftover resource assessment.
- `demo-registry-diff.md` and demo JSON files: independent historical inventories.
- `exe-vehicle-registry.md`: constructor, record shape, allocation and version anchors.
- `frontend-vehicle-selection.md`: menu, AI, events and persistence.
- `vehicle-slot-feasibility.md`: go/no-go and R5V-B audit plan.

Reproduce metadata from the repo root with `tools/scanner/r5v_a_inventory.py`, `r5v_a_exe_registry.py`, then `r5v_a_finalize.py`. The JSON stores hashes, sizes and names only. Source paths are supplied at invocation.