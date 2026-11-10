# Independent course lighting

The package selector previously required `LightingPackageRoot/<scene ID>/materials.lsm`
before inspecting any draw. A new independent RaceTest scene therefore rejected
all universal lighting with `course_package_missing_invalid_or_wrong_scope`, even
when its material textures were byte-identical to certified original materials.
This is a source-confirmed gate failure; it does not by itself establish an
observed gameplay result.

The selector now derives one ID-independent Common material catalogue from
existing course packages. It applies to every draw missing an explicit material
row, including future courses, mixtures of original assets and modifications
under existing scene IDs. No active scene ID is copied into catalogue records.
Every donor must pass the existing
LSM checksum, format, capability and single-course scope checks. Lookup still
uses the exact runtime texture SHA. Category and winding must agree across all
occurrences. Each generic pass must match the complete required flag mask of one
original witnessed material contract. Alternative Noise and Plain bindings remain
separate; optional flags are never combined across donors. A semantic conflict or
explicit exclusion produces sticky Deny. A known texture without a supporting
pass remains known and unsupported, so it cannot fall through to AutoGround.
Consistent environment-texture certificates retain their certificate-only role.
Unknown or edited textures do not gain a material capability from the catalogue.
They retain the existing AutoGround path only for proven opaque, unblended,
non-alpha-tested base_noise ground: the exact native noise texture, shader stages,
resource and geometry checks remain mandatory. Unknown plain, cutout and
environment materials retain native rendering. This is not a claim that all
arbitrary new materials are supported.

A present per-scene package remains authoritative: its rows, including explicit
Deny and authored roles, override the Common catalogue. Missing rows inherit
Common. Missing material files, corruption and wrong scope in that directory
block that scene rather than bypassing its package. Invalid donor packages
reject Common reuse; a separately valid scene package can still use its explicit
rows and established AutoGround policy. Normal hints describe source positions, so they are
never copied across scene IDs; independent geometry computes its own normals.
The metadata diagnostic SHA for reuse hashes the sorted donor scene and payload
SHA manifest. `reused_original_texture_capabilities_ready` identifies a
catalogue-only selection; `shared_catalogue_sha256` identifies the catalogue
attached to an authored package. Catalogue construction occurs at selection or
reload, never for individual draws.

The standard package root defaults to `Atmosphere/courses` when the INI key is
absent. An explicit path remains authoritative; an explicit blank key retains
the legacy single-metadata mode. Both the package-selection diagnostic and the
resolver metadata diagnostic include catalogue provenance.

Deployment requires the existing `Atmosphere/courses` material packages alongside
the updated DLL. Existing and future courses using supported native materials
need no ID registration or per-course material copying. Genuinely new material
contracts still need source qualification; unsupported shader semantics are not
guessed from a texture name. Runtime verification should compare the
same independent course and preset before/after, inspect the package diagnostic
and F10 coverage, and repeat a stock course plus an explicitly packaged custom
course. Automated metadata and geometry tests do not establish visual acceptance.

The installed dataset at `D:/Game/Master Rallye Atmo-copy/Atmosphere/courses`
contains 59 packages, 6,873 rows and 530 distinct texture identities. The shared
catalogue retains 514 identities: 53 road, 135 terrain, 100 vegetation and 226
static (including 37 with a witnessed environment-capable variant).
Twelve identities remain denied and four remain environment certificates only.
Requiring every optional flag
to be identical would retain only 492 identities and unnecessarily exclude native
`grass-tga`, `basegrass-tga`, `pavement-tga`, `f_conc-tga` and several static props.
The catalogue preserves every witnessed Noise/Plain alternative for these
materials instead of removing a valid Plain pass because another course used
only Noise. For example, Plain|AlphaTest and Noise do not prove Noise|AlphaTest.
These are metadata counts, not measured draw or visible pixel coverage.
