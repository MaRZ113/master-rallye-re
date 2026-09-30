# Frontend stats — retail ID25

## Reader

FUN_004819B0 writes the Vehicle Select properties Speed, Acceleration,
Handling and Endurance. For each property it obtains the absolute ID from
FUN_00481E20, obtains the registry object through FUN_0045A3C0, and reads a
32-bit field using stride 0x34.

The accessor returns the registry object base. The first record begins at
base +4. Therefore these effective addresses map to the following record
fields:

| UI property | Effective expression from registry object base | VehicleRecord field |
|---|---|---|
| Speed | base + 0x10 + ID*0x34 | +0x0C |
| Acceleration | base + 0x14 + ID*0x34 | +0x10 |
| Handling | base + 0x18 + ID*0x34 | +0x14 |
| Endurance | base + 0x1C + ID*0x34 | +0x18 |

The exact property strings and direct loads are in
.research-output/r5v_e0_1/core_identity_disassembly.txt around
0x4819B0–0x481D92. No class-local stats table or hardcoded Astero fallback is
used by these reads.

## Why ID25 shows Astero-derived stats

The reader indexes record25 directly after class2 local11 converts to ID25.
R5V-E0 initialized the four record stats with the Astero values
[6, 6, 8, 8]. The same values are present in the stock Astero initialization.
Thus the displayed bars are Astero-derived because the ID25 record was
initialized with Astero-derived stat integers, not because the front end
redirects ID25 to Astero's record.

The values can be controlled through the original full initializer's four
integer arguments without copying the donor object. This is a proven
record-level control point; how the UI scales those integers into bar pixels
is a separate presentation step and was not needed to explain the ID25 result.

## Evidence classification

- local11 -> absolute ID25: **RAW_GHIDRA_SUPPORTED**, FUN_00481E20.
- property reads use the selected record: **RAW_GHIDRA_SUPPORTED**,
  FUN_004819B0 and FUN_0045A3C0.
- ID25 has [6, 6, 8, 8] in the E0 profile: **PROVEN** by the committed E0
  profile/patch documentation.
- Astero-derived display is a record-value effect, not a separate lookup:
  **PROVEN** for the inspected consumer path.

R5V-E0.1 does not change these values.
