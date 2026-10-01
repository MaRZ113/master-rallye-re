# Retail construction, destruction and adjacent array

## Normal construction order

Retail constructor `0x458CD0` performs the following operations:

1. Calls the generic array constructor `0x5C210C` for 26 VehicleRecords at
   `registry+4`, stride `0x34`, using default constructor `0x45A080` and
   destructor `0x458D60` for unwind.
2. Calls the same array helper for 39 RaceTest rows at `registry+0x54C`, stride
   `0x2C`, using constructor `0x45A300` and destructor `0x458DA0`.
3. Initializes the vehicle configuration sequence for IDs0–24.
4. At `0x458D3F`, calls the secondary initializer `0x4598D0`.

The R5V-F candidate changes the first array count to 27 and the second-array
base to `registry+0x580`. Its hook at `0x458D3F` runs a bounded initializer
stub which full-initializes the existing test Trooper record25, full-initializes
new Landcruiser record26, then calls the original `0x4598D0` exactly once.
IDs0–24 retain their original initialization calls and order.

## Secondary RaceTest rows

`0x4598D0` contains 39 calls to `0x45A330`. Each call supplies `ECX` with an
explicit row address via `LEA ECX,[ESI+disp32]`. All 39 original displacements
from `0x54C` through `0xBD4` are increased by `0x34`, producing a contiguous
range from `0x580` through `0xC08` for the row starts. The constructor stub
does not need to reimplement or duplicate these 39 initializers.

Eleven direct retail consumers contain a base-relative displacement into this
array. Their exact patch addresses are:

```text
0x449CAD
0x45003B  0x4500B0  0x45010E
0x45EC29  0x45EC35
0x47B83D
0x47ED43  0x47ED53  0x47F155  0x47F1F2
```

Each displacement increases by `0x34`. A separate unowned block at
`0x40A6B9` indexes an anonymous runtime object by `EDI*0x1C` and has unrelated
fields around `+0x564..+0x688`; it is not a VehicleRegistry secondary-array
consumer and is deliberately unchanged.

## Destruction and exception safety

Destructor `0x458E00` first destroys the 39 RaceTest rows, then destroys the
VehicleRecords. The candidate moves the RaceTest base to `+0x580` and changes
the VehicleRecord count from 26 to 27. The normal destructor for each record
still runs exactly once; it frees the owned string at `+0x20`.

Constructor unwind handlers are part of the same object lifetime:

- `Unwind@0x686790` destroys the partially constructed VehicleRecord array.
  Its count changes to 27.
- `Unwind@0x6867A6` destroys the partially constructed RaceTest array. Its
  base changes from `+0x54C` to `+0x580`; count and stride remain 39 and `0x2C`.

The complete layout has no gap or overlap: record26 ends at `+0x580`, and the
RaceTest array ends at the expanded allocation boundary `+0xC34`.

## Owned-name initialization

The stub does not byte-copy record25 or ID0. It creates a temporary string
using the existing constructor at `0x4D11D0`, passes all record values through
the established full initializer ABI at `0x45A0B0`, and lets the initializer
deep-copy the internal name into the owned field. The temporary string is
constructed separately for `Trooper` and `Landcruiser` so each record receives
independent ownership. Both record destructors remain on the normal retail
path.
