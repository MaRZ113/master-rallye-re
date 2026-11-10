# Atmosphere 6.18: switch-node lamp attachments

Historical candidate: gameplay exposed a native/source triangle-order mismatch.
See `native-winding-fix.md` for the 6.19 correction and revised probe boundary.

This candidate supersedes the rear-displacement limitation documented in
`geometry-candidate.md` (6.17). It also includes the ID-independent course
material catalogue and the current-frame centre-depth visibility mask.

## Cause and fix

Four Kangoo and six Mattserati rear rig points have no ordinary lamp-texture
draw to bind to. Their real lenses use the body livery in `$switch(blight)`
OFF/ON geometry. Mattserati's upper pair additionally appears in an ordinary
main draw. OFF nodes do not expose the existing fleet-owner stack context.
The previous candidate deliberately preserved static rig placement there.

`tools/atmosphere_lamp_attachments.py` now authors source attachments for missing
rig points without car-name conditions. It selects evidenced switch-lens
triangles, rejects glow billboards and allows passive main geometry only when
its triangles duplicate that lens geometry. It preserves both switch states.
The authoring probe calls the renderer's actual C++ barycentric implementation.

The generated `lamp_attachments.lpa` binds to the exact `lamp_rigs.txt` SHA256
and checksums its own payload. Each record contains the car/point, original
texture pixel identity, expanded triangle-UV identity and barycentric anchor.
Raw and opaque-alpha pixel identities are supported independently. Unknown,
modified, malformed or incompatible records do not receive an attachment.

The renderer captures matching current geometry before body uploads or lens
texture replacements. Position changes do not affect its UV identity; neither
does draw-local vertex reindexing. A bounded current-frame queue resolves switch
ownership before UI rendering, after all verified car poses are available.
Exactly one current-frame WORLD match is required; stale or ambiguous owners
fail closed. Known draw ownership must agree with that match. Race/reset epochs
revoke queued data. Texture identity is cached by resource generation, including
negative results, so this adds no per-frame texture readback.

At resolve time the same current triangle updates the point and its normal.
Tail/brake/reverse roles remain controlled by the existing car state. Points
managed by this sidecar never use the old static rig fallback; missing, removed,
collapsed or unrecognised geometry suppresses them. OFF/ON alternatives replace
the same owner/point instead of creating duplicate glints. The automatic rig
solver and unmatched-car lens detector remain available.

## Evidence

The local source sample contains 25 rig cars and 186 points. Ordinary lenses
cover 176; the new sidecar covers the remaining ten with 20 state-specific rows:

| Car | Points | Passive geometry | Brake ON geometry |
| --- | ---: | --- | --- |
| Kangoo | 4 | OFF `23.2`, `kangoologo128-tga` | `23`, `breaklightson-tga` |
| Mattserati | 6 | OFF `22.2` plus main `18`, `mattl128-tga` | `22`, `breaklightson-tga`, plus main `18` |

Actual-asset runtime-probe cases are OFF/ON multiplied by rest, first-observation
translation, first-observation rotation and local selected-triangle damage.
Every case produces all ten unique points, correct roles and idempotent resolve.
Position error is below `2.4e-7` game metres and axis error below `1.6e-6`.
These are offline source and isolated C++/D3D8 results, **not gameplay acceptance**.
The existing centre-depth probe still covers D24S8/D24X8 with 0/2/4x MSAA.

Native contract tests additionally reject malformed/checksum-mismatched sidecars,
incompatible rig hashes, partial tables, unknown texture/UV layouts, stale and
ambiguous owners, owner disagreement, race/reset mismatch and collapsed meshes.
The new Python authoring tests compile the real C++ math probe and check source
switch qualification, UV serialization and texture identity handling.

## Build and package

Use the current branch and the canonical command:

```
python ps2-research/pc-port/overlay/build_overlay.py
```

The package root `d3d8.dll` is the new renderer. Copy its
`Atmosphere/vehicles/lamp_attachments.lpa` alongside the matching existing
`lamp_rigs.txt` in a copied installation. The package includes that unchanged
rig file for exact provenance; preserve the existing `lamp_masks` directory,
profiles and course material packages. Do not substitute a different rig revision
without regenerating the sidecar. No game EXE, archive or installed game file is
changed by building or packaging.

The sidecar is optional for legacy layouts. A missing/invalid sidecar is reported
by `atmosphere_lamp_attachment_catalogue`; it retains legacy behaviour rather
than pretending the new switch attachments loaded. In the intended candidate
installation expect `ready:true`, 20 rows, and increasing `points_total` in
`atmosphere_lamp_attachment_stats` for these two cars. `signature_misses` may
include unrelated draws sharing a livery; `owner_misses` identifies queued draws
that lacked a unique current-frame car pose.

`comparison-atmosphere6.17/d3d8.dll` is the exact preceding candidate. The
`rollback-installed-atmo-copy` copy is the renderer observed in the named test
installation, with separate recorded provenance. Select one explicitly for an
A/B or rollback. Older DLLs ignore the new sidecar.

Owner gameplay checks remain: both cars with and without braking/reverse, a
controlled collision, camera movement, covered lenses, rivals, race re-entry,
reset, pause/resume and the existing F6 performance A/B. Confirm that actual
game draw UV ordering and switch WORLD ownership satisfy the source certificates.
