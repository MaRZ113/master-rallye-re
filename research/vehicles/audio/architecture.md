# Vehicle engine-audio architecture

## Identity layers

The retail path has two identities that the G.2 candidates keep separate:

1. **Physical participant identity** — `Race/CarN/CarID`, which continues to
   identify the vehicle record, model, class, wheel family and physics family.
2. **Audio selector** — the CarID value read by `FUN_00408F20` and consumed by
   its native sample/tuning switches.

Retail does not expose a separate named audio-profile field. The selector is
an input to constructor logic that combines:

* a resource path such as `vehicles/rev9` or `vehicles/engine9`;
* a sample-object scalar written at offset `+0x1C` (raw float bits recorded in
  the matrix);
* a tuning-object field written at offset `+0x14` (raw float bits); and
* one of four pairs of 60-entry 16-bit lookup arrays in read-only executable
  data.

The sample path and tuning selection are distinct decisions inside one
constructor. Several vehicles share a sample family but retain different
scalar/table combinations. The 25 tuned retail identities have 25 distinct
composite combinations across the fields recovered here. This explains why
some vehicles can sound broadly alike without having byte-identical complete
profiles.

## Owners and data locations

| Role | Evidence |
|---|---|
| Per-race sound manager | `FUN_00408660` reads `Race/NumCars` and loops active slots |
| Per-participant component constructor | `FUN_00408F20` |
| Per-slot CarID getter call | `0x00408FB4 -> FUN_004AC660` |
| Race broker path pieces | `FUN_004ABCE0` registers `Race/Car` and `/CarID`; slot string is composed between them |
| Warning literal | `gaAiVehicleSound: Warning - untuned car engine sound used (CarID %d)` |
| Warning producer | `FUN_00408F20`; only constructor xref found in pristine retail |
| Sample/tuning object creation | resource path passed through the retail sound-resource constructors |
| Curve arrays | `.rdata`, retail addresses and byte hashes in `stock-audio-matrix.json` |
| Per-frame consumer | `FUN_00409EB0`; reads the constructed per-car sound/tuning state |

The code class name contains “Ai”, but this component is not AI-opponent-only.
The manager creates it for Car0 and every other active CarN.

## Limits

The static code shows profile selection and per-frame consumption. It does not
establish what each float or curve axis means, nor whether an audible donor is
subjectively suitable for Mercedes. Tyre, road, collision, starter, gearbox,
and non-engine sound design are outside this phase unless they share the
selected engine profile (no such coupling was needed for the current proof).
