# Runtime object separation and layout

The full bounded tables are in `rigid-object-layout.json`; offsets are hexadecimal and relative to the specified owner, never fixed live RAM addresses.

| Representation | Allocation | Important fields |
|---|---:|---|
| gaAiRigidBody AI | 0x3c | +08 vtable, +0c body, +10 shadow, +14 mass, +18 trigger, +1c MOI, +2c/+30/+34/+38 owner state |
| Registered physical body | 0x1dc | +00 pause, +14 vtable, +18 integrator, +20/+24 mass/inverse, +28/+4c/+70 inertia matrices |
| Physical pose/state | within body | +a0 position, +ac quaternion wxyz, +bc rotation, +104 P, +110 L, +11c velocity, +128 omega |
| gaPhysicsManager | 0x74 | +20/+24/+28 prop pointer vector, +14/+18/+1c separate vehicle vector, +34 detector |
| Physics transform AI | 0x14 | +0c Broker key, +10 DelayInterpolation property |
| Per-entity convex instance | 0x20 | +10 body, +14 surface category, +18 entity name |
| Visual entity en3d | existing scene representation | +20..+5c 4x4 world matrix; +0c model/resource ID |

Body state uses 13 scalar values: position(3), quaternion(4), linear momentum(3), angular momentum(3). Derived v, omega, rotation and world inverse inertia are not additional integrator state values.

Constructor and init are separate evidence stages. Owner+34/+38 acquire their selected initial values during init. Body local COM +94..+9c is initialized from startup zero globals; later COM writers were not exhausted. No diagnostic silently infers a COM from mesh bounds.

Exact loads/stores by original base register are preserved in each function inventory item. Register offsets alone do not assign a semantic type to unrelated temporaries. Unknown helper layouts remain unknown.
