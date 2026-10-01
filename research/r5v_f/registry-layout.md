# Retail VehicleRegistry storage

## Retail object

Retail `MRallye.exe` SHA-256 is
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
The singleton getter at `0x45A3C0` lazily allocates a heap object with
`operator new(0xC00)` at `0x45A3DF`. The allocation is not a fixed-size global
buffer embedded next to another object.

The object begins with a 4-byte header. VehicleRecord0 starts at object `+0x4`;
each record is `0x34` bytes. The second inline array contains 39 RaceTest
records of stride `0x2C`.

| Region | Retail offset | Expanded offset |
|---|---:|---:|
| Object header | `0x000..0x003` | unchanged |
| VehicleRecord0 | `0x004` | unchanged |
| VehicleRecord25 | `0x518..0x54B` | unchanged |
| VehicleRecord26 | absent | `0x54C..0x57F` |
| RaceTest rows | base `0x54C` | base `0x580` |
| Allocation end | exclusive `0xC00` | exclusive `0xC34` |

Arithmetic is corroborated by the constructor/destructor arguments and their raw
assembly, not used as the sole basis for the patch:

```text
old: header 4 + 26 * 0x34 + 39 * 0x2C = 0xC00
new: header 4 + 27 * 0x34 + 39 * 0x2C = 0xC34
```

The final VehicleRecord ends exactly at `+0x580`, the relocated RaceTest base.
The 39th RaceTest row ends at `+0xC34`, exactly the new allocation end.

## Demo comparison

The September and November demo singleton allocators independently show
`operator new(0x6C4)` and `operator new(0xA84)` for their respective layouts.
Their record stride is `0x24`, unlike retail's `0x34`. The November demo's
27-record array ends at `+0x3D0`, where its 39-row secondary array begins.
Those binaries confirm the heap-object pattern but cannot supply retail
offsets. See [demo-capacity-diff.md](demo-capacity-diff.md).

## Retail addresses

| Purpose | Address | Original → expanded |
|---|---:|---|
| Lazy allocation size | `0x45A3E0` immediate | `0xC00 → 0xC34` |
| Vehicle array construction count | `0x458CF4` immediate | `0x1A → 0x1B` |
| RaceTest construction base | `0x458D12` immediate | `0x54C → 0x580` |
| RaceTest destruction base | `0x458E2C` immediate | `0x54C → 0x580` |
| Vehicle array destruction count | `0x458E46` immediate | `0x1A → 0x1B` |
| Constructor exception unwind count | `0x686796` immediate | `0x1A → 0x1B` |
| RaceTest exception unwind base | `0x6867B3` immediate | `0x54C → 0x580` |
| Record full initializer | `0x45A0B0` | reused for ID25 and ID26 |
| Existing secondary initializer | `0x4598D0` | called once after both new records |

The new record occupies the old RaceTest start, so moving only the count would
corrupt the adjacent array. Every constructor, destructor, unwind and direct
consumer reference listed in [construction-destruction.md](construction-destruction.md)
is adjusted together.
