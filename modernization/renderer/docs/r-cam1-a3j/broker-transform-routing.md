# R-CAM1-A3j.2 — Broker transform routing proof

## Verdict

**`BROKER_ROUTING_PROVEN` for the pristine retail executable, by static executable evidence.** The stock recovery writer resolves `Controller/CarN`, obtains a `ControllerCarBrokerAccess` adapter, and writes the transform into the adapter's backing pointer. The per-car physics controller holds that same backing pointer and reads the flag and matrix from it before calling the chassis pose path.

This proves the Broker-to-physics route for the stock reset transform. It does not prove that arbitrary relocation is safe or that the stock reset operation is a complete teleport transaction. No reset was invoked, no runtime probe was run, and no game state or code was changed.

## Build identity and method

| Field | Value |
|---|---|
| Image | `MRallye.exe` |
| Size | 3,121,214 bytes |
| SHA-256 | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |
| PE | PE32 / I386; timestamp `0x3C02695D` |
| ImageBase | `0x00400000` |
| Entry | VA `0x005C4602`, RVA `0x001C4602` |
| Analysis | Ghidra 12.1.4, isolated temporary project outside the repository |

All addresses below are VAs; RVAs are the VA minus `0x00400000`. Evidence is from the hash-verified retail image. This is static evidence, not runtime confirmation.

## Corrected path selection in the reset manager

`ResetManager_Constructor_004CC5F0` initializes separate per-participant path arrays and expected class IDs. Its loop formats and interns the keys; the recovery routine then consumes those arrays in distinct operations:

| Reset-manager field | Interned path | Expected Broker payload type | Use in `ResetManager_Recovery_004CCC90` |
|---|---|---|---|
| `+0x20` | `Controller/Car%d` | `ControllerCarBrokerAccess` at manager `+0x60` | Transform-apply flag and 64-byte matrix |
| `+0x1C` | `Car%d` | `gaVehicleOutputData` at manager `+0x5C` | Separate four-vector output at `+0xBC`, `+0xCC`, `+0xDC`, `+0xEC` |

The decisive recovery instructions are at `0x004CCFCC–0x004CCFF1`: load the path array from `[ESI+0x20]`, select participant `EBX`, pass the expected type at `[ESI+0x60]` to the Broker resolver, take the returned adapter's `+8` field as `EBP`, then set byte `[EBP+0x33]` to `1`. At `0x004CD129–0x004CD12C`, the routine passes `EBP+0x34` as the destination for a 16-dword copy. Thus the matrix destination is the pointee stored by the adapter, not the `gaVehicleOutputData` record selected by `Car%d`.

The same recovery routine subsequently resolves `[ESI+0x1C]` with expected type `[ESI+0x5C]` and writes the four distinct vectors into that payload. The two Broker paths are both used, but for different outputs.

### A3j.1 correction

The A3j.1 trace described the 64-byte transform and apply flag as writes to the `Car%d` Broker object. That attribution came from matching the wrong reset-manager path-array field. The code uses `+0x20` (`Controller/Car%d`) for the flag and matrix; it uses `+0x1C` (`Car%d`) for the four vectors. This document and the additive `a3j2_follow_up` evidence-map entry record the correction. The A3j.1 source files remain unchanged.

## Adapter and shared backing pointer

`ControllerCarBrokerAccess_Constructor_005089E0` initializes the controller backing object `P`, including clearing `P+0x33`. It creates a 12-byte adapter object `Q` and registers `Q` under the formatted `Controller/Car%d` key. The adapter fields established by the constructor are:

```text
Q+0x00 = vtable 0x00691A54
Q+0x04 = interned class ID for ControllerCarBrokerAccess
Q+0x08 = P
```

The adapter's copy/clone method at `0x00508B90` copies `Q+0x08` into the new adapter's `+0x08`; it does not allocate or copy the backing controller object. The adapter is therefore a Broker-visible wrapper carrying a direct pointer to `P`.

The physics controller constructor `PhysicsController_004442A0` calls `ControllerCarBrokerAccess_Constructor_005089E0` and stores the returned `P` at outer-controller offset `+0x74`; the store is at `0x004443FD`. The Broker adapter and physics controller consequently reference the same backing allocation:

```text
Broker entry Controller/CarN -> payload Q
Q+0x08 -------------------------------> P
physics controller O+0x74 ------------> P
```

There is no `CarN`-to-`Controller/CarN` copy step needed for this route. The reset writer and physics reader converge on the same `P`.

## Consumer chain

`PerCarControllerUpdate_00444AE0` loads `P` from `[O+0x74]` and reads the byte at `P+0x33`. When set, it calls `ApplyControllerTransform_00444D50` (call site `0x00444BB8`). That function loads the same `P` from `[O+0x74]`, copies 16 dwords from `P+0x34..P+0x70` into the local transform block, then calls `ResetChassisAndWheelState_00443740`. That helper reaches `SetPhysicsBodyPose_0043A020`.

The end-to-end static route is:

```text
ResetManager_Recovery_004CCC90
  -> Broker resolve Controller/CarN, expected type ControllerCarBrokerAccess
  -> payload Q; P = Q+0x08
  -> P+0x33 = 1; copy 64-byte transform to P+0x34

PhysicsController_004442A0
  -> O+0x74 = P

PerCarControllerUpdate_00444AE0
  -> reads P+0x33
  -> ApplyControllerTransform_00444D50
  -> reads P+0x34..P+0x70
  -> ResetChassisAndWheelState_00443740
  -> SetPhysicsBodyPose_0043A020
```

This is a pointer-identity route established from construction, registration, reset writes, and consumer reads in the exact image. It is not inferred from matching field offsets alone.

## Flag and scheduling limits

The controller-data constructor initializes `P+0x33` to zero. Recovery sets it to one before publishing the matrix; the reset manager's clear path sets it back to zero. The consumer reads the flag and does not itself clear `P+0x33`, so the flag behaves as a shared level until another writer clears or changes it. A separate restore-like path at `0x004CB410` also writes the controller flag from packed state, without publishing this matrix.

Static analysis establishes the data route but not the scheduler order between reset-manager updates and physics ticks, or whether a paused game advances either subsystem. The matrix can be consumed by the per-car controller when it observes the flag; the precise first/last tick after recovery remains unproven.

## What this proves about relocation

The stock reset routine does more than publish a similarly shaped matrix: it publishes directly into the controller backing storage consumed by the chassis pose helper. The native helper and its limited wheel-state cleanup were documented in A3j.1 and are reachable through this newly proven edge.

Teleport readiness remains **NO**. This route does not establish velocity policy, complete wheel/suspension state, contact/manifold reconciliation, broadphase refresh, safe solver phase, destination clearance, rollback, or runtime behavior. Do not treat this proof as permission to invoke the reset path from Freecam.

## Evidence index

Machine-readable claim/address records are in [`broker-transform-routing-evidence.json`](broker-transform-routing-evidence.json). The validation boundary and artifact checks are in [`broker-transform-routing-validation.md`](broker-transform-routing-validation.md). The existing [`evidence-map.json`](evidence-map.json) has an additive A3j.2 entry; earlier A3j.1 documents are retained as historical records.
