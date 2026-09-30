# Race Results icon selector — retail

## Producer: result participant ID to registry integer

FUN_0047C840 builds the Race Results values. In the participant loop it reads
the result participant's vehicle ID from participant +0x08, calls registry
accessor FUN_0045A3C0, and computes:

registry_object_base + vehicle_id*0x34 + 0x20

The accessor returns the registry object base, not the first record address.
The first VehicleRecord begins at object base +4, so the expression above is
exactly:

VehicleRecord[vehicle_id] + 0x1C

This is the extra integer field, not the owned internal-name string at record
+0x20. The raw retail instructions at 0x0047CB41–0x0047CB5E show the
participant ID load, accessor call, stride multiplication and field load.

The producer formats Frontend/RaceResults/Car%d and writes this integer to
the matching property. The literal is referenced in the Ghidra extract at
FUN_0047C840. The results scene has Car0 through Car7; each uses the
smallcarsheet model with Image Bank Index 0 and an Image* property linked to
Frontend/RaceResults/CarN. FUN_00530300 watches the property and applies
changes to the embedded image selector through FUN_004E23E0 and
FUN_004E1FF0.

## ID25 result

The R5V-E0 ID25 initializer deliberately supplied the same +0x1C integer as
Astero: 0. Therefore the Race Results selector chooses smallcarsheet frame 0.
The retail file smallcarsheet_000_000.dxt is 32x16, 2,068 bytes, SHA-256
3c8be06737bde2906c4e68b1f64e46a69e18e674186ec38a1d81063c7293871d. Visual
inspection shows an Astero-like small car; the owner also reports Astero at
Race Results. The dataflow to selector value 0 is **PROVEN**; the exact car
identity of the drawn frame is **STRONGLY_SUPPORTED**, not encoded in the
selector itself.

Retail frame 29 also exists and visually resembles Forklift, but no normal
record or ID25 binding to 29 was established. Its presence is not proof of a
vehicle assignment.

## Separation from other channels

This results path consumes neither the internal Trooper string nor the
Vehicle Select carsheet index nor the progress HUD frame. It uses:

race participant vehicle ID -> VehicleRecord +0x1C -> numeric image index ->
smallcarsheet frame

The field was previously recorded as an untyped extra integer. For this
specific consumer it is now identified as the Race Results image-bank
selector. No claim is made that this is its only use in the executable.
