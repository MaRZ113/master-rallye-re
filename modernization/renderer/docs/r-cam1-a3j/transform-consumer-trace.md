# R-CAM1-A3j.1 — Reset-to-physics consumer trace

## Result

**Status: `R-CAM1-A3j.1 — PARTIAL / EXACT_CONSUMER_GAP_IDENTIFIED`.** The pristine retail image contains a native path that applies a transform-shaped block to a physics chassis and performs bounded reset work on four associated wheel records. The stock reset manager writes a matrix-shaped block and apply flag into the `CarN` Broker object. The physics controller consumes corresponding fields from a separately named `Controller/CarN` Broker object. Static evidence does not prove those objects are the same storage or that a callback copies one into the other. The exact reset-to-chassis edge therefore remains unproven, and the result is not a safe teleport transaction.

Static analysis only: no game state was written and no runtime probe was run.

## Build identity

| Field | Value |
|---|---|
| File | `MRallye.exe` |
| Size | 3,121,214 bytes |
| SHA-256 | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |
| PE | PE32 / I386, timestamp `0x3C02695D` |
| ImageBase | `0x00400000` |
| Entry | RVA `0x001C4602`, VA `0x005C4602` |
| Analysis | Ghidra 12.1.4; temporary project outside the repository |

Addresses below are VAs; RVA is VA minus `0x00400000`.

## Stock reset output

`FUN_004CCC90` (VA `0x004CCC90`, RVA `0x000CCC90`) has a recovery path called from `0x004CCBE4` and a clear path called from `0x004CCC2E`. The recovery path selects a route sample from the reset manager's `RaceLine`, `Progress`, and `LastMarker`, then resolves its per-participant `Car%d` Broker value.

The recovery path:

1. Stores `1` at the resolved `Car` data pointer plus `0x33`.
2. Builds basis/position data from the selected route sample and copies 16 32-bit words beginning at `CarData+0x34` (the last word starts at `+0x70`; end-exclusive `+0x74`). Call site `0x004CD12C` sets the destination to `CarData+0x34`; `FUN_00404E60` (`0x00404E60`, RVA `0x00004E60`) copies 16 words. This is a 64-byte, matrix-shaped block. Its translation is based on the route sample with the routine's Y adjustment.
3. Separately writes four 16-byte vectors to `RaceState` data at `+0xBC`, `+0xCC`, `+0xDC`, and `+0xEC`.
4. Reads `ResetNo`, increments it, and writes the new integer through its Broker accessor.

Mode zero only clears `CarData+0x33`; it does not publish a matrix or increment `ResetNo`. The `RaceState` vectors and `CarData` matrix are distinct outputs.

## Physics consumer found downstream

`FUN_0043F020` reads `Race/CarN/PlayerType`, creates a per-car physics handle through `0x0043E4C0`, and associates four wheel records. The handle is not the chassis structure. `FUN_00442D40` attaches a separate `0xA4` controller at handle `+0x14`; the four wheel records have a `0x188` stride.

The controller data object is constructed by `FUN_005089E0` (VA `0x005089E0`, RVA `0x001089E0`) under Broker path `Controller/Car%d` through `ControllerCarBrokerAccess`. It has fields at `+0x33` and `+0x34`, but this path is distinct from the reset manager's `Car%d` path.

`FUN_00443820` calls `FUN_00444AE0` first, then processes wheel records and later reaches its solver/update helper. In `FUN_00444AE0`:

- the controller reads `Controller/CarN` data `+0x33` and copies it to controller state `+0x18`;
- when nonzero, it calls `FUN_00444D50` (call site VA `0x00444BB8`);
- `FUN_00444D50` copies 16 words from that controller data object's `+0x34..+0x70` into a temporary matrix and calls `FUN_00443740`.

`FUN_00443740` passes the matrix to `FUN_0043A020` for the physical object behind the per-car handle (`handle+8`, then its `+4` body pointer). `FUN_0043A020` writes position to body `+0xA0..+0xA8`, copies it to previous-step position fields `+0x144..+0x14C`, and updates orientation-related fields. This confirms a chassis pose setter and previous-position synchronization **when this controller path is activated**.

After the pose setter, `FUN_00443740` also clears a 32-bit field at `+0x120` in each of four wheel records, calls `FUN_0043C310` on related state, calls `FUN_004437B0(0)` to clear byte fields in chassis/controller/wheel records, and conditionally calls `FUN_0043B800` if its service and gate are present. The collision-service path may adjust chassis position; it does not establish a complete wheel/contact-cache reconciliation contract. The wheel fields remain unnamed, no wheel pose is directly written in this helper, and linear/angular velocity policy remains unproven.

