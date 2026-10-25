# V-SDK2 bounded authoring foundation

Stock projects are copy-on-write and preserve retail identity. The first
qualified pairs are Pajero/CarID 1 and Megane/CarID 18, from the existing exact
PC registration evidence. This is not a general guessed name-to-ID mapping.

`tools/stock_vehicle_project.py create --source RETAIL_UNPACKED --project NEW
--family Megane --car-id 18` copies only that vehicle family into a private
project. `build --project PROJECT --output NEW_BUILD` emits changed resources
only. Unedited projects emit no overrides. Source SHA256 pins, family ownership,
path containment, links, additions/removals and identity changes are gated.
Changed DX must pass the existing semantic parser; changed DXT must pass its
exact-size wrapper parser. Other changed formats remain unsupported. These are
resource authoring checks, not proof of gameplay equivalence.

Two original family zero-edit builds and one reversible Megane whitepaint DXT
edit are under `.research-output/vehicles/vsdk2/stock/`. The edit scales only the
red channel by 0.9, preserving alpha, dimensions and wrapper. Restore by copying
the pinned original back into the project; omitting the stock project restores
retail passthrough. No retail files, registration, class, unlock, AI, save data,
physics or audio are edited. Composition is through a new sealed roster only.

## Camera progression and current qualified experiment

The existing `research/vehicles/vsdk1/camera.md` remains the verified extent and
mode map. A diagnostic-only profile accepts explicit half-length and height,
dispatches by CarID in offline comparison, and rejects runtime policy claims.
It does not demonstrate native CarID isolation or install a camera hook.

Fresh REA/Ghidra 12.1.4 inspection reverified original PC SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Camera manager 004B7DE0 resolves its target using 004F5EB0; 004F5EB0 calls
0050E420 (bounded registry lookup) and returns the first element of the resolved
object list. It then passes that target to camera/helper virtual methods and
004B82A0. The latter constructs mode-specific camera instances and copies shared
parameters. This supports instance-local injection as a research direction; it
does **not** identify the target as a physical participant or provide its CarID.

Evidence IDs: `ev_ea50988f99f4734684903140c563c2d7937d3d5c85ef93152ea624342dd67ced`,
`ev_165dbf9f6124d4654a4623019bf05c8f44ec3cc0bbd21e8bf2fa49074c7685b5`,
`ev_ac07442993ab03cb5d7b4cf6350529e57fd5571a25568ec6d522745d304edde6`,
`ev_de8de28ba5fd767b849b5605c020d1af748396a24dac39447c201401009a9cd0`.

The subsequent exact-byte trace closes the owner-binding gap for the narrow
follow initializer: 004B7AFB..004B7B21 formats `Car%d` (literal 006AFDE0) from
manager+210 into manager+1F8. Update resolves that named scene entity. The
initializer retains it in EDI and reads its model at +50. Original 004F59F0
writes the scene name at entity+5C. This is not a guessed actor structure.

The new adapter checks that target name is canonical Car0..Car63, requires the
already-initialized native Race broker (no lazy creation), and resolves its
current **physical CarID** using the existing native 004ADA50/004AC660 getters.
Unrelated model resource names are rejected **before** invoking that getter.
The native getter uses mutable broker scratch strings, and missing lookups may
materialize broker records; it is not a pure read. CarID0 overrides are therefore
rejected until a stronger missing-key presence guard is qualified. The current
experimental profiles are IDs 18 and 28; no ID0 support is claimed.
It then separately matches canonical model resource name and all 44 original
bounds bytes. A different ID sharing the same model passes through unchanged.
Only calls 0052C652/0052C65E/0052C677 receive immutable camera-only bounds.
No source bounds, collision, geometry, actor, shared XML or persistent map is
written; current target is checked again on every invocation.

Native profiles use version 1, `policy: native_follow_extents`, CarID,
runtime_family, source_model_sha256 and follow_extents (half_length_m,height_m).
Values are authored framing calibration, not recovered physical dimensions.
Other camera modes, explicit distance, FOV, smoothing and focus offsets are not
implemented. Existing diagnostic-only profiles remain a separate offline tool.

Independent private controls (both retain the previous Pajero2 baseline):

- `vsdk2/candidate-camera-r2/Launch-SDK-Roster.cmd`: Lancer ID28, half-length 2.25 m,
  height 1.5 m; all other IDs pass through.
- `vsdk2/candidate-camera-megane-r2/Launch-SDK-Roster.cmd`: stock Megane ID18,
  half-length 2.0 m, height 1.3 m; its zero-edit stock project supplies pinned
  source evidence, without emitting any resource override.
- `vsdk2/candidate-stock-material/Launch-SDK-Roster.cmd`: separate reversible
  Megane whitepaint edit, no camera hook; native payload unchanged from baseline.

All 366 game resources are byte-identical to the baseline in both camera
controls. Three launcher preflights pass for each. Original x86 initializer
replay passes 18 cases per profile including ID mismatch/shared model,
foreign/malformed target, absent broker, disabled extent flag and resource
mismatch. Native getter count, source bounds, stack, EDI and x87 stack are
preserved. Three fixture-free generated-x86 tests also verify native flags and
volatile results. Service stubs are explicitly not live gameplay evidence.

Evidence: `.research-output/vehicles/vsdk2/camera-target-chain.json`,
`camera-replay.json`, `camera-megane-replay.json`,
`camera-resource-regression.json`, and final R2 `camera-final-regression.json`.
The latter replays the **actual delivered full payload** (18 cases per control)
and verifies deterministic source reproduction, not a separately assembled stub.
The selected model heights previously fed
by antennas and donor half-length are replaced only for the selected CarID's
follow framing; suspension and handling are untouched.

Human acceptance remains: selected follow modes, rear view, split-screen,
replay, changing target, race teardown/re-entry, and unrelated stock/addon IDs.
Unknown names and an absent broker fall back without caching any owner pointer.
Live target teardown and replay/split lifetimes still need the above testing. A complete
live update and gameplay camera-fidelity claim is not made from CPU replay.
