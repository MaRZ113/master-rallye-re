# Michelin RAV4 visual microfix — v8.0

The accepted original candidate remains immutable. The owner confirmed loading,
convincing appearance, natural driving, body damage and breakable glass. Full race
completion/Results have not been confirmed. The two corrected defects still need
an actual owner D3D8 comparison; D3D9 is offline evidence only.

## Wheel diagnosis and correction

Original T0004 indexed wheel texture (`wheel-texture-003`, selected from
Tarmac_t0004.pdo) has source-qualified magenta/index0 coverage. Its decoded RGBA
SHA256 is `4020f5bd5614064f5808162bbdb11e945b41fadd467141917d425011d1ba8ec8`.
The accepted native DXT SHA256 is
`42bea2dde1eeae9e3e076833ee998112e571703ca5f20afd1c90fab741f8ab4e`.
This SDK wrapper contains uncompressed BGRA, not block-DXT compression.

Bilinear sampling interpolates the hidden magenta RGB with visible rim RGB near
the binary cutout edge. Synthetic sampling reproduces the pink contour; actual
fixed-angle D3D9 A/C captures show it, while B/D remove it. The opt-in
`material_derivation.transparent_edge_padding` uses a deterministic row-major
four-neighbour wavefront with radius8. It changes RGB of2419 zero-alpha texels
only. Every nonzero-alpha pixel and every alpha byte remain exact. Source TGA,
palette, cache, UV, geometry, material state and wheel position remain unchanged.
The operation never applies to unrelated atlases. More distant mip/runtime
sampling still requires the owner test.

The common bridge accepts an explicit per-material `transparent_edge_padding`
policy with radius/evidence only for unchanged binary cutout coverage. Default
profiles and the accepted RAV4 project do not opt in.

## Rear lenses: geometry versus texel ownership

The old recipe selected12 corner triangles and520 red-dominant texels within two
rectangles. Exact source UV inspection finds42 intended red-lens texels outside
that mask and54 intended texels not covered by the selected faces. Amber upper
regions and the pale inset must not automatically become brake lights.

`michelin_lamp_coverage.py` pins the exact accepted scene, rear atlas hash and
90-face `body-texture-007` topology. It supplies explicit concave red-lens
contours:336 texels, all covered by10 original source faces including bilinear
support:40,57,58,59,60,68,84,85,86,87. This is conservative reversible **MR
authoring**, not recovered Michelin electrical/shader behavior. Pale inset
reverse/highlight identity remains unresolved and excluded. No blanket red
classification or Toyota recipe is applied to Mégane.

Large faces40/68 also contain opaque painted panels. Merely adding them to the
old unlit replacement would wrongly remove ordinary lighting from those panels.
The common native-state writer therefore offers explicit `masked_overlay`:
OFF keeps the original surface; ON keeps that same diffuse surface and adds an
alpha-tested unlit lens plus bounded glow. Both derived maps have zero alpha
outside the exact contours. The original geometry/UV coordinates do not move;
render overlays are explicit passes, not new source surfaces. No enlarged halo,
body transparency, added body geometry or global two-sided state is used.

OFF and broken-glass surface multisets match the accepted candidate exactly,
including positions/normals/colors/UV/material flags. Collision and bounds suffix
bytes match. The original frontend is unchanged. Emission/glow share the same
explicit contour, independently checked for alpha leakage. Same-plane overlay
depth/filter behavior remains an owner D3D8 validation item.

## Private comparisons and reproducibility

Private root: `.research-output/vehicles/cross-game-materials/rav4-comparisons/`.

| Variant | Change versus accepted resources |
|---|---|
|A|Unmodified copied baseline, original307-resource sealed index|
|B|One rim DXT only|
|C|Race car state packaging and two new lens maps only|
|D|B+C after both independent offline checks|

Each has `candidate/Launch-SDK-Roster.cmd`, a separate resource index and
`manifest.json` listing exact differences. Original executable, native extension,
physics, hubs, audio, crew, camera, glass, damage, shadow, identity, frontend,
roster and other families remain unchanged. B/C/D launchers are rebuilt with the
new trusted hashes; integrity validation is not weakened. No new CarID is added:
the same isolated alternative29 in the qualified30-entry roster is copied.

`tools/create_rav4_visual_comparisons.py` verifies the accepted index, compiles
both derivations twice, checks exact OFF/broken-glass/collision and unrelated
resources, then runs launcher verify/environment/allocation checks. Output must
be fresh inside the private ignored milestone directory. Original files are
never written. A restores the baseline simply by launching its separate copy.

`tools/capture_rav4_visual_comparisons.py` generates final explicit **race**
captures: six fixed views, rear/rear-quarter OFF/ON and outward-facing oblique
wheel close-ups. `final-views/`, `six-views-final/` and `capture-validation.json`
are current. Earlier `views`, `focused-views`, `views-qualified` are superseded
diagnostics: default frontend does not exercise the race brake switch, and the
first diagnostic front-axis convention was reversed. Final images were
regenerated, not relabelled. `lamp-comparison.png`, `lamp-closeup.png` and
`wheel-comparison.png` compare A/B/C/D. Source geometry and textures remain private.

## Focused owner D3D8 checklist

1. Launch A, then B independently on the same course/camera. Inspect both sides
   of the wheels from front/oblique angles, at rest and spinning. Check openings
   remain open with no dark replacement caps or changed tyre geometry.
2. Compare A with C from rear and rear-quarter, brake released/pressed. Both red
   lens portions should illuminate without a cutoff/displaced triangle. Amber,
   pale inset, emblem, bumper and painted panels should remain unaffected.
3. Check C while steering/moving and under different lighting for overlay flicker,
   depth artifacts or leakage. Report exact angle/state if observed.
4. Compare D only after B/C individually look correct. Confirm glass/body damage,
   driving and other already-working systems still behave as before.
5. A remains the rollback. Full race completion, Results and menu re-entry require
   their own owner results; they are not inferred from these checks.

No corrected D3D8 gameplay PASS is claimed by this delivery.
