# R5V-I.0 registry layout

All offsets below are allocation-relative unless identified as executable
virtual addresses. Retail structure and current-branch EXE evidence are
preserved by the deterministic I.0 manifest.

| Field | H.2 parent (27 records) | I.0 (28 records) |
|---|---:|---:|
| Header | 4 bytes | 4 bytes |
| VehicleRecord stride | 0x34 | 0x34 |
| VehicleRecord count | 27 | 28 |
| Record 25 | 0x518 | 0x518 |
| Record 26 | 0x54C | 0x54C |
| Record 27 | absent | 0x580 |
| RaceTest base | 0x580 | 0x5B4 |
| RaceTest count | 39 | 39 |
| RaceTest stride | 0x2C | 0x2C |
| Allocation size | 0xC34 | 0xC68 |

The executable builder changes the registry allocation, the three record
lifecycle counts, and the adjacent RaceTest base used by construction,
destruction and unwind. It shifts 39 initializer LEAs and 11 indexed consumer
displacements from the H.2 parent by one 0x34-byte record. The operation list
contains 81 non-overlapping, byte-verified operations. The 833-byte I.0
wrapper payload is placed at virtual address 0x0068E800 in the fresh audited
zero-filled cave and ends before `.rdata`; the `.text` VirtualSize is extended
to map that payload. No unrelated allocation or table relocation is claimed.

The builder checks every original range against the deterministic H.2
intermediate, verifies the resulting candidate ranges, rejects overlaps and
out-of-bounds changes, and applies the I.0 inverse to recover byte-exact H.2.
The source retail EXE is never modified. Exact source and output hashes are
recorded in [validation](validation.md) and the ignored candidate manifest.
