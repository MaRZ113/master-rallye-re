# Phase R2.5 findings

## Outcome

The recovered texFinder archive was classified as historical evidence. No
legacy source or game asset was vendored. Reproducible findings were
reimplemented against the canonical R1/R2 architecture.

## DXT encoder proof

The conservative writer preserves the exact 20-byte template header, requires
the original dimensions, converts upright RGBA to stored bottom-up BGRA, and
replaces only the pixel plane. Raw `DxtTexture.bgra` and `header` remain
forensic source data.

- Modern corpus test: **1,143/1,143** vehicle DXT files byte-identical after
  parse -> upright RGBA -> encode; 26 families, 11 dimension pairs, 0 header
  differences, 0 payload differences.
- Of these, 153 contain non-opaque alpha values.
- Independent actual legacy pipeline: **6/6** byte-identical samples across
  Astero, Forester, Pajero, ChevyBlazer, Ufo, and Bruno, including 8x8,
  16x16, 32x32, and 128x128 images and alpha-bearing examples.

Evidence: `dxt-roundtrip.json` and `legacy-dxt-roundtrip.json`.

## DX writer generations

v1 demonstrates a safe template-patch principle. Astero complete achieved a
byte-identical zero-edit round-trip with `positions-only/no-bounds`; changing
one X coordinate changed one byte and the modern parser still validated every
known topology/draw structure. Default v1 is not bit-preserving because its UV
and 40-byte-footer behavior changed 338 bytes.

v2 is shape transfer, not serialization. It is retained only as a possible
future experimental authoring concept.

v3 is rejected: its Astero complete output parses but fails modern validation,
including 6,285 reconstructed/stored global-index mismatches and invalid local
ranges. See the dedicated analyses.

## Sidecars and TXT metadata

`resolve_sidecar()` now scores every same-directory TXT candidate using
normalized ordered texture tuples, unique/ambiguous/unmatched draw matches,
mesh-span compatibility, and weak filename hints. An exact stem receives only
a small bonus and cannot override substantially stronger structural evidence.
Ties remain explicitly ambiguous.

Across all 78 vehicle DX resources, a unique scored candidate was selected for
78; 12 selections were non-exact-stem. Candidate scores and alternatives are
preserved in `sidecar-resolution.json` and Blender object JSON. This is a
best-evidence selection, not a newly discovered binary material index.

`SidecarTexture` now preserves nullable `has_alpha`, `uses_alpha`, and
`is_noise`; Blender metadata serializes all three.

## Read-only asset audit

`mrtool audit-textures` reports present DXT files and references from both DX
draws and all TXT sidecars. It never moves, renames, or deletes files. The
vehicle audit found 1,143 present, 87 apparently unreferenced, four missing
references, and zero parse errors. All four missing names occur in
`forklift` and are common driver/helmet resources; this is reference evidence,
not permission to alter the archive. “Unreferenced” never means safe to delete.

## R2.2 regression and warnings

Blender 5.2.2 LTS headless synthetic import/save/reload passed. Real validation
passed for 19 resources across Astero, Pajero, Forester, Bruno, Ufo, megane,
and ChevyBlazer; all remained `SOURCE_IDENTICAL` after reload. PNG row,
Blender direct-V, glTF flip-V, normal provenance, and stable calculated display
normals are unchanged.

Remaining importer warnings:

| Resource | Exact warning | Classification |
|---|---|---|
| `Pajero/car.dx` | `declared top-level count 28 differs from reconstructed root count 29` | **EXPECTED_DIAGNOSTIC**; exact stored-global validation still passes |
| `ChevyBlazer/car.dx` | `declared top-level count 31 differs from reconstructed root count 32` | **EXPECTED_DIAGNOSTIC**; exact stored-global validation still passes |

Astero and Forester folders reported zero importer warnings; Pajero reported
the one diagnostic above. Folder import now also prints each warning with its
resource name, so the summary count is traceable. Blender save messages about
absolute temporary image paths are application-level path diagnostics, not
Master Rallye importer warnings.

## R3 readiness

**READY**, with a deliberately narrow sequence:

1. R3.1: binary-preserving template serializer; prove zero-edit and
   same-topology positions-only output.
2. R3.2: expose same-size template-preserving DXT replacement.
3. R3.3: Blender positions-only export with strict provenance/count gates.
4. R3.4: change one vertex, emit one modified DX, then require human
   Master Rallye runtime validation.
5. R3.5: only after runtime proof, add gated UV/normal/material edits.
6. R3.6: defer topology-changing output until draw/tag/trailing construction
   has additional evidence.

R2.5 implements none of those DX export stages.
