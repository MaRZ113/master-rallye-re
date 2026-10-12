# R-CAM1-A3j — Safe vehicle reposition research

## Result

**Status: `A3j — READ_ONLY_REPOSITION_RESEARCH / PARTIAL`.** The pristine retail executable contains a stock `gaVehicleResetManager` recovery path, but this analysis does not prove that it moves the live rigid-body owner together with all four wheel/suspension objects and reconciles the physics collision state. It also selects a race-line recovery point rather than accepting the Freecam position. No teleport or undo control is safe to enable from the available evidence.

The single blocking prerequisite is a verified exact-build native relocation transaction for the identified human vehicle physics owner: a target transform plus velocity, wheel/contact and broadphase reconciliation, with a supported phase and rollback. No such complete transaction is established below.

## Build and scope

Analysis target: `MRallye.exe`, 3,121,214 bytes, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. The PE is 32-bit I386, timestamp `0x3C02695D`, ImageBase `0x00400000`, entry RVA `0x001C4602` (VA `0x005C4602`). All VAs below refer to this exact image; RVA is VA minus `0x00400000`.

This is static analysis only. Ghidra 12.1.4 analyzed a temporary project outside the repository. Temporary function-boundary probes were rolled back. Existing research files were read but not changed. No game executable, DLL, Ghidra database, runtime log, or raw function export is included in this handoff.

## Player identity is not yet a physics-owner certificate

The normal race setup uses participant indices across distinct systems. Existing research maps ordinary Quick Race preparation through `0x0044A320`/`0x0044ED50` and named physics configuration into `Vehicles/CarN/...`; the physical initialization loop later filters `Race/Car%d/PlayerType` at `0x0043F020`. Existing R-AI2 runtime evidence on a hardened derivative observed Car0 as the human participant, but that does not identify the live rigid-body pointer on this exact pristine process.

The France1 race certificate established for Freecam is a supported scene/lifecycle gate. It does not independently certify the current native physics object, its generation, or a safe write phase. Thus `Car0` is a useful candidate participant index for a standard Quick Race, not sufficient authorization for mutating native physics state.

## Physics ownership and update path

The exact executable has a distinct physics manager and per-car physics handle path:

| VA / RVA | Evidence |
|---|---|
| `0x0043EF80` / `0x0003EF80` | Per-participant physics setup block reaches `0x0043F020` for each car, then manager/update setup. Ghidra did not establish a function boundary at this address; the call-flow is also recorded by the read-only R-AI2 map. `CONFIRMED_BY_EXE`. |
| `0x0043F020` / `0x0003F020` | Reads `Race/CarN/PlayerType`, resolves the car object, creates a physical handle through `0x0043E4C0`, and associates four wheel records through `0x0043ED00`. `CONFIRMED_BY_EXE`. |
| `0x0043E4C0` / `0x0003E4C0` | Builds a `0x2C` per-car physics handle, inserts it into the dynamic physics vector via `0x0043BB70`, and registers it with the collision manager via `0x0043A800`. `CONFIRMED_BY_EXE`. |
| `0x0043A800` / `0x0003A800` | Adds collision entries and invokes collision-manager update/registration work. `CONFIRMED_BY_EXE`. |
| `0x0043AC80` / `0x0003AC80` | Iterates registered car handles and four wheel-sized records (stride `0x188` in this path), forwarding them through a collision-service virtual call. This establishes coupled registrations, not a complete post-teleport invalidation recipe. `CONFIRMED_BY_EXE`. |
| `0x0043F890` / `0x0003F890` | Runs two physics substeps per invocation. `CONFIRMED_BY_EXE`. |
| `0x0043F650` / `0x0003F650` | Copies position/orientation-related values into prior-step fields for registered physics objects. This is evidence of temporal state, not a complete rigid-body layout. `CONFIRMED_BY_EXE`. |

The creation and update paths expose a real car-plus-four-wheel physics topology, but this pass did not recover a typed authoritative chassis pose/velocity layout, a native setter, contact/manifold lifetime, or the exact safe point between simulation phases. The `0x2C` handle and `0x188` wheel records are not treated as complete public structure definitions.

## Stock recovery manager

