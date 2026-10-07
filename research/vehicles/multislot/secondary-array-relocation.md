# R5V-I.0 adjacent RaceTest table

The `VehicleRecord` array is followed by a 39-entry `RaceTest` table in the
same allocation. This means adding one record moves the adjacent array even
though its entry count and 0x2C-byte row stride do not change.

For 28 records the base is 4 + 28 × 0x34 = 0x5B4. H.2 used base 0x580, so the
I.0 step moves it by 0x34; pristine retail to I.0 is +0x68. Current-branch
Ghidra evidence found 39 references to the secondary initializer at
`FUN_0045A330`, all from `FUN_004598D0`. The candidate shifts all 39
initializer LEAs and all 11 audited indexed consumers. Constructor,
destructor and unwind base immediates point at 0x5B4, and record lifecycle
counts are 28.

This is static PE/Ghidra and patch-emulation evidence. It does not prove that
all 39 initialized rows have no deeper semantics beyond the audited table, or
that runtime ID27 selection, materialization, physics or cleanup succeeds.
Those remain in the human I.0 slot proof and later independent-vehicle test.
