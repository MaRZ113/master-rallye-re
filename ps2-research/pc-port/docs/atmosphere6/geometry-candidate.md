# Atmosphere 6.17 candidate

Historical 6.17 boundary. The ten rear switch-node displacement exceptions are
resolved in the newer [6.18 candidate](switch-attachments.md); retain this report
as the evidence for its preceding build.

Source foundation: `a377fe7`, containing the latest Atmosphere/PERF-ATMO2 commit
`beb3967`. Work branch: `fix/atmosphere-custom-courses-lamp-geometry`.

## Independent courses

The old package selector rejected a new scene ID before inspecting its materials.
A course-independent catalogue now supplies exact original texture capabilities
whenever the current course has no explicit rule for that material. It applies
to every course ID, including new material combinations under existing IDs.
There is no list of supported custom IDs and no per-ID cloning requirement.
Category and winding must agree; each pass selects one complete witnessed
material contract, preserving valid Noise/Plain alternatives without mixing
unsupported flag combinations. Explicit
material rules (including Deny) remain authoritative. New opaque `base_noise`
ground can also use the existing AutoGround shader/noise/opacity/geometry proof;
unsupported plain/cutout/environment textures and conflicting roles stay native.
The default package root is `Atmosphere/courses`; an explicit blank keeps the
legacy single-metadata-file route. Spatial normal hints never transfer to a
different scene. See `custom-course-material-reuse.md`.

## Lamp geometry and visibility

The previous lamp rig placed all points at fixed car-space coordinates and kept
those coordinates when recognising a deformed lens. The candidate retains the
automatic rig solver, its units, textures, brake/reverse rules, and the live
section detector for unmatched cars. Recognised rig points bind to the closest
eligible triangle in a recognised rest lens, using barycentric weights. Current
vertex positions and the triangle normal then update their position and axis.
The binding identity includes texture name, stride, full local triangle indices
and UVs. Race/reset changes discard bindings; invalid geometry cannot produce a
front rig point. A first observation already outside the rest-match tolerance
uses the existing live section detector.

An actual-asset C++ probe checks 25 rig cars against their original `car.dx`:
all 72 front points bind; 104 of 114 rear points bind. Rear points without a
current ordinary-lens anchor keep the previous automatic rig placement. These
are four Kangoo and six Mattserati points in separate body-livery OFF/ON nodes;
their damage displacement is **not solved** by this candidate. A current valid
surface anchor replaces the rear fallback by point identity, without adding a
duplicate. Other rig cars are not inferred from the 25-car source sample.

Every lamp type now uses a current-frame GPU depth sample at its centre to gate
the complete glow and streak. A narrow occluder over the centre therefore hides
the entire effect instead of leaving bright sprite edges. The former 35 cm
camera displacement is reduced to a 1 cm numerical surface bias. Back-facing
points no longer receive the unconditional additive glow. Mask/driver failure
suppresses the effect; there is no unoccluded visibility fallback or depth
readback. Scene depth must already be certified by the existing rendering gate.
Transparent geometry that does not write depth cannot be an occluder in this
method; the numerical bias also limits sub-centimetre occlusion claims.

## Verification and owner checks

Canonical build: `python ps2-research/pc-port/overlay/build_overlay.py`.
The local branch lock names this isolated branch; the frozen renderer source,
tree and original hashes remain pinned. Byte-exact archived audit inputs must
retain their Git bytes (a fresh Windows checkout can convert an archived JSON
file to CRLF; restore its audited Git blob rather than changing its checksum).

`tests/lamp_gpu_probe.cpp` exercises open depth, full blocking, a narrow central
blocker, open depth again, and geometry behind the lamp, using D24S8/D24X8 and
0/2/4x MSAA. It also poisons stage 2 and verifies restoration of shader, target,
depth surface, viewport, Z-write, alpha test and texture stage operation. The
original-geometry fixture checks rigid translation/rotation and normals. Native
contracts also cover invalid, removed and collapsed geometry, metadata conflicts,
unknown textures, explicit-package precedence and corrupt-package rejection.

All of these are offline or isolated D3D8 evidence, **not gameplay acceptance**.
Use a copied installation with its current Atmosphere assets and profiles. Replace
only the renderer DLL for the A/B test after backing up that copy's DLL. Preserve
`Atmosphere/courses/*/materials.lsm`, vehicle rigs/masks, and the existing INIs.
The candidate has no new required assets or configuration keys. Do not silently
chain another `d3d8.dll` proxy.

Owner gameplay gates:

1. Same independent course/new ID and fixed preset/CloudNumber, before/after.
   Check roads, terrain, vegetation, static objects and headlight pools; inspect
   `atmosphere_course_package` for the shared catalogue SHA and, with no authored
   package, `reused_original_texture_capabilities_ready`.
2. Repeat a stock course and a custom course with its own explicit package.
3. At night, observe front lamp positions before/after a controlled collision,
   then rotate the camera and cover the lens with damaged geometry. Check rival
   cars too. A covered centre should leave no glow or streak edges.
4. Verify brake and reverse roles, including Kangoo/Mattserati rear fallbacks;
   retain their stated displacement limitation when evaluating the candidate.
5. Reset/re-enter a race with another car, change cameras, pause/resume and check
   the existing F6 performance A/B. GPU-mask cost and in-game frame time remain
   unmeasured until this test.

No installed game files, executable, archives, saves or existing worktree changes
are modified by building or packaging this candidate.

## Package contents

Use the **root** `d3d8.dll` as the candidate. `validation.json` records its SHA256
and exact validation boundary; `SHA256SUMS.txt` covers the package files.
`comparison-perf-atmo2/d3d8.dll` is the previous Atmosphere/PERF-ATMO2 release
(`cad90ece...`) for a controlled comparison. `rollback-installed-atmo-copy/d3d8.dll`
is a separate byte-for-byte snapshot of the renderer found in
`D:/Game/Master Rallye Atmo-copy` while packaging (`99d3ba54...`); its version is
not inferred from that path. Choose the appropriate comparison/rollback copy
explicitly, rather than extracting every DLL into the game directory.

`existing-assets-provenance.json` inventories the existing course material
packages and lamp rigs/masks; it is a provenance reference, not an installer.
The package does not replace INIs or game assets. `source/` and `changes.patch`
contain the candidate changes; `evidence/` contains the native catalogue and
isolated lamp-depth reports and original-geometry probe.