New exact-build analysis expands the older note that reset behavior was unknown. The previous [G1 executable note](../../../../research/g1/limits-executable.md) says the manager is wired to `LimitState` and leaves exact downstream behavior unknown. This pass confirms its recovery decision path, but not a safe physical relocation transaction.

| VA / RVA | Static evidence |
|---|---|
| `0x004CC2D0` / `0x000CC2D0` | Constructor registers `gaVehicleResetManager`; its vtable is at `0x00691508`. `CONFIRMED_BY_EXE`. |
| `0x004CC5F0` / `0x000CC5F0` | Initializer binds per-car `Car`, `Controller/Car`, `Progress`, `LastMarker`, `LimitState`, `ResetNo`, `Finished`, and `Resetting` Broker keys. `CONFIRMED_BY_EXE`. |
| `0x004CCAF0` / `0x000CCAF0` | Per-car update checks reset-related state and calls detection/transition helpers; when a reset countdown completes it invokes `0x004CCC90`. `CONFIRMED_BY_EXE`. |
| `0x004CD4A0`, `0x004CD550`, `0x004CD1B0` | Reset eligibility/timing and per-car recovery state helpers called by the update. Their observed role is the stock reset state machine. `CONFIRMED_BY_EXE`. |
| `0x004CCC90` / `0x000CCC90` | Recovery routine reads `RaceLine`, `Progress`, `LastMarker`, and `Landscape`; selects a route-line sample using `0x004CD200`; calls an interface returned by `0x004E8CD0`; then updates race-car output/state transform data and advances `ResetNo`. It receives participant index and reset mode, not a Freecam destination. `CONFIRMED_BY_EXE` for the flow; `STATIC_INFERENCE` for the output-data interpretation. |

The routine is a useful stock recovery seam, but the exact vtable used at this call site narrows what its query can prove. `0x004E8CD0` creates the first service with vtable `0x00691824`; the methods called by `0x004CCC90` are `0x004F4E10` (`+0x1C`, return only), `0x004F4E20` (`+0x20`, return only), and `0x004F4E00` (`+0x18`, returns false). Therefore the subsequent hit-position and hit-normal getters are skipped in this exact path. The route-line target is not validated by a successful result from that service. The routine then publishes race-car output/state transform data and increments `ResetNo`.

No operation in the recovered path accepts an arbitrary requested transform and is proven to update the registered chassis, four wheel/suspension states, velocities, and collision caches as one transaction. The exact relationship between the published race-state transform and the physical manager remains unknown; it is not treated as a physics setter. In particular, the stock recovery route does not provide the destination validation required for this Freecam teleport.

## Initial placement is a separate lifecycle

`0x0048EB40` (`RVA 0x0008EB40`) runs race start placement. Its optional `Race/Debug` path reads `Physics/Car0/Transform`, publishes a corresponding `Race/Car0/Transform`, and returns; the ordinary path generates positions from `StartArea` and publishes per-car race transforms. Exact string references to `Physics/Car0/Transform` occur in this start-placement function. This is startup configuration/initialization evidence, not a validated setter for an already-created live physics body.

Consequently, copying the Freecam pose into `Race/Car0/Transform`, writing the Broker key, or changing only a render actor would not satisfy the requested physical teleport and could split visible and physical state.

## Safety decisions

- Do not add `VehicleTeleportEnabled`, key bindings, native writes, a reset trigger, or Undo in this partial phase.
- Do not infer ground height from camera height or use a render overlap as collision proof.
- Do not reuse raw pointers or opaque rigid-body bytes for persistence.
- Keep the existing Freecam, FOV, roll, bookmarks, pause, and camera ownership behavior unchanged.
- No teleport runtime test is authorized by the evidence state: there is no safe production path to test. Any future candidate needs a fresh exact-build identity/lifecycle gate and complete rollback semantics before an in-game road test.

## Evidence sources

New exact-build static observations are indexed in [evidence-map.json](evidence-map.json). Existing read-only context includes `research/r-ai2/native-storage.md`, `research/r-ai2/participant-pipeline.md`, `research/r5v_b_2/physics-dataflow.md`, `research/r-ai1/downstream-consumers.md`, and `research/g1/limits-executable.md`. Older findings remain unchanged; the new interpretation belongs only in this A3j folder.
