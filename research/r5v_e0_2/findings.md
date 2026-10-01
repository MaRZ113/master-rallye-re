# R5V-E0.2 — Vehicle Select icon slot and generic scene extender

## Status

**Static analysis and candidate preparation: PASS. Runtime P0: PENDING.** Retail
has 11 T3 icon widgets and no widget for class-local index 11 / vehicle ID25.
The carsheet does contain frames, so the exact root cause is
**SCENE_OBJECT_MISSING**. A scene-only `T3_Car12` candidate and a structurally
validated full `Data.sma` candidate have been staged under ignored
`research-output/r5v_e0_2/`. The diagnostic icon uses the existing Astero frame
5; it is not represented as Trooper artwork.

The reusable generator is manifest-driven across T1/T2/T3 classes. It checks
class-local numbering, an explicit class-to-ID base, row ID, frame, and a list
of position properties supported by the selected build profile. Synthetic
tests demonstrate T1_Car8, T2_Car8, T3_Car12 and (with a hypothetical
13-position profile) T3_Car13. The actual retail profile lists only
Button0XPos through Button11XPos, so it correctly refuses T3_Car13 until a
future phase proves support for Button12XPos. No T1/T2 mappings or game limits
were changed.

## Findings

- Retail `VehicleSelect.xml` has a sibling `List Name="cars"` in
  `EggLists_Version4`; all 25 `Tn_CarN` widgets are direct children of this
  list. The separate `List Name="VehicleSelectScreen"` contains other screen
  objects.
- Class-local icon identity is represented by the widget name, the
  `gaFrontendXYButtonAI` X/Y IDs and a static `en2d Image Bank Index`. The
  widget's image frame is not read from VehicleRecord, SmallCarSheet, the
  runtime family string, or the absolute ID.
- `0x481E20` maps T3 local 11 to absolute ID25. `0x481950` generates
  Button0XPos through Button11XPos (`i < 12`); it does not assign carsheet
  frames. The T3_Car12 scene object is the missing icon binding.
- Frame 5 is already used by retail T3_Car3 / ID16 (Astero) and is a safe,
  recognizable diagnostic donor. Frame 25 is a red-and-white SUV image, not a
  proven Trooper icon. Frame 31 depicts a forklift, but no stock T3_Car12
  binding points to it.
- The two historical demos contain T2_Car8 widgets, supporting a reusable
  class-slot scene pattern. Neither has T3_Car12 or an identified Trooper
  Vehicle Select icon. Their assets remain build-specific and were not copied.

## Candidate

The source retail scene SHA-256 is
`EC7FD6372FE5008B1039EB8E09890EF3B37396DAD1581568AF439CBB611B58E1`. The
generated scene SHA-256 is
`7676532F4BFAD1A196A5AD39FA3941BFE9EBDD9E636A58C5A8FCF9F18CC3F95A`. It
contains exactly one appended `T3_Car12` widget with:

| Field | Candidate value |
|---|---|
| Class/local / absolute ID | T3 / 11 / 25 |
| Image bank | `frontend\\vehicleselect\\carsheet`, FileType 1 |
| Frame | 5, the existing Astero diagnostic donor |
| Navigation IDs | X=11, Y=2, Button ID=1 |
| Position property | `Frontend/VehicleSelect/Button11XPos` |
| Unlock AIs | None; the template is an unlocked T3 widget |

The generated full archive is
`research-output/r5v_e0_2/runtime-test/Data.sma`, SHA-256
`BB3C69CB97ADD992BF261F64C6ABAFAABAB946AB5CAE7E496D2D486C31A18020`.
Compared with the source retail archive
`87EEC21C395245F7C08D43553F2E2E0341D66C0D1E16EB683D0C79C3F7C2B06F`, it has
the same 8,015 members and exactly one different member:
`DataScene/FrontendScreens/VehicleSelect.xml`. The source archive and source
scene were not modified.

## Readiness

The scene-level mechanism is prepared, but it has not yet been shown in the
game. **R5V-F remains BLOCKED pending the human P0 runtime check**: confirm the
donor icon appears at T3 local 11 / ID25 and stays correctly navigable after
moving between entries and classes. The candidate tests Vehicle Select only;
it does not require a race. Authentic Trooper-specific Vehicle Select artwork
remains unidentified, but that is not a blocker for the structural P0.

See [scene inventory](vehicle-select-scene.md), [carsheet inventory](carsheet-inventory.md),
[Trooper asset search](trooper-icon-search.md), [generic design](t3-car12-design.md),
[runtime test](runtime-test-plan.md), and [validation](validation.md).
