# Retail Cameras marker list: bounded executable investigation

## Binary identity

Retail `MRallye.exe`, PE32 x86, preferred base `0x00400000`, SHA-256
`BF8AEF32407EB6552C05045B8ABEF149F32983CEDD9503B865069B444C5F96B4`.

## Executable anchors

The `gaCameraManagerParams` class string is referenced by parameter-class
functions at `0x004B7FB0`, `0x004B8930`, and `0x004B8C10`. Indexed strings
`FixedCamera %d` and `FollowCamera %d` are referenced from the latter parameter
readers and `0x004B91E0`. The exact functions read/write fixed/follow camera
parameter records; this alone does not connect their inputs to RaceTest
`MarkerLists/Cameras`.

The string `Cameras` has xrefs in accessors at `0x004B9B20` and `0x004B9B60`.
The `FlyByList` string had no executable xref in the exact Retail string-ref
scan used here. No loader path was found that binds the XML `Cameras` list
records or their `Marker Pos` / `Marker Dir` to these parameter records.

## Status

- RaceTest `Cameras` list: structurally present in 36/36 curated Retail
  courses; 2,975 markers; every marker has Pos, Dir, and Marker Type.
- Executable camera parameter classes and Fixed/Follow properties:
  `CONFIRMED_BY_EXECUTABLE`.
- RaceTest XML `Cameras` list → `gaCameraManagerParams` relation:
  `UNKNOWN`.
- `Cameras` Marker Pos/Dir gameplay use:
  `UNKNOWN` from current evidence.
- `FlyByList` relation:
  `UNKNOWN`.

Blender exposes position helpers and optional Marker Dir rays under the
read-only `Route Research` collection. These are diagnostic previews and do
not assign camera semantics or enable authoring.
