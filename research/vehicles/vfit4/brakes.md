# V-FIT4 mechanical attachment evidence

The Lancer brake rotor and caliper packets are currently baked into `car.dx`.
The physics wheels are independent native instances. The source GT4 rest hubs
and the current combined-fitment MR initialization attachments differ by
**57.224317 mm**. Moving the confirmed mechanical groups fixes that reference
pose without changing physics. It does not implement dynamic attachment.
The subsequent optional native instance prototype is documented in
`brake-attachments.md`; it has controlled x86 evidence and a live-runtime gate.

## Source and classification

Fresh `gt4_assembly.assemble` / `gt4_scene.reconstruct` reads from the original
user-owned GT4 Beta CAR4 and DBT/IDI, not a cached OBJ or assembly pickle:

- Race CAR4 SHA256 `6586265558f008d69991e8cb1a826136e5209cb063402b6df411653e195ac36c`.
- Menu CAR4 SHA256 `b3e24db37de08aaa7e4df1ab2c8e508c037b1b4ecb3b8c528f769e1214b99a15`.
- Current `car.dx` SHA256 `b1798279dfa54cb9ecb5276ee8fe199858b56f146ca15195390cd0584796ac2e`.

The selected source commands contain callbacks11..14, each with four packets.
The qualified assembler transforms those packets with the corresponding
DBT-derived wheel hub and half-width offset, marks `component='brake'`, and
appends them to the body. `build_gt4_vehicle.py` excludes rim/tyre components
from `car.dx` but retains the mechanical groups. This establishes the baked
ownership; it does not establish a live GT4 or MR suspension pose.

Texture inspection and original packet geometry identify the first packet as
the rotor cutout quad and packets3/4 as two caliper faces. Packet2 is a source
additive rotor effect and is deliberately omitted by the existing converter.

| Callback / source shapes | Rotor draw | Caliper draws | Source MR-frame hub m |
|---|---:|---|---|
| 11 / 0,2,3 | 90 | 91,92 | (+.745,.18535,+1.255) |
| 12 / 4,6,7 | 93 | 94,95 | (-.745,.18535,+1.255) |
| 13 / 8,10,11 | 96 | 97,98 | (+.745,.18535,-1.255) |
| 14 / 12,14,15 | 99 | 100,101 | (-.745,.18535,-1.255) |

The source-to-MR basis is `(-x,y,-z)`, a proper 180 degree Y rotation.
Rotor quad Y/Z centres agree with the source hubs. The quad X plane is
`+/- .782339990`, intentionally 37.339990 mm outboard of the .745 m hub.
Its Y/Z half-extent is .164800048 m; this is **quad extent**, not a measured
visible rotor radius. Visible coverage is defined by the source texture alpha.
Caliper bounds are asymmetric and must not be used to infer a hub.

## Narrow optional correction

`brake-fitment.json` pins the exact baseline and selects only those 12 leaves.
Targets are computed from the actual primary combined-fitment generated XML
and its active `registry_name` ride reference. The existing native formula
`004407FC..004408C0` gives hubs `(+/-.745,+.15,+/-1.30)` at zero jounce.
The correction is `(0,-.03535,+.045)` front and `(0,-.03535,-.045)` rear.
Neither target is claimed to be a measured settled gameplay position.

Only 48 vertex positions change. No whole-body correction is justified by this
mechanical mismatch. No frontend correction is requested: `complete.dx` embeds
its source wheels and brakes in the same original rest frame, so they already
agree. Handling profiles remain a separate experiment.

`addon_sdk.visual_fitment` provides:

- `diagnose_mechanics(raw, definition)`: explicitly selected draw bounds,
  declared source/target hubs, material names and translation differences.
- `translate_mechanics(raw, definition) -> (bytes, report)`: optional static
  visual correction. Unknown keys, wrong hashes, controls, overlapping groups,
  shared vertices and translations above .25 m fail closed. Source remains
  immutable. Output differs only within selected position triples and bounds1339.
- `attachment_point(point, source_hub, current_hub, rotation)`: pure proper
  rigid-transform math for a caller-supplied dynamic pose. It has no native
  memory offsets or implicit steering/spin assumptions.

`tools/diagnose_vehicle_mechanics.py --model ... --profile ... --output ...`
writes diagnostics. `--corrected-model NEW_PATH` explicitly requests a new
static copy; existing outputs are rejected. Per-resource authoring should pass
an independently pinned definition for each selected resource. The provided
definition applies only to `car.dx`.

## Dynamic boundary

An attached caliper needs current hub translation, suspension jounce, front
steering and qualified toe/camber, while excluding wheel spin. A rotor may use
a separate spinning pose. Adding both to the existing spinning `wheel.dx`
would rotate the caliper and is not a correct reconstruction.

The admitted DX parser/writer grammar contains material leaves(tag2), named
switch envelopes(tag7) and cases(tag8); it contains no qualified per-draw
matrix payload. This is a limit of the currently admitted grammar, not proof
that the native engine lacks any unsprung attachment mechanism. An arbitrary
group label cannot be asserted to create a controller. Native attachment work
therefore requires verified scene/SFX registration and the corresponding
non-spinning wheel matrix, or a separately audited runtime render path.

Until that path is verified, the static candidate must retain the explicit
limitation: at nonzero jounce/steering its body-owned mechanics can diverge
from the wheel. No runtime alignment or PS2 visual parity is claimed here.

## Verification and private outputs

Seven synthetic tests pass: selected-only position writes with nested controls
preserved; identity profile; hash/control/overlap/large-offset rejection;
shared-vertex rejection; descriptive bounds; proper rigid attachment math.
The seventh test covers unsprung extraction, inverse side basis, native lamp
cases and rejection of a corrupted auxiliary colour attribute.
The actual corrected model reparses and passes the existing native brake scene
validator against the stock Navara reference. All normals, UVs, colours,
indices, draw/material/control records and collision bytes are identical.
The corrected rotor quad Y/Z centres match the declared targets within
0.00000005 m float32 error. These are offline checks.

Private evidence under `.research-output/vehicles/vfit4/`:

- `source-mechanics.json`: fresh original hashes, raw DBT provenance and selected callbacks.
- `target-hub-provenance.json`: effective setup and exact generated XML/profile hashes.
- `brake-static-correction.json`, `brake-verification.json`: measured shifts and byte-preservation checks.
- `car-static-aligned.dx`: SHA256 `59400d0cf7ccfe437384bb2fac617cca53f4b3aa02c0651f8b9d0c7503779fdb`.

The baseline candidate and all original assets remain intact. Source reports,
test results and this optional profile can be handed off separately from
private textures/models and diagnostic captures.
