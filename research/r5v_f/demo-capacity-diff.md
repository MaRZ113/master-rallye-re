# Demo 26→27 capacity differential

The demo comparison is a structural oracle for what changes when developers
increase this kind of retail registry. It is not a source for copying retail
addresses or strides.

| Build | Registry constructor | Record array | Adjacent array | Object allocator | Total |
|---|---|---|---|---|---|
| demo-8.4.1 | `0x4476D0` | 26 × `0x24`, starts `+0x4` | 22 × `0x24`, starts `+0x3AC` | `0x480040`: `new(0x6C4)` | `0x6C4` |
| demo-9.3.1 | `0x44D1C0` | 27 × `0x24`, starts `+0x4` | 39 × `0x2C`, starts `+0x3D0` | `0x44E040`: `new(0xA84)` | `0xA84` |
| retail | `0x458CD0` | 26 × `0x34`, starts `+0x4` | 39 × `0x2C`, starts `+0x54C` | `0x45A3C0` path: `new(0xC00)` | `0xC00` |
| retail R5V-F | same entry | 27 × `0x34`, starts `+0x4` | 39 × `0x2C`, starts `+0x580` | same path: `new(0xC34)` | `0xC34` |

## Matched constructor/destructor evidence

- demo-8.4.1 `0x4476D0` calls the generic array constructor with count `0x1A`
  and stride `0x24`, then count `0x16` and stride `0x24` at `+0x3AC`.
  Destructor `0x447800` mirrors both arrays. Singleton allocator `0x480040`
  requests `0x6C4` bytes.
- demo-9.3.1 `0x44D1C0` uses count `0x1B`, stride `0x24`, then count `0x27`,
  stride `0x2C` at `+0x3D0`. Destructor `0x44D2F0` mirrors those counts and
  base. Singleton allocator `0x44E040` requests `0xA84` bytes.
- The November initializer `0x44D360` contains normal record calls through ID26;
  its final vehicle name is Citroen. That is historical demo data and is not
  used as a retail payload.
- Retail has a different record stride and its own constructor, destructor,
  and unwind functions. R5V-F therefore applies retail-specific counts and
  offsets while following the demonstrated “array followed by array” object
  pattern.

## What the oracle revealed

The 26→27 change in demo-9.3.1 did more than increase the vehicle loop bound:
it also moved the adjacent array base and changed that array from 22 rows of
`0x24` to 39 rows of `0x2C`. Retail already has the 39-row secondary array,
but its base is exactly where the proposed record26 belongs. R5V-F moves all
39 retail rows by one VehicleRecord stride, adjusts all 39 initializer LEAs,
and updates the 11 direct reader displacements. Retail exception-unwind paths
also receive the new base/count so a partial construction failure destroys
only live objects at their expanded locations.

The demo builds do not have Data.sma; their resources are separate unpacked
trees. No demo executable or asset was copied into Git.
