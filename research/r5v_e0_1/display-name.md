# Display name and localization — retail ID25

## Dataflow

The active Vehicle Select update is FUN_004819B0. It calls
FUN_00481E20 to convert the current class-local position to an absolute
vehicle ID. For class 2, the helper adds 14; local 11 therefore becomes ID25.
The screen then calls the unlock checker FUN_0045A150 and updates the
Frontend/VehicleSelect/CarModel setting.

On the unlocked path, FUN_004819B0 queries the localization/config object
returned by FUN_00485CF0 twice:

- group 0x33, indexed by the absolute vehicle ID, for the manufacturer label;
- group 0x34, indexed by the absolute vehicle ID, for the model label.

The call-site argument flow is visible in the raw Ghidra extract
.research-output/r5v_e0_1/core_identity_disassembly.txt around
FUN_004819B0. The calls are not indexed by T3 local position and do not read
VehicleRecord +0x20. They use the absolute ID produced by FUN_00481E20.

At ID25, the owner reports the rendered label STEEL MONKEYS FORKLIFT. Retail
EXE string data contains FORKLIFT and STEEL MONKEYS FORKLIFT literals at
0x006E0B0C and 0x006E0924. The combination of ID-indexed localization lookup,
the retail literals and the human runtime result strongly supports the current
ID25 label. The exact localization-table entry-to-literal xref is not
preserved as a direct raw table dump, so the rendered mapping is classified
STRONGLY_SUPPORTED rather than independently reproduced.

The locked branch is distinct: it writes CarModel = -1 and uses a separate
group-6 selector based on ID. That path does not describe the owner's unlocked
ID25 display.

## Trooper identity

The internal resource name Trooper is stored in the owned VehicleRecord string
at +0x20 by the E0 initializer. It selects runtime resources independently of
the localization groups. No retail Trooper display string or Trooper-specific
Vehicle Select localization row was found in the targeted retail UI/config
search. The demo-8.4.1 Trooper hit is a main-menu scene model reference, not a
display-name entry.

Therefore:

- current absolute slot: ID25;
- localized display identity: Forklift;
- internal/runtime resource identity: Trooper;
- the display label is not derived from the internal resource string.

## Evidence classification

- ID25 derived from class2 local11: **RAW_GHIDRA_SUPPORTED**, FUN_00481E20.
- Manufacturer/model lookups keyed by absolute ID: **RAW_GHIDRA_SUPPORTED**,
  FUN_004819B0, groups 0x33 and 0x34.
- Rendered STEEL MONKEYS FORKLIFT at ID25: **STRONGLY_SUPPORTED**, raw
  selector path plus retail literals and owner runtime report.
- Trooper display string available in retail frontend data: **not found** in
  the targeted search.
