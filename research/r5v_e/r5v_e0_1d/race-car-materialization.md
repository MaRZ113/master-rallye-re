# Bounded `Race/CarN` materialization trace

## Scope and method

The retail Ghidra Bridge project was opened from the existing read-only copy at `research-output/r5v_e/_research_tmp_r5v_e0_1/ghidra_project_readonly_copy`, using the existing Ghidra 12.0.4 installation. A task-local Bridge YAML and isolated Ghidra user directories were used under ignored `research-output/r5v_e0_1d/ghidra/`; the installed Bridge config and original project copy were not edited.

The inspected cluster was limited to `FUN_0048E2D0`, `FUN_0048EB40`, `FUN_004C0B20`, `FUN_004BCA30`, `FUN_004B6A00`, `FUN_0047B780`, `FUN_004ADFB0`, and `FUN_004ADF50`, plus their direct call context where needed.

## Findings

| Function | What the binary establishes | Colour producer? |
|---|---|---|
| `FUN_0048E2D0` | Race-level setup; under a race-type condition, calls `FUN_0048EB40`. | No Colour value identified. |
| `FUN_0048EB40` | Iterates race/car context. In its `RecordSpline` path it constructs a spline recorder and calls `FUN_004C0B20`. | No Colour assignment identified. |
| `FUN_004C0B20` | Constructor for a `gaVehicleSplineRecordAI` object. Builds/reads `Race/Car%d/CarType` and `Race/RaceName`, calls `FUN_004BCA30` and `FUN_004BC590`, then registers/holds `Car%d`, `Controller/Car%d`, `ControllerCarBrokerAccess`, `Race/Car%d/Time`, and `Race/Car%d/Finished` path objects. | No Colour key or value assignment in this constructor. This is a spline-record observer/helper, not the general participant producer. |
| `FUN_004BCA30` | Lazily creates shared car configuration state through `FUN_004BB240`. | No Colour source established. |
| `FUN_004B6A00` | Handles `Race/Car%d/DriverID`, car/driver setup and vehicle resource paths. Uses the generic property API for the driver field. | No Colour write found in this function. |
| `FUN_0047B780` | Reads `Frontend/QuickRace/Car0` and `Car1` through `FUN_004ADFB0`; writes selected ID and class/type state through `FUN_004ACAF0` and `FUN_004ACC10`. | No Colour write. |
| `FUN_004ADFB0` | Reads `Frontend/QuickRace/Car0` for argument 0 and `Car1` otherwise. | Getter only. |
| `FUN_004ADF50` | Writes `Frontend/QuickRace/Car0/Car1` through the generic setter, but has zero direct callers in the analyzed retail project. | Not evidence of the live colour producer. |

The participant setup around `FUN_0048EB40` reads/uses race data and the spline recorder branch, but this trace does not reveal the routine that writes the shared runtime value consumed as `Race/Car0/Colour`. No direct source object, palette, index, or assignment order was recovered.

## Generic property writer limit

`FUN_004B6A00` and `FUN_0047B780` demonstrate generic property setters for other keys. Following those setters confirms that they handle DriverID, CarID, and CarType inputs; it does not lead to a colour value. A writer could still use a schema or field table without embedding the full `Race/Car%d/Colour` literal. That possibility remains open. No claim of “no writer exists” is made.

## Demo evidence

No demo executable was needed for this bounded trace. No demo analysis was performed in this phase.

## Evidence location

Raw Ghidra Bridge decompilations, assembly, P-code, and context exports are ignored under `research-output/r5v_e0_1d/ghidra/`. In particular, `race-instance-properties-asm.txt` shows the sibling key setup in `FUN_004C0B20`, and `race-participant-setup-asm.txt` shows the conditional call from `FUN_0048EB40`.
