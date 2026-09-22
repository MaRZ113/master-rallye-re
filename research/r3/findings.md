# Phase R3 findings

## Automated writer result

The canonical template writer derives the position span from the proven DX
parser (`0x10`, 12 bytes per parsed vertex for the current vehicle grammar).
It preserves unchanged position bytes and every non-position byte exactly.
Output is accepted only after binary-diff audit, complete reparse, structural
comparison, preserved-section hashes, unchanged diagnostics, and source-AABB
validation.

Complete vehicle-corpus results:

- zero edit: **78/78 byte-identical**;
- temporary safe single-position edit: **78/78 validated**;
- skipped resources: **0**;
- failures: **0**;
- unexpected changed byte ranges: **0**.

The machine-readable evidence is `dx-writer-corpus.json`; the compact table is
`dx-writer-corpus.md`.

## Blender authoring/export result

Blender provenance now distinguishes `SOURCE_IDENTICAL`,
`POSITIONS_ONLY_CHANGED`, `UNSUPPORTED_TOPOLOGY_CHANGED`, and
`INVALID_PROVENANCE`. Export requires unique complete source vertex and
triangle identities plus an unchanged topology/draw/group fingerprint.

Blender 5.2.2 LTS (`d13f752e3b9c`) passed:

- synthetic untouched import -> export byte identity;
- one synthetic Blender vertex -> one canonical source vertex patch;
- duplicate source identity rejection without output;
- save/reload -> byte-identical export;
- installable ZIP using only the vendored canonical library;
- byte-identical zero-edit export for 12 real resources spanning Astero,
  Pajero, Forester, Bruno, ChevyBlazer, Ufo, and megane `sus.dx`.

The established R2 texture, direct-V Blender UV, source-normal provenance, and
safe display-normal policies remain unchanged.

## Runtime candidates

Ignored local output:

`.research-output/r3/runtime-test/`

The primary candidate is `Astero-complete-one-vertex.dx`:

- source SHA-256: `853a1e7e76b00c1b4c0747e19ec6a4c110bda7923a974bc807c7f5907645331f`;
- output SHA-256: `cbcee7acd70699d9e282b33a2fe2a3f0f1437755c9c900d0549e9cc0d2a2596c`;
- source vertex: 415;
- source position offset: `0x1384`;
- source delta: approximately `(+0.08, 0, 0)`;
- changed bytes: 3, all within that vertex's 12-byte record;
- AABB containment and post-write validation: PASS.

`Astero-car-one-vertex.dx` is supplied as a clearly labeled alternative
because XML/TXT evidence does not directly prove the runtime selection context:

- source SHA-256: `b97949651ae1c0089a614beaa24f6b07bbea84735c70faf1570760a9aaa16d90`;
- output SHA-256: `2699ec8c3dbf7cefef28fc77523681da80c55ad6c6dbf5de88efecc8e79e3279`;
- source vertex: 1183;
- source position offset: `0x3784`;
- changed bytes: 3.

The candidates were generated through the Blender export path. Neither was
installed or launched by the agent.

## Human runtime validation

**RUNTIME VALIDATED — PASS**

**FIRST CONFIRMED WRITABLE MASTER RALLYE VEHICLE GEOMETRY**

- Date: **2026-09-22**
- Confirmed scope: same-topology vertex-position edits
- `complete.dx`: visible in the vehicle presentation/menu model
- `car.dx`: visible during an actual race
- Game load: PASS
- Model load: PASS
- Position edit visible: PASS
- Visual artifacts: none observed

With the correctly modified `car.dx`, collision, normal damage/deformation,
and glass breakage continued to function. These observations confirm that the
original game accepts the positions-only template patch produced by R3.

Topology-changing export, UV writing, normal writing, and material writing are
**not** runtime-confirmed.

## Runtime-confirmed repack method

The human test unpacked `Data.sma`, modified the intended resource, packed the
unpacked tree as a normal ZIP archive using 7-Zip, renamed `.zip` to `.sma`,
and launched the game. The game accepted this archive. No broader claim is
made about required ZIP options, variants, or implementation details.

## Preliminary runtime resource roles

Normal use and controlled swaps support:

- `complete.dx`: presentation/menu vehicle resource;
- `car.dx`: race vehicle body/chassis resource;
- `wheel.dx`: wheel geometry instantiated separately by the race runtime.

When `car.dx` replaced `complete.dx`, the menu vehicle lacked its normal
embedded wheels and showed driver/co-driver geometry; the menu did not appear
to instantiate `wheel.dx` like the race runtime. When `complete.dx` replaced
`car.dx`, the race rendered the complete model and also instantiated
`wheel.dx`, producing duplicate wheels, a strongly lifted/incorrect placement,
and loss of normal collision and damage behavior, including passing through
walls.

This is not evidence that collision data itself resides inside `car.dx`. The
supported conclusion is: **the race runtime expects the structure/role
represented by `car.dx` for normal vehicle collision/damage behavior;
substituting `complete.dx` is incompatible with that runtime pipeline.** The
exact dependency is unresolved and reserved for R4A.
