# R-PHYS2.2 — Trooper whole-family runtime binding experiment

**State: READY FOR HUMAN RUNTIME TEST — TEST NOT YET RUN.** This report prepares a process-local debugger test. No game was launched and no runtime or disk mutation was made during this phase.

## Goal and evidence boundary

Keep the retail Navara type and resource slot, with the already imported Trooper model resources in that slot. Temporarily redirect the source family identity so the ordinary broker reads the complete retail `Vehicles/Trooper/*` package, applies `Trooper/Player1`, and writes participant zero to `Vehicles/Car0/*`.

The controlling executable is the exact retail build SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` (3,121,214 bytes). The experiment is a debugger-only process-memory change. Do not edit the executable, vehicle XML, model assets, type catalog on disk, or slot registration.

## Confirmed Navara runtime hit

The human observed the ordinary local-race path in x32dbg:

| Field | Captured value |
|---|---|
| Breakpoint | `00493E30` (`FUN_00493E30`) |
| Return address at `[ESP]` | `0044F0D2` in `FUN_0044ED50` |
| ESP | `001AF808` |
| EBP | `00000000` (static caller dataflow maps EBP to participant index) |
| Argument string object at `[ESP+4]` | `001AF838` |
| Resolved family text | `Navara` |
| Other family text visible on the same stack | `Navara/Player1` |

The ordinary participant -> `Navara` -> `FUN_00493E30` edge is **CONFIRMED_BY_HUMAN_RUNTIME**. The presence of overlay text on the stack does not prove that the optional overlay reader ran; the prepared test checks the `FUN_00493FD0` call separately.

## Source and managed string construction

Static decompilation and instructions show that the names in `FUN_0044ED50` are raw `char*` locals, not the 16-byte argument objects passed to the readers.

```text
FUN_004B0630 -> class ID
FUN_0045A3C0 -> catalog base
catalog + 0x24 + class_id * 0x34 -> family-name pointer slot
FUN_004D1990(family slot value) -> deep-copied local_4e8 C string
    -> local managed string object -> FUN_00493E30

FUN_0044E400(participant, class ID)
    -> independently re-reads that same catalog family-name pointer
    -> appends /Player1 for participant 0, otherwise /Player2
    -> FUN_004D1990 -> deep-copied local_4e0 C string
    -> local managed string object -> optional FUN_00493FD0