## Missing edge: `CarN` to `Controller/CarN`

The reset manager resolves and writes `Car%d`; the controller constructor builds and reads `Controller/Car%d`. Matching participant indices and offsets (`+0x33`, `+0x34`) do not prove pointer identity or propagation.

```text
CarN recovery output (+0x33 / +0x34)
    - - - unproven alias / copy / callback - - ->
Controller/CarN data consumed by FUN_00444AE0
    -> FUN_00444D50
    -> FUN_00443740
    -> FUN_0043A020
    -> authoritative chassis pose
```

`ResetNo` is not the proven physics trigger. The identified named-key consumer at `0x004B7DE0` compares it with cached state and resets camera tracking through `0x004B82A0`. No `ResetNo -> physics setter` edge was found in the examined references. This is scoped evidence, not a whole-program absence claim.

## Ownership and update phase

`FUN_0043F020` proves per-participant physics handles and four-wheel associations. It does not certify which participant is human in the exact pristine runtime or certify a live chassis pointer generation. Prior derivative evidence that labels `Car0` as the player is not exact-retail ownership proof.

The physics manager at `0x0043F5D0` iterates registered handles and reaches `FUN_00443820`. Within that per-car call, controller transform handling precedes wheel routines and the solver/update helper. The reset-manager scheduler position relative to the physics manager and both substeps is unknown. “The next controller tick” is the narrowest supported phase description; the paused camera scheduler is not a physics-write phase.

## Startup placement candidate

`FUN_0048EB40` (RVA `0x0008EB40`) is called from race-entry setup `FUN_0048E2D0`. It writes start transforms under `Race/Car%d/Transform`; its optional `Race/Debug` branch reads `Physics/Car0/Transform` and publishes a race transform. Separately, physics-handle construction at `0x00442D40` invokes the common `FUN_00443740` pose/reset helper before handle insertion and collision registration complete.

Initial construction is a plausible controlled placement seam. The exact Broker key/data alias between the start-placement output and constructor input, and their precise order in the supported retail scene, are not established. Do not enable `Race/Debug` or write either key.

## Evidence table

| Claim | VA / RVA | Evidence | Grade | Open question |
|---|---|---|---|---|
| Reset sets `CarData+0x33` and copies 16 words to `CarData+0x34` | `0x004CCC90` / `0x000CCC90`; copy at `0x004CD12C` / `0x000CD12C`; helper `0x00404E60` / `0x00004E60` | Recovery branch, Broker resolution, direct copy destination | `CONFIRMED_BY_EXE` | Does it alias/feed `Controller/CarN`? |
| Reset writes separate RaceState vectors and increments `ResetNo` | `0x004CCC90` / `0x000CCC90` | Direct stores and Broker integer read/increment/write | `CONFIRMED_BY_EXE` | No physics relation proven |
| Controller conditionally consumes its `+0x33/+0x34` | `0x00444AE0` / `0x00044AE0`; `0x00444D50` / `0x00044D50` | Constructor path and direct field reads/copy | `CONFIRMED_BY_EXE` | Alias/copy from reset object unproven |
| Native helper sets body pose and previous position | `0x00443740` / `0x00043740`; `0x0043A020` / `0x0003A020` | Matrix call chain and direct stores | `CONFIRMED_BY_EXE` | Velocity, wheel pose, contacts, trigger remain incomplete |
| Helper touches four wheel records | `0x00443740`; `0x004437B0` / `0x000437B0` | Four iterations at stride `0x188`; clears `+0x120` and byte `+0x4` | `CONFIRMED_BY_EXE` | Field semantics and full reconciliation unknown |
| `ResetNo` drives camera discontinuity handling | `0x004B7DE0` / `0x000B7DE0`; `0x004B82A0` / `0x000B82A0` | Cached counter comparison and camera reset call | `CONFIRMED_BY_EXE` | Not a whole-program negative proof |
| Race-start placement and physics construction both reach transform behavior | `0x0048EB40` / `0x0008EB40`; `0x00442D40` / `0x00042D40` | Race transform publication; constructor calls shared pose helper | `CONFIRMED_BY_EXE` | Key alias and startup order unknown |

## Next narrow action

Trace the `ControllerCarBrokerAccess` vtable and Broker key routing to prove or disprove whether `CarN` and `Controller/CarN` share storage or whether a callback copies the matrix and flag. That resolves the missing consumer edge without repeating broad physics discovery.

A read-only runtime probe is **not required yet**. If Broker implementation details do not establish pointer identity or copy semantics, use one bounded observer during a user-initiated stock reset to record only validated Broker pointers/values at the reset write and controller read, plus validated chassis pose before/after. Do not add a write-enabled probe or trigger reset automatically.
