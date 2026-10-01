# T3_Car12 implementation and generic slot design

## Current slot specification

The candidate appends one `Egg Name="T3_Car12"` to the retail
`EggLists_Version4/List Name="cars"` list. It is a raw XML clone of unlocked
`T3_Car1`, with only four edits:

| Source field | Candidate value |
|---|---|
| Egg name | `T3_Car12` |
| `en2d Image Bank Index` | `5` (existing Astero donor) |
| `gaFrontendXYButtonAI / X ID` | `11` |
| `gaFrontendXYButtonAI / XPos*` | `Frontend/VehicleSelect/Button11XPos` |

The Y ID remains 2, Button ID remains 1, image-bank path and FileType remain
the stock values, and the original matrix/visibility/AI layout is preserved.
No unlocker/disabler is copied. This is a development diagnostic; campaign
unlock rules are not added or altered.

## Generic generator contract

`tools/prepare_vehicle_select_icon_overlay.py` consumes the committed
`icon-mapping.json` profile and a source scene. Schema version 2 keeps
build-specific facts in data:

- `class_mappings` explicitly maps a class to the current vehicle-ID base and
  row ID.
- `layout_position_properties` enumerates the position keys proven in that
  build. Retail currently lists Button0XPos through Button11XPos.
- Each slot states class, local index, absolute vehicle ID, same-class template
  widget and carsheet frame.
- The `image_bank` record defines the scene bank, container, frame pattern,
  frame count and FileType.

For each requested slot the tool checks source SHA-256, appends only the next
contiguous `Tn_CarN` sibling, verifies the class-local ID equation and row,
checks the chosen frame's DXT header/dimensions, and rejects locked templates.
It copies the original XML text for the widget and changes only its name,
image-bank frame, X ID and position key. It then proves removing the generated
node restores the source text exactly. Output stays under `research-output`,
and an existing different output is never overwritten.

The scene binding is represented as a profile field like:

```json
{
  "slot_id": 25,
  "vehicle_class": "T3",
  "local_index": 11,
  "frontend": {
    "vehicle_select_icon": {
      "image_bank": "frontend\\vehicleselect\\carsheet",
      "frame_index": 5
    }
  }
}
```

This is separate from VehicleRecord `+0x1C` / SmallCarSheet, runtime-family
name, localization ID, stats, and race-marker RGBA.

## Extension boundary for R5V-F

The generator is class-generic rather than hard-coded to T3_Car12. Synthetic
tests append T1_Car8, T2_Car8, T3_Car12 and T3_Car13 using an explicit
hypothetical profile. This tests the reusable scene-writing operation only;
it does not claim those registry slots are currently available in retail.

For current retail, local index 12 has no verified position key: the
`layout_position_properties` list ends at Button11XPos, and the runtime
updater loop ends at 12 iterations. Therefore the retail manifest rejects
T3_Car13. Adding Button12XPos to a future profile requires direct proof that
the executable and UI layout support it.

Likewise, the present class-to-ID bases 0/7/14 cannot simply be reused to
extend T1/T2: T1 local 7 would collide with the existing T2 base 7. R5V-F must
establish new class bases/registry conversion and ID uniqueness before using
the scene generator for T1_Car8 or T2_Car8. This stage changes no EXE limits,
class capacities, unlock tables or registry records.

## Why the template avoids T3_Car11

T3_Car11 / ID24 carries bonus unlock AIs. Copying it to ID25 would carry
ID24's unlock policy and would be wrong for a diagnostic. T3_Car1 has the
same class row and resource type, an unlocked widget state, and no
slot-specific disabler/unlocker AI. The generator rejects any template with
those lock AIs rather than guessing a new campaign policy.