```

`FUN_0044E400` does not derive the overlay from `local_4e8`; it re-reads the same catalog entry and appends the player suffix. Therefore a temporary change to the shared catalog C-string pointer before the first read naturally produces both `Trooper` and `Trooper/Player1`. Changing only the argument at `FUN_00493E30` would produce a hybrid and is rejected.

At `FUN_00493E30`, the first argument is a 16-byte engine string object. For the human-observed object address `001AF838`, the fields used by the fixed-build helpers are:

| Address | Offset | Meaning supported by code |
|---|---:|---|
| `001AF838` | `+0x00` | First dword/auxiliary bytes; exact meaning unresolved |
| `001AF83C` | `+0x04` | Pointer to character storage |
| `001AF840` | `+0x08` | Character length |
| `001AF844` | `+0x0C` | Capacity used by the reserve helper |

The supplied runtime capture did not include the pointer value at `001AF83C`, length, or capacity, so those live values are not invented here. In this call path, non-empty text is copied into a separate character buffer; no inline-string path is used. `FUN_0040F720` records the length and NUL terminator, `FUN_0040F740` reserves capacity, and `FUN_0040F600(1)` releases the buffer using the reference-count byte immediately before the data pointer. The reader's managed object is destroyed after the call. The overlay reader uses the same representation.

The table stores a C-string pointer. The proposed temporary buffer is also a plain NUL-terminated C string; the engine's own code deep-copies it into its managed objects. This avoids fabricating the managed object header, capacity, or ownership state.

## Safest redirect point

At `0044EDFB`, immediately before `MOV EAX,[EAX]`, the register `EAX` holds the address of the current catalog entry's family-name pointer field. Static instructions compute that field as `catalog + 0x24 + type_id * 0x34`. For the static Navara ID 7, its offset from the returned catalog base is `0x190`; use the live EAX slot address rather than guessing a runtime catalog base.

Replace the pointer in this one field temporarily with a process-local buffer containing `Trooper\0`. Do not edit the pointer's target characters and do not replace a managed 16-byte object. The table entry is read once for the base family and again by `FUN_0044E400` for the overlay. At `0044EE25`, after `FUN_0044E400` has returned and EDX points to its independently built overlay text, restore the original catalog pointer and free the temporary page. By then both `local_4e8` and the overlay builder have copied the family text. This keeps the shared catalog change limited to the two string-construction calls; `0044F343` is retained only as the later Car0 writer-return check.

| Method | Decision |
|---|---|
| Temporary catalog C-string pointer substitution at `0044EDFB` | **Chosen.** One source identity controls both base and overlay; reversible; keeps type ID 7 and normal CarN writer. |
| Change only the managed argument at `00493E30` | Rejected: leaves the independently resolved Navara overlay. Requires correct managed-object allocation and lifetime. |
| Patch base and overlay objects separately | Rejected: two independently owned strings and a greater chance of a hybrid or lifetime error. |
| Reuse a presumed Trooper object from config memory | Rejected: no evidence identifies a live standalone C string with a stable lifetime. XML/config database entries are not proven to be reusable string objects. |
| Replace Navara XML values with Trooper values | Not needed for this test. That would test a Trooper-equivalent package under the Navara name, not a true family redirect. |
| Edit Car0 floats individually | Rejected as the primary test; it bypasses the source-family question and native broker. |

The retail initialized family table contains Navara ID 7 and does not contain Trooper. The runtime intervention keeps ID 7 as the carrier and changes only the C-string value read from its existing entry. It does not create a Trooper type ID or slot.

## Trooper reader and overlay completeness

Reparsed the read-only retail corpus inputs for this comparison. Their hashes and sizes match the R-PHYS2.1 audit:

| Input | Size | SHA-256 |
|---|---:|---|
| `vehicles.xml` | 757,388 bytes | `a6762bb20999c7224c71b9f5d1d7edca55bcea147ff9f973300a8cf8d350aee0` |
| `Modifications.xml` | 135,772 bytes | `16df5a3a6b0c50c40f4ee74186e47b40294e6cb4ac11e0a3d7d20dafb8a5a65d` |

Navara and Trooper each have all 147 same-typed paths used by the broker's six base groups. Trooper has no base `Modifications/*` fields, matching Navara; the separate player overlay is complete for both players.

| Broker base group | Required paths in corpus | Trooper present | Missing |
|---|---:|---:|---:|
| Dimensions | 8 | 8 | 0 |
| Chassis | 16 | 16 | 0 |
| Steering | 5 | 5 | 0 |
| Engine | 45 | 45 | 0 |
| Suspension | 48 | 48 | 0 |
| DamageParams | 25 | 25 | 0 |
| **Total** | **147** | **147** | **0** |

Trooper has all 13 `Player1/Modifications` fields and all 13 `Player2/Modifications` fields. Navara has the same paths and values in both overlays (13/13 exact per player), so the overlay namespace will change to Trooper but will not create a numeric delta in this corpus pair. These facts establish present fields, not that every reader return is checked by the caller; R-PHYS2.1 found the base reader result is ignored.

For the exact retail Navara-versus-Trooper base comparison, 105 of 147 values are exact and 42 differ: Chassis 4, DamageParams 17, Dimensions 3, Engine 6, Suspension 12, Steering 0. This is a different comparison from the prior R-PHYS2.1 late-Trooper-versus-retail-source audit; those counts are not reused here.

## Distinguishing predictions

The following values are copied by the native reader/writer path. They are configuration predictions, not yet runtime measurements.

| Field | Navara | Trooper | Difference / expected observation |
|---|---:|---:|---|
| Dimensions/WheelBase | 2.80000 | 2.40000 | 0.40 m shorter; strongest geometric control |
| Dimensions/TrackWidthFront | 1.70000 | 1.65000 | 0.05 m narrower |
| Dimensions/TrackWidthRear | 1.70000 | 1.65000 | 0.05 m narrower |
| Suspension/Front/RideHeight | 0.05000 | 0.05000 | No direct family delta |
| Suspension/Rear/RideHeight | 0.05000 | 0.05000 | No direct family delta |
| Chassis/TotalMass | 1320.00000 | 1350.00000 | +30 kg |
| Suspension/Front/AuxRollStiffness | 3000.00000 | 7000.00000 | Greater configured front roll stiffness |
| Suspension/Rear/AuxRollStiffness | 3000.00000 | 7000.00000 | Greater configured rear roll stiffness |
| Suspension/Front/SpringRate | 34500.00000 | 34000.00000 | -500 |
| Suspension/Front/DamperRate | 2250.00000 | 2200.00000 | -50 |
| Suspension/Rear/SpringRate | 33500.00000 | 32000.00000 | -1,500 |
| Suspension/Rear/DamperRate | 2000.00000 | 2100.00000 | +100 |
| Engine/PeakTorque | 275.00000 | 340.00000 | +65 in the source field |
| Engine/GearRatioDiff | 3.92000 | 3.82000 | -0.10 in the source field |
| Engine/EngineDamping | 0.10000 | 0.05000 | Half the source value |
| Engine/Gear0 | -3.62000 | -3.20000 | Reverse ratio differs |
| Engine/Gear2 | 4.0000 | 4.10000 | Forward ratio differs |
| Engine/Gear6 | 0.95000 | 1.00000 | Top listed ratio differs |

The established `gaWheelSplinePlaybackAI` offset path uses `WheelBase/2` for the two longitudinal anchors and `TrackWidth/2` for the lateral anchors. If the ordinary model's visible wheel placement consumes the same Car0 fields, the front/rear anchors move inward by 0.20 m longitudinally and 0.025 m laterally per side. That is a testable visual prediction, not proof that physical contact points use this spline path. Wheel placement toward the imported Trooper body is the strongest visible expected effect. Ride height should not change from these family values.

The raw base package also changes front/rear spring, damper, unsprung mass, wheel damping, and wheel moment of inertia. The five Steering values are identical: MaxSpeed `60.00000`, MaxSteer `0.70000`, MinSpeed `25.00000`, SteerOffset `0.00000`, and SteerScale `1.00000`. This pair does not predict a steering change from the Steering group. Engine behavior may feel different if the normal runtime consumers use the changed torque, damping, and gear values; driving feel alone is not the initial pass criterion.

All 17 differing `DamageParams` values will also be read from Trooper if the normal base reader consumes them. The game already has damage-capable Trooper model resources, but damage behavior is recorded as an observation and is not required for a successful first binding test.

## Successful human runtime test — R-PHYS2.2

The human ran the ordinary retail race in x32dbg with the imported Trooper
model still occupying the existing Navara carrier. The successful hit was the
second/mirrored lookup branch at `0044EE69`, immediately before `MOV EAX,[EAX]`.
The family pointer was temporarily redirected to a process-local
`Trooper\0` buffer and restored before downstream broker processing. This was
a process-memory-only experiment; the on-disk EXE and game assets were not
changed.

| Observation | Result |
|---|---|
| Retail EXE SHA-256 | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` |
| Lookup breakpoint | `0044EE69` |
| EBP / participant | `0` / Car0 |
| ESI / carrier type ID | `7` / Navara |
| Catalog pointer slot in that process | `03488A78` |
| Original pointer in that process | `03489640` -> `Navara` |
| Base reader | `FUN_00493E30` received `Trooper`; caller return `0044F0D2` |
| Overlay reader | `FUN_00493FD0` received `Trooper/Player1` |
| Runtime writer | Normal `FUN_004938C0` path ran for the participant |
| Race | Started |
| Visible wheels | Corrected to the imported Trooper model |
| Vehicle behavior | Distinct from Navara and operated with Trooper-specific behavior |

The heap addresses in the table are evidence for that process only. They are
not stable identifiers and must not be embedded in a launcher, patcher, or
configuration. The runtime result proves that the complete surviving Trooper
package is accepted by the native retail broker and produces functional
Trooper-specific behavior; it does not prove that each of the 147 fields
individually affects simulation.

An earlier plan proposed observing the first branch at `0044EDFB` and checking
the copied overlay near `0044EE25`. The successful run instead used the
alternate branch at `0044EE69`; only the values in the observation table above
are reported as runtime evidence. The runtime implementation phase must find
a persistent mechanism and must not copy addresses from this table.

### Car0 verification and success criteria

At `0044F343`, the ordinary caller has returned from `FUN_004938C0` with participant index 0. Static evidence shows that writer formats the path through `FUN_00493600` as `Vehicles/Car0` and writes all eight matching groups. Combined with observed reader arguments `Trooper` and (when enabled) `Trooper/Player1`, this confirms the native broker path to Car0. The internal dynamic config store's numeric field addresses are not mapped in this phase, so do not claim a debugger readout of Car0 values unless the human captures one with additional evidence.

Minimum success: the expected base and overlay strings are observed, the optional `FUN_00493FD0` call executes, the Car0 writer returns for participant 0, the game reaches the race, and wheel placement visibly moves toward the Trooper body. Record engine, suspension, steering, and damage behavior separately. A non-crash alone is not success.

If the broker continues but the model does not visually align, first distinguish the expected `WheelBase`/`TrackWidth` values from model-resource wheel geometry. Do not immediately patch floats. If a reader rejects a path, stop at the first missing/rejected subtree; current corpus coverage shows all required base groups and player overlay fields exist.

## Runtime test record

```text
HUMAN_RUNTIME_CONFIRMED — successful x32dbg pointer substitution

Base family observed: Trooper
Overlay family observed: Trooper/Player1
FUN_00493E30 caller return / participant: 0044F0D2 / Car0
FUN_00493FD0 executed: yes; Trooper/Player1
FUN_004938C0: normal writer path reached
Car0 WheelBase / TrackWidthFront / TrackWidthRear: not directly read in debugger
Race started: yes
Wheel placement: corrected for imported Trooper model
Suspension behavior: not isolated/measured
Engine/gear behavior: distinct overall handling observed; fields not isolated
Steering: not isolated/measured
Damage: not tested
Crash/error: none reported
Notes: temporary catalog pointer restored; on-disk EXE/assets unchanged
```

## Automated verification

- Focused R-PHYS2.2 tests: 8 passed, 0 skipped.
- Full synthetic suite: 295 passed, 0 skipped.
- `git diff --check`: passed.
- Automated tests validate the recorded evidence and redirect-plan fields; runtime facts above were supplied by the human operator. The agent did not launch the game.

## Next action

R-PHYS2.2 is runtime-confirmed. R-PHYS3 now traces the persistent family
catalog source and replaces manual debugger editing with a generic,
version-aware, reversible binding workflow. Do not begin cooker reconstruction
until the no-debugger binding gate in the R-PHYS3 report is met.
