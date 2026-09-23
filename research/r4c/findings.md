# R4C findings

## SeatBuggy correction

Before R4C implementation, the unpublished R4B checkpoint was amended with the
independently reproduced SeatBuggy control: car and complete carry the same
3,760-byte tag-101 section and SHA-256
`ea8ddbde932c548fbb09a6557caecb077094843abf228c860b3c28733569d8eb`.
The successful complete-to-race runtime substitution therefore strongly links
tag 101 to collision activation without proving sole sufficiency.

## Writer result

- **CONFIRMED_BY_WRITER_READER:** 28/28 exact tag-101 zero-edit round trips.
- **CONFIRMED_BY_WRITER_READER:** 28/28 byte-identical complete-DX zero edits.
- **CONFIRMED_BY_CORPUS:** all five GeometryBlock vertex families are absolute
  positions/centroid points and translate by D.
- **CONFIRMED_BY_CORPUS:** 27/27 validated hulls pass translation invariants
  and full-DX reparse; Forklift is safely skipped.
- **UNKNOWN runtime:** whether the original game consumes the translated hull
  as predicted. Human testing is required.

## Candidate

The isolated Astero candidate uses `(+0.40, 0, 0)` source units on the lateral
X axis. It changes 132 bytes across 39 source-X float32 fields, with zero
unexpected ranges and zero visual-geometry changes. The file and validation
package are ignored local artifacts.

## Scope boundary

R4C implements zero-edit and rigid translation only. It does not implement
scale, rotation, arbitrary vertex editing, topology generation, BSP/cylinder
writing, Blender collision export, or installation automation.
