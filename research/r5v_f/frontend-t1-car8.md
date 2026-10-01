# T1_Car8 frontend binding

The P0 scene candidate appends one `T1_Car8` node to the retail/E0.2
VehicleSelect scene. It clones the same-class `T1_Car1` widget and preserves its
button AI. The binding uses:

| Scene field | Value |
|---|---|
| Class/local | T1 / 7 |
| Sparse physical ID | 26 |
| Image bank | `frontend\\vehicleselect\\carsheet` |
| Carsheet frame | 3 (retail Landcruiser / ID0 donor) |
| Button X ID / Y ID | 7 / 0 |
| Position key | `Frontend/VehicleSelect/Button7XPos` |

The scene extension uses the tested generic overlay generator. The R5V-F icon
manifest supplies `T1.sparse_vehicle_ids[7]=26`; it does not change the generic
generator into a hard-coded T1_Car8 tool. The source scene was the staged E0.2
candidate scene containing the existing `T3_Car12`; the generated scene keeps
T3_Car12 and appends only T1_Car8.

The candidate archive has 8,015 members, identical member order to the staged
E0.2 archive, and exactly one changed member: `DataScene/FrontendScreens/VehicleSelect.xml`.
T3_Car12 remains bound to ID25/frame5/Button11XPos. No proprietary art or demo
asset is committed.

During P0, verify that frame3 appears as the eighth T1 icon, it sits at
Button7XPos, and the selected preview uses the Landcruiser `complete.dx`
resource family. The runtime image presentation is pending human confirmation.
