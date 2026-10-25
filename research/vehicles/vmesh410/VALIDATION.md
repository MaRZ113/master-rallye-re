# V4.10 validation — v410-exp-002

Status: **PASS offline; new visual behaviour requires the user's runtime test.**

## Evidence

- 121 focused synthetic regression tests passed, including five new finishing-operation tests. Existing V4.5–V4.9, material, geometry, atlas and R4E tests retained.
- SDK vehicle validation, addon project validation/build, author verification, runtime prepare/verify and launcher `--verify` / `--verify-launch-environment` passed. No integrated launch was performed.
- 187 sealed resources compared with V4.9: 181 identical, five declared visual changes, one permitted user-options difference. The changes are `car.dx`, `complete.dx`, `headlamp-tga.dxt`, `mercwheel64-tga.dxt`, `nevwheel-tga.dxt`.
- All retained body triangle attributes compare exactly; only the halo is clipped/replaced. Original lamp caps, glass and upper housings are retained.
- `wheel.dx` byte identical, including recess, tyre shoulder, local origin, radius and width. Existing frontend wheel instances unchanged. No fitment or physics edits.
- Collision suffix exact; all native material flags, texture slots, switch labels/control words identical. Entire lit brake draw retained exactly.
- All 300 halo vertices lie on the source lens triangles at the specified 1.5 mm offset. Halo uses the original case2 material and UV pattern; case1 retained. Released-brake offline images match byte for byte.
- Three edited DXT headers, dimensions and file lengths retained; decoded runtime pixels match project PNG input exactly. Source metal pixels/alpha unchanged. New headlamp swatch does not touch existing lamp pixels or guarded UV footprints.
- Candidate ZIP CRC passed; selected DX/DXT members match runtime output.
- Protected EXE and installed graphics DLL SHA256 unchanged.

## Runtime resource hashes

| Resource | SHA256 |
|---|---|
| car.dx | `acfd863771e5a5dd76cf11f20acc3931927ad807cf8913e1a204facb83fe72c5` |
| complete.dx | `3b0a070515da33d125503089500b674c325984e37a1bcb9b2118cf9eaebaa329` |
| wheel.dx | `3e56f0ee1815519a417329599086bc2453e454431bd533de75e92f0e454a74c2` |
| candidate ZIP | `79020c6d64718b9738d034f77e47ab872243f037b1f1ebf812b7b446b93e7ee8` |

## Visual comparisons

Private `preview/index.html` contains before/after front, oblique front, wheel and brake case comparisons plus reflection OFF/ON diagnostics, rendered from the finished runtime DX/DXT files. The reflection ON approximation adds a constant helper colour contribution; it does not reproduce native environment coordinates, lighting, filtering or mipmaps. These are offline comparisons, not game captures.

Inspected previews show the reflector detail, darker wheel interior, separate rubber sidewall and constrained brake halo. The intercooler backing extends the bounded perimeter without replacing its mouth. Complete gap removal at grazing angles, lamp brightness/reflections, tyre filtering and the new glow's silhouette require Vehicle Select/race verification.

For the user's check: reflections OFF/ON; front from low and oblique angles; wheel at grazing angle; same rear view with brake released/pressed plus an oblique rear view. Baseline brake response was reported correct by the user. No new input response claim is inferred from static geometry or manually selected offline cases.

Full local evidence: `reports/final-offline-audit.json`, `reports/build-validation.json`, `reports/cleanup-operations.json`, `reports/commands.log`, `reports/tests-focused.txt`.
