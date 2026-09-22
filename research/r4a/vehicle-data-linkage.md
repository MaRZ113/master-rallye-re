# R4A vehicle data linkage

## Direct data links

`DataGame/Game.xml` registers `vehicles`, `collision`, `Drivers`, `Cameras`,
`Damage`, and `Modifications` as separate XML brokers. The following names are
copied verbatim from those files.

### `vehicles.xml`

The file contains 35 vehicle identifiers, while `DataGx/Vehicles` contains 26
resource folders. Folder/config names match case-insensitively for the normal
families, but the XML also contains variants such as `Pajerostripe`,
`Navarabig`, `Megane2`, and `Custom`; folder identity is therefore not a
one-to-one resource filename declaration.

Per-vehicle fields include:

- `Dimensions/Length`, `Width`, `Height`, `WheelBase`, `TrackWidthFront`,
  `TrackWidthRear`, `WheelRadiusFront`, and `WheelRadiusRear`;
- `Chassis/TotalMass`, `MomentOfInertia`, `UseCuboidMOI`,
  `CentreOfGravity`, `Restitution`, `SlidingFriction`, and other dynamics;
- `Suspension/Front/*` and `Suspension/Rear/*`, including `RideHeight`,
  `WheelMOI`, `MaxBounce`, `MaxDroop`, and the three literal
  `SuspAppPointOffsetLat/Long/Vert` fields;
- vehicle-specific `DamageParams/*` thresholds, scores, strengths, and maxima.

**DATA LINK / CONFIRMED:** wheel dimensions and suspension physics are external
to `wheel.dx`. No field directly gives a wheel model filename or four wheel
instance transforms.

### `collision.xml`

The file defines global `ConvexHull/PlaneThickness` and 22 named overrides.
Nine of the 24 literal car `$chull(name)` values match an override name
case-insensitively (`Bruno`, `Chevy`, `Frontera`, `Landcruiser`, `Sbuggy`,
`Navara`, `Rmonster`, `Tata`, `Xtrail`). Other hulls use the global value.

**DATA LINK / HIGH:** the shared literal term `ConvexHull` plus name matches
link the XML tolerances to `$chull(...)` source meshes. The XML contains no
resource filename, node index, draw index, or activation flag.

### `Damage.xml` and `vehicles.xml`

`Damage.xml` contains only global maxima:

- `Damage/MAX_Engine`
- `Damage/MAX_Suspension`
- `Damage/MAX_SteeringWheel`
- `Damage/MAX_Tyre`
- `Damage/MAX_Gear`

Vehicle-specific behavior is parameterized under `Vehicles/<id>/DamageParams`.
No inspected XML value names a mesh, draw, vertex/index range, glass group, or
DX resource.

### `Modifications.xml`, `Cameras.xml`, and `Drivers.xml`

`Modifications.xml` contains per-player suspension/engine adjustments,
including `RideHeight`; it does not name DX resources. `Cameras.xml` contains
camera parameters but no model binding. `Drivers.xml` contains ten
`gaIContDriverParams` records and animation/control parameters, but no crew
mesh name or vehicle DX filename.

### DataScene broker registration

`DefaultVehicleParamBrokerRegistration.xml` uses the literal
`CarModelDataFile` with value `RMonster`. This is a direct link from a scene
broker to a vehicle-family identifier, not to `car.dx` or `complete.dx`.
`DefaultTyreParamBrokerRegistration.xml` similarly names `TyreType`.

## Evidence graph

```text
CarModelDataFile -> vehicle-family identifier             CONFIRMED
vehicle identifier -> vehicles.xml physics/damage fields HIGH by naming
vehicle folder -> car/complete/wheel resources            CONFIRMED corpus
car TXT $chull(name) -> collision.xml ConvexHull settings HIGH
car tag-7/tag-8 labels -> intact/broken glass textures    HIGH
XML -> exact car/complete/wheel filename                  UNKNOWN
XML -> draw/group/vertex damage binding                   UNKNOWN
```
