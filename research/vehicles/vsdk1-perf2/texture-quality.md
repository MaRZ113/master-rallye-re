# Explicit texture quality policies

V-SDK1-PERF2 adds a conservative authoring policy, not a loading-delay fix.
All source inputs remain immutable. No game/GT textures ship with the SDK.

## Evidence and options

The original converted Pajero family charges **13,393,920 bytes**, versus
**3,170,304 bytes** after the previous blanket128 limit. Inspection of the
private source texture contact sheet confirms that Nikon lettering, race
numbers and sponsor graphics occupy256px source atlases. The128 output halves
their linear resolution. The DXT wrapper stores BGRA pixels; there is no
additional DXT block compression to blame in these particular converted files.

`normalize_vehicle_texture_residency.py` now requires an explicit legacy
`--max-edge` or one of:

| Preset | Rule | Original Pajero family charge, automatic policy |
| --- | --- | ---: |
| Source Fidelity | Copy every input byte unchanged |13,393,920 |
| Balanced |256 ceiling; protect sampled alpha edges, raise ceiling for detailed/large surfaces |12,607,488 |
| Performance |128 ceiling; preserve alpha edges and raise detailed/large surfaces to256 |11,624,448 |

Balanced changes just one1024x256 broad body atlas to512x128. All256 sponsor
and number atlases remain at source resolution. This is an explicit lossy
option, not proof of exact GT visual fidelity. The private inspected profile
also protects22 identified sponsor/number atlases as `text`; its decisions
override all automatic reduction rules. The automatic Performance figure above
does not include these extra authored protections; consult each output report.

The generic policy uses selected DX surface area, UV triangle area and estimated
texels/metre, sampled RGB gradients, alpha transitions and optional per-texture
importance. It does **not** claim OCR, material recognition, screen visibility
or measured runtime performance. Layered surfaces can contribute overlapping
area. Explicit `text`, `livery` and `alpha-critical` roles preserve original
bytes; `secondary`/`effect` deliberately admit the chosen ceiling. Optional
source hashes prevent stale per-texture overrides from applying silently.

There is no automatic reduction loop that sacrifices protected artwork to hit
a memory number. The report shows the resulting native width*height*4 charge;
the author must inspect the result and the combined roster budget.

## Native cache caveat

The original full-source Pajero plus all four addon families and an explicit
synthetic8MiB world/UI reserve exceeds the retail32MiB texture cache in the
serialized-order simulation:33,784,064 bytes requested,198 steady-frame misses.
This is a **prediction**, not a measured race or the cause of menu hesitation.
Source Fidelity remains available for isolated comparisons. Balanced saves
786,432 bytes relative to that set, but actual world/UI residency is unknown;
passing this particular synthetic reserve is not a universal safety guarantee.

## Reproduce

```text
python tools/vehicle_sdk.py normalize-textures --source PRIVATE_CONVERTED/assets --output NEW_QUALITY/assets --preset balanced --quality-profile USER_PROFILE.json
python tools/vehicle_sdk.py resource-diagnose NEW_QUALITY/assets --reference PRIVATE_CONVERTED/assets --output NEW_DIAGNOSTIC.json
python tools/preview_vehicle.py NEW_QUALITY/assets/complete.dx --resource-diagnostics NEW_DIAGNOSTIC.json
```

The editable profile is version1 with a `textures` map keyed by native texture
stem. Each entry permits `role`, `importance` (finite0..4), `source_sha256` and
an explanatory `reason`. Output must be fresh and outside the source directory.
DX geometry, material references and UV bytes are copied unchanged. Every file
has before/after hashes and every texture has its decision and reasons recorded.

The Previewer now exposes **I** for current draw/triangle counts, reflected/alpha
draw counts, family native texture charge and isolated-layer texture dimensions.
The JSON diagnostic adds per-texture dimensions, UV/area/detail risk evidence,
reference-resolution ratios and explicit unmeasured cold/warm/re-entry fields.
Neither the D3D9 viewer nor Python file timings stand in for original-game QPC
measurements.

## Final Pajero material candidate

The repaired material family adds a source-qualified paint-alpha variant and a
1x1 white texture for black vertex-coloured headlamp housings. It has79 textures:
Source Fidelity charges14,442,500 bytes; the explicit final Balanced profile
charges13,066,244 bytes. Original256-pixel sponsor/number atlases are preserved.
Two low-frequency broad panel maps are reduced under recorded profile decisions;
this is intentional lossy normalization, independent of the lossless reader.

The final four-addon race-family simulation plus a **synthetic8 MiB** world/UI
reserve charges33,521,924 bytes against33,554,432 bytes, with no steady eviction
in that sequence. This leaves only32,508 bytes of headroom. Real tracks/UI can
exceed the assumed reserve: this is **not a measured race safety or FPS claim**.
The native cache remains32 MiB. Source Fidelity is retained privately for
comparison; it is not silently substituted into the combined runtime candidate.
