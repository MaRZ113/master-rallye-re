# Vehicle runtime roles

Phase R4A separates five evidence classes: **RUNTIME OBSERVATION**, **STATIC
FORMAT FACT**, **DATA LINK**, **INFERENCE**, and **UNRESOLVED**. A structural
correlation is not promoted to runtime causality.

## Confirmed roles

### `complete.dx`

- **RUNTIME OBSERVATION / CONFIRMED:** presentation/menu vehicle resource.
- **STATIC FORMAT FACT:** present in all 26 vehicle folders; tag 2 only in all
  files; no literal crew mesh names in any structural sidecar.
- **STATIC FORMAT FACT:** 25/26 contain four or five non-spare wheel meshes by
  name. Ufo has neither a separate `wheel.dx` nor named complete wheels.
- **HIGH:** presentation assembly normally includes its visible wheels. In 22
  normal families, the complete model contains 100% of the separate wheel's
  quantized rigid-invariant edge signature with a minimum four-copy
  multiplicity. IceCream, Kamaz, and Navara are named-wheel outliers whose
  separate and embedded geometry signatures differ.

### `car.dx`

- **RUNTIME OBSERVATION / CONFIRMED:** race body/chassis resource.
- **RUNTIME OBSERVATION / CONFIRMED:** same-topology position edits preserve
  collision, deformation/damage, and glass breakage when this resource retains
  its original structure.
- **STATIC FORMAT FACT:** present in all 26 folders. All have opaque trailing
  data beginning with raw u32 `101`; its semantic name remains unknown.
- **STATIC FORMAT FACT:** 25/26 use tags 2/7/8; forklift uses tag 2 only.
- **CONFIRMED_BY_NAME:** every selected structural car TXT has crew-associated
  names; 25/26 have `$chull(...)` and forklift is the exception.

### `wheel.dx`

- **RUNTIME OBSERVATION / CONFIRMED:** instantiated separately by the race
  runtime.
- **STATIC FORMAT FACT:** present in 25/26 folders; Ufo is the exception.
- **STATIC FORMAT FACT:** every wheel resource has 252 triangles, one UV set,
  tag 2 only, four or five draws, and the recognized 56-byte bounds footer.
- **HIGH:** it is a reusable visual wheel template. Runtime observation proves
  separate instancing; static data does not expose the instance transforms.
- **UNKNOWN:** wheel/suspension physics does not follow from visual geometry.
  Physics parameters live separately in `vehicles.xml`.

## Structural binding evidence

Twenty-four standard car sidecars satisfy this exact relationship:

```text
TXT source mesh span - compiled render triangle count
    = named $chull(...) triangle span
```

Pajero uses a nonstandard `Pajero.txt` structural sidecar whose exporter span
does not reconcile with the compiled car, and forklift has no named hull.
Every car nevertheless has the raw trailing marker `101`. SeatBuggy is the
only complete sidecar with `$chull(...)`; it is also the only complete trailing
section beginning with `101`. The other ordinary complete files use the bounds
footer (Ufo has a separate 44-byte opaque outlier).

This is **HIGH** evidence that `$chull` source content and the marker-101
trailing family participate in the race collision structure. It does not yet
prove the exact trailing layout, that collision is wholly stored in `car.dx`,
or how the runtime activates it.

## Resource graph

```text
Vehicle identifier/folder
├── presentation visual -> complete.dx                  CONFIRMED runtime
│   └── embedded presentation wheels (25/26 named)      HIGH
├── race body/chassis -> car.dx                         CONFIRMED runtime
│   ├── crew meshes                                     CONFIRMED_BY_NAME
│   ├── tag-7/tag-8 glass/light state groups (25/26)    HIGH
│   └── $chull + marker-101 structural family           HIGH association
├── race visual wheel template -> wheel.dx (25/26)      CONFIRMED runtime
├── chassis/wheel/suspension physics -> vehicles.xml    CONFIRMED data
├── damage thresholds/strengths -> vehicles.xml         CONFIRMED data
├── global damage maxima -> Damage.xml                  CONFIRMED data
└── convex-hull tolerances -> collision.xml             CONFIRMED data
```

No XML field was found that directly names `car.dx`, `complete.dx`,
`wheel.dx`, a draw index, or a damage/glass group. Runtime selection and
binding remain implicit.

## Controlled swap boundary

Replacing `complete.dx` with `car.dx` in presentation omitted normal embedded
wheels and exposed crew. Replacing race `car.dx` with `complete.dx` produced
duplicate wheels, lifted placement, and loss of normal collision/damage.

The supported conclusion is: **the race runtime expects the structure/role
represented by `car.dx`; substituting `complete.dx` is incompatible with that
pipeline.** This is not proof that all collision data resides in `car.dx`.

The lift remains an **UNRESOLVED_RUNTIME_TRANSFORM_DEPENDENCY**. For Astero,
source-Y minima differ (`car` -0.228596, `complete` -0.000733), and similar
differences are common, but bounds alone do not establish the observed lift's
cause. Duplicate wheels and external suspension placement are competing
factors.

See `research/r4a/` for the corpus matrix, linkage details, damage evidence,
and proposed controlled tests.
