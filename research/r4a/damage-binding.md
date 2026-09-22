# R4A damage and glass binding

## Damage parameters

**STATIC FORMAT FACT:** `Damage.xml` supplies five global maximum values.
`vehicles.xml` supplies per-vehicle `DamageParams` for engine, tyre, steering,
suspension, and gear damage. These are numeric gameplay parameters; neither
file references DX filenames, mesh names, draw IDs, or vertex/index ranges.

**RUNTIME OBSERVATION:** normal Astero `car.dx` supports procedural deformation,
normal damage, and glass breakage. Substituted `complete.dx` does not preserve
that behavior.

## Switchable draw evidence

Twenty-five of 26 car resources contain tag 7 groups with tag 8 children;
forklift is the exception. All complete and wheel resources use tag 2 only.
Car group-label frequency is:

| Label | Files |
|---|---:|
| `blight` | 25 |
| `screenfront` | 24 |
| `screenleft` | 21 |
| `screenright` | 21 |
| `screenrear` | 5 |

For Astero, `screenfront`, `screenleft`, and `screenright` roots use
`windscreen32-tga`; their tag-8 alternatives use `windscreenc32-tga`. The TXT
names pair `screenfront` with `screenfrontb`, and likewise for the side panes.
The `blight` group selects brake-light texture variants.

**HIGH:** tag-7/tag-8 groups are binding points for runtime-selectable
glass/light states. The exact case selector and break trigger are not mapped.

## Glass material evidence

Car sidecars contain 102 literal glass/screen mesh names across 19 resources;
complete sidecars contain 47 across 18. Sidecar materials explicitly preserve
separate `HasAlpha` and `UsesAlpha` values. Astero includes `WindScreen` and
`GlassBroken` materials with alpha-bearing textures.

**HIGH:** intact/broken glass variants are represented by car draw groups and
texture/material tuples. **UNKNOWN:** whether breakage replaces a draw,
modifies vertices, changes collision, or combines several mechanisms.

## Collision/deformation boundary

The `$chull`/trailing-marker correlation is independent of the tag-7/tag-8
glass switches. Static data therefore supports at least two distinct
structures inside the race asset pipeline:

1. a collision-hull-associated car structure;
2. switchable render draw groups for glass/lights.

No static field proves how procedural body deformation maps impacts to
vertices. The marker-101 trailing section is a leading candidate for future
structural research, but its payload must remain semantically unknown until
mapped.
