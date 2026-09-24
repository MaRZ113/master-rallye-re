# Executable vehicle registry: targeted xrefs

All VAs refer to the **unmodified final** `MRallye.exe` (SHA-256 in the final JSON). This is targeted static disassembly with local `objdump`; Ghidra decompilation was unavailable. These are research anchors, **not approved patch addresses**.

| VA | Evidence |
|---|---|
| 0x45A3C0 | Lazy singleton: if global pointer at 0x6F5ED4 is null, heap allocate **0xC00** bytes, construct at 0x458CD0, cache pointer. Storage is heap allocated but its layout and capacity are compile-time fixed. |
| 0x458E00 | Array construction: **26 × 0x34** records starting at object +0x04; another **39 × 0x2C** array starts at object +0x54C. `4 + 26*0x34 + 39*0x2C = 0xC00`. The second array's semantic role is not established. |
| 0x458E70–0x4598CB | Explicitly initializes 25 named records at object +0x04, +0x38, …, +0x4E4. No literal initializer for record 25, which was default constructed. |
| 0x45A0B0 | Per-record constructor stores ID at +0x04, class at +0x08, four stat-like integers at +0x0C..+0x18, another integer at +0x1C, name object at +0x20 and four float32 fields at +0x24..+0x30. This establishes **0x34 stride**. The +0x1C integer and floats are not semantically named. |
| 0x45A150–0x45A18B | A consumer checks record ID `<= 0x19` (25), then branches through a 26-entry jump table. It is a real registry-associated bound; whether case 25 is a valid vehicle is unresolved. |
| 0x4819B0–0x4819D5 | Vehicle-select code obtains an absolute index, computes `index * 0x34`, accesses the singleton array at +0x04, then calls 0x45A150. This directly links frontend selection to the compiled registry. |
| 0x443D40–0x443E83 | Resource path builder combines `Vehicles/`, a name returned through the selected car path, and `/car`. Adjacent literals include `/wheel` at 0x6B1974. The exact name-provider call has not been fully typed. |
| 0x6B99E8 | English localization rows of 12 bytes include 25 car names followed by Forklift; Ufo and Forklift strings do not themselves register playable vehicles. |

The 25 verified IDs are listed in `final-vehicle-registry.md/json`. Index is not inferred from directory or XML order: each constructor's `lea ecx,[esi+offset]` and last numeric push give the ID and stride. The last numeric push equals the offset-derived index in all 25 records. The preceding push is class 0, 1 or 2 and agrees with the frontend boundaries 7 and 14. A separate first numeric push ranges non-contiguously from 0 to 28; it is retained as an uninterpreted field, not called a resource ID.

## Structural version comparison

| Build | Heap allocation | Registry array | Other array | Literal-initialized names |
|---|---:|---:|---:|---:|
| September | 0x6C4 | 26 × 0x24 | 22 × 0x24 | 6 / 26 |
| November | 0xA84 | 27 × 0x24 | 39 × 0x2C | 24 / 27 |
| Final | 0xC00 | 26 × 0x34 | 39 × 0x2C | 25 / 26 |

Each allocation equals the header plus both fixed arrays. September's 20 and November's three non-literal records reference global name objects whose runtime values have not been established. Do not equate those with usable empty slots. The version progression proves that the developers rebuilt layout and capacity, but no safe relocation or count patch is proved.

## What remains to trace

- All xrefs to singleton 0x6F5ED4, especially direct offsets and 0x34 multipliers outside frontend.
- Meaning of default record 25, jump-table case 25 and every bound around 25/26.
- Initial construction of the frontend vehicle lists for each class.
- Physics name lookup, AI/opponent IDs, and savegame identity/bounds.
- Whether any static arrays elsewhere parallel the 26 records.

The exact patch point list is therefore **none approved**. Addresses above are anchors for R5V-B audit.