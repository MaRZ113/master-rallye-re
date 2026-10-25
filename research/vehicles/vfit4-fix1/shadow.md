# Shadow fix1: native deserialization layout

User runtime result: V-FIT4 shadow was still oversized. This is explained by
an admission bug, not evidence that the chosen body footprint needs shrinking.

## Exact cause

Original retail EXE SHA256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
REA Ghidra 12.1.4 original assembly evidence:
`ev_de5fbe282de9cf30ab860e6ae6506adb6b256fb2886c3cfecb572f0ff5019fa5`,
procedure `00553C80`.

The previous wrapper assumed the marker1339 file representation was also the
loaded bounds representation, with a nonserialized header at offset zero.
This assumption was wrong. Native loader allocates exactly 44 bytes. It removes
the file marker and inserts a computed radius-squared value:

| Offset | File footer | Native loaded record |
|---|---|---|
| 00 | marker1339 | centre X |
| 04 | centre X | centre Y |
| 08 | centre Y | centre Z |
| 0C | centre Z | radius |
| 10 | radius | radius squared |
| 14..1C | minimum XYZ | minimum XYZ |
| 20..28 | maximum XYZ | maximum XYZ |

Original instructions `00553CD5..00553D04` establish centre, radius and radius
squared; `00553D69..00553D90` copy minima/maxima. The old comparison of 40 file
bytes against native pointer+4 therefore failed closed and returned unchanged
Navara bounds. Earlier isolated tests built the same incorrect synthetic
native layout, so they did not expose this error.

## Correction

`runtime_bounds()` now reproduces the source-qualified loader layout.
`bind_profile()` emits original and replacement records in this representation.
The wrapper checks all 44 native bytes from pointer+0. Resource key admission
and original full-source/profile pins remain mandatory. The consumer, scope,
footprint policy, source assets, physical parameters and collision are unchanged.

The previous profile remains valid and intentionally unedited. Rebuilding is
required because its derived binding and native payload change. Original sealed
candidates are historical artifacts and are not rewritten.

## Validation boundary

Six proprietary-free synthetic tests pass, including a nonzero-centre/radius
layout fixture. `validate_vehicle_shadow_native.py` now executes original
`00553CA4..00553D9A`, after successful allocation, with only virtual scalar stream
reads stubbed. It checks its actual output against the binding before running
58 admission/register/stack/original-footprint cases. The computed radius square
executes the original x87 instructions; the record has no invented vtable.

Private result:
`.research-output/vehicles/vfit4-fix1/shadow/native-validation.json`.

This proves the corrected loader contract and unchanged original shadow
arithmetic offline. Live resource cache resolution, terrain projection and
visible screenshot comparison still require a new race test. Compare the same
location and camera with the previous no-whine candidate; the rear alpha>=32
support target remains about 0.80 m shorter than the donor-bound footprint.
Stock model keys must continue to pass through unchanged.
