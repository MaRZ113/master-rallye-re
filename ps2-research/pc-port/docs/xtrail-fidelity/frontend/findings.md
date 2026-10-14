# X-Trail frontend readiness

Decision: **source preparation GO; menu replacement NO-GO until the current
frontend owner/resource join is measured.** This workstream does not change a
renderer, source game asset, private model resource or running game memory.

## Original COMPLETE sources

| Source | SHA-256 | Geometry layer |
|---|---|---|
| PS2 `\TNG\DATAPSM\VEHICLES\XTRAIL\COMPLETE.PSM` | `30f976c4e4e371851e8ebd45dabc1db4ea6c676f9bf99684f70a9a2932096e38` | 6606 source vertices, 4636 nonsuppressed/nondegenerate authored faces, 24 material-owning visual meshes |
| PC `Xtrail/complete.dx` | `ce1694d24a09934cccc3163cfc3561c9308c2cac8d1a65443279c0eb00cda652` | 2555 source vertices, 2487 compiled faces, 24 records |

Both source identities were reverified from the protected original inputs using
the existing PackFS extractor and read-only Course SDK. All 24 PC unsigned
position digests are unique to this COMPLETE resource within the previously
decoded 78 original vehicle DX resources. This is a bounded vehicle-corpus
negative search, not an exhaustive all-game geometry admission certificate.

The PS2 hierarchy has one tag1 group and 24 tag2 meshes, no named/indexed
conditional branches. Terminal101 is at byte350262 with a3952-byte opaque convex
auxiliary trailer. The proven shared visual reader handles this source without
the tag102 adapter. The trailer is not transferred or interpreted as visual data.
Authored face counts are not simultaneous live menu draw counts.

The PS2 menu screenshot supplied by the user is evidence of COMPLETE appearance;
the separate countdown/race screenshot concerns CAR plus separately posed wheels.
The screenshots do not prove a current PC frontend resource owner or transform.

## Coordinate and material boundaries

Original model-local identity coordinates give **0/2487 PC face matches** at
0.001 source-unit tolerance. A longitudinal translation candidate derived once
from source bounds is PC-to-PS2 `[0,0,-0.17423653602600098]`. Held fixed, it still
gives **0 matches at0.001**, and **1098 at the explicitly relaxed0.005**.
This is a diagnostic registration, not a proved runtime/world transformation.
No constant was tuned to increase match counts, and no fitted transform grants
suppression authority.

The original PS2 painted body uses separate side, bonnet, color and rear
`carshiny` groups. `mastersticker069` is also `carshiny` with silverpaint secondary.
Headlight material groups differ: lights/silverpaint, lights/perspex, mlamp/glass
are distinct; there is also a windscreen `carglass` mesh. Do not merge these
contracts or assume the COMPLETE lamp groups equal the race lamp owner branch.

PS2 COMPLETE wheel groups19–22 have528/688/528/1100 source faces with tread,
wheel643, mercwheelrim and jumpwheel64 primary images. PC COMPLETE wheel
records17–20 have288/144/216/360 faces (see JSON for exact primary-slot association
and source ranges). None match even under the relaxed translation check.
The visible wheel differences therefore warrant an authentic visual-mesh
replacement investigation, not a declaration that a material change suffices.
This does not authorize replacing race wheel instances or their native poses.

## Current frontend identity gate

The latest two F10 captures at this audit are frames1274/session4888 and
8422/session27240. Both are certified Turkey2 race/Hud0 contexts. The older two
VehicleSelect captures in the same four-file inventory are the already recorded
Forester session23804. **There is no confirmed X-Trail VehicleSelect capture.**
These captures supply no reusable X-Trail pointer, VB/IB ID, ordinal or pose.

The prior original-PC byte-verified owner chain remains useful without another
broad reverse pass: VehicleSelect AI publishes selected ID; CarMover callback
`0x44c4c0` resolves it and constructs `<vehicle>/complete`; `0x4f5b70` updates the
en3d state model-name ID+0xc and invalidates its cached object+0x74 on name changes.
The cached compiled model's current buffer/lifetime relationship is not proved.

**Exact missing link:** same-frame current CarModel Egg -> en3d state -> loaded
model-name/cache resource -> current fully mirrored COMPLETE VB/IB draw set,
joined to a stable VehicleSelect selection generation. Selected Broker ID alone
cannot certify completed loading or safe original geometry suppression.

## Smallest safe pilot plan

1. Select X-Trail in the original PC VehicleSelect and capture two F10 frames
   after rotation, then select another car and return. Keep frontend and race
   diagnostics separate.
2. Collect one bounded read-only owner/name/cache observation tied to each exact
   frame; verify the original owner type/vtable and completed load generation.
3. Calculate all24 exact source position hashes from current upload mirrors,
   retained VB/IB generation/revision/ranges; bind them to that owner/context.
   Verify view/projection/world and every part transform; never use fixed matrix,
   IB displacement, frame sequence or historical Forester resource identity.
4. Validate originals can be suppressed as a complete verified set, once per
   logical instance; reject partial, shared, ambiguous or stale sets. Preflight
   all private converted meshes/materials/textures before suppression.
5. Only then implement a separately gated X-Trail COMPLETE pilot. Inherit the
   current proven model transform, preserve rotation and menu UI. Exercise car
   switching, Reset, failure rollback and resource retirement before expansion.

No menu implementation is proposed for this pass. Source preparation already
exists privately from VEHICLE-MODEL-PORT1; full geometry/texture data remains
ignored and is excluded from committed evidence and handoff archives.

## Focused reproducibility

Actually executed from re-general master, startingHEAD `10af03a2`:

```powershell
python ps2-research/pc-port/docs/xtrail-fidelity/frontend/audit.py
python -m unittest discover -s ps2-research/pc-port/docs/xtrail-fidelity/frontend -p test_readiness.py -v
python -m compileall -q ps2-research/pc-port/docs/xtrail-fidelity/frontend
git diff --check -- ps2-research/pc-port/docs/xtrail-fidelity/frontend
```

The audit needs canonical PackFS data, protected PC DX data and the read-only
Course SDK; existing parser modules are reused. The four focused tests run on
compact committed metadata and synthetic inputs without original game data.
No build directory or runtime mutation was created by this subtask.
