# ID26 preview, race and physics path

## Preview

Vehicle Select state `class0/local7` maps to absolute ID26. The selected
absolute ID remains 26 after the display-selector alias. Preview/stat code
calls the registry getter and indexes a `0x34`-byte VehicleRecord. The preview
resource builder at `0x44C4C0` obtains the owned internal-name field at `+0x20`
and requests:

```text
Vehicles/Landcruiser/complete
```

The T1_Car8 icon is a separate scene binding and does not change resource
selection.

## Offline Quick Race and actor resources

The Quick Race selection path carries the selected absolute ID to
`Race/Car0/CarID`. Race setup and model lookup index the registry record, read
its owned internal name, and use the resulting family for car/wheel resources.
Retail code builds the family paths from record data; no per-ID model switch is
needed for the donor duplicate.

The `Car%d` path in physics readers denotes a race actor instance slot, such as
`Car0`, rather than an absolute vehicle ID. The actor's `CarType`/`WheelType`
name values connect that instance slot to the selected record's internal
family. With record26 initialized as `Landcruiser`, the existing named
Landcruiser physics values are the donor source. This statement is a static
dataflow result; it is not a runtime confirmation for the new slot.

## Other record fields

The already traced race setup reads the same record for:

- frontend preview `complete.dx`;
- race `car.dx` and `wheel.dx` resource family;
- physics family attributes;
- SmallCarSheet selector at `+0x1C` (ID0 donor value 9);
- race marker RGBA at `+0x24..+0x30` (ID0 donor vector).

All record access occurs after the new allocation and array construction. The
P1 test should verify model, wheels, physics, collision, damage, camera,
top-left and Results icons, race colour, stage completion and return to menu.
P1 must wait for P0 FULL PASS.

## Remaining runtime boundary

The old ID25 Trooper profile remains part of the candidate so original
T3/Trooper selection can be checked during P0. The candidate does not add ID26
to campaign opponent generation and does not establish campaign save or
network support. Use an isolated offline test installation and a disposable
profile.
