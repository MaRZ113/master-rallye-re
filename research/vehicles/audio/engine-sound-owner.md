# `gaAiVehicleSound` ownership

`FUN_00408660` obtains `Race/NumCars`, loops `slot = 0 .. NumCars-1`, creates
the per-slot `VehicleSound%d` binding, and invokes `FUN_00408F20(slot)`. This
includes slot 0. The same constructor and vtable/update path therefore serve
the human player and AI participants.

The constructor stores the participant slot at object offset `+0x54`; the
following bind/update code uses that slot to build `Car%d`,
`Race/Car%d/Finished`, `Controller/Car%d`, and other per-car paths. Separately,
the constructor reads the physical CarID through the Race broker getter and
uses it for engine-audio selection.

`FUN_00409EB0` is the per-frame consumer. It reads the constructed sound
object, its tuning state, and several per-car broker values. The raw fields
and table-selection behavior are documented; the exact semantic names for the
scalar/table axes remain unknown. This phase does not infer RPM, throttle,
load, or pitch names from plausible values.

The “Ai” in `gaAiVehicleSound` is historical/internal naming, not proof that
the component belongs only to opponent AI. If a future AI participant is
assigned physical CarID26, the same selector seam would apply there. This is
static architecture evidence only; adding ID26 to an AI pool is out of scope.
