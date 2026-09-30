# R5V-F readiness after E0.1c

## Decision: BLOCKED

R5V-E0.1c did not close the progress-marker tint source. The exact remaining link is:

```text
semantic source and selection rule
    -> writer/initializer
    -> Race/Car0/Colour property
```

The consumer can apply a tint, and the HUD XML contains per-widget `ObjectColour` values, but no evidence proves that either the participant source or the static widget palette produces `Race/Car0/Colour`. The owner's aquamarine description has no corresponding captured runtime number. R5V-F must not treat colour as a vehicle profile field or claim the frontend identity map is complete.

## Profile ownership boundary

Keep these proven presentation controls in the vehicle identity model:

```text
VehicleSlotProfile:
    slot_id
    vehicle_class
    internal_name
    frontend_speed
    frontend_acceleration
    frontend_handling
    frontend_endurance
    smallcarsheet_index
```

Do not add `progress_marker_colour` to `VehicleSlotProfile` without proof of vehicle dependence. If the future writer traces to participant or player state, model it in an appropriately named race/HUD participant profile. The current evidence does not yet justify selecting that profile's exact name or schema.

The unresolved T3 `Car12` Vehicle Select icon is a separate static scene/widget mapping issue. It may be carried as a bounded UI task within R5V-F after the tint producer has been closed; it must not be folded into race progress tint work.

## Next evidence-gathering step

Repeat the dynamic trace with an interactive x86 debugger session that can reach Quick Race and preserve access to registers/memory at the consumer. Capture `Race/Car0/Colour` and, if present, Car1+; identify the property backing value; then break on its race-specific write and trace the value's source object/table/index. Only after that source is proven should a Player1/Car0-only red diagnostic be prepared for human runtime confirmation.
