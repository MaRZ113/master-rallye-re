# Vehicle Select carsheet inventory

## Retail resource bank

| Property | Value |
|---|---|
| Scene resource name | `frontend\\vehicleselect\\carsheet` |
| Container | `DataGx/Frontend/VehicleSelect/carsheet.dxb` |
| Container SHA-256 | `712D655CD01FE2A6C7B5D3F9FD6B47234FDCC0430F1FCF4A85E383454131547F` |
| Indexed frame count | 32, indices 0–31 |
| Frame pattern | `carsheet_NNN_000.dxt` |
| Frame dimensions / bytes | 128x128 / 65,556 bytes each |
| File type in scene | 1 |

The DXT files are decoded RGBA payloads with the 20-byte format header and
`128 * 128 * 4` image bytes. No indexed frame assets were copied into Git.
Static inspection used the ignored contact sheet at
`research-output/r5v_e0_2/icons/carsheet_contact.png`.

## Selected frame evidence

| Index | Retail Vehicle Select use | Visual observation | SHA-256 |
|---:|---|---|---|
| 5 | T3_Car3 / ID16 | Astero-like teal rally vehicle; diagnostic donor | `370007A674232CB2BB6FDAB6FC00C2BEEF5247F7FBFCDBAEAE5D4D3E1F73D65D` |
| 25 | no stock widget binding | red-and-white SUV; not identified as Trooper | `675C37F6BA61527A4E1C5B97BF942B06C98DFDCAB15BE2033DEB3F7CA1009065` |
| 30 | T3_Car11 / ID24 | UFO-style bonus icon | hash not needed for the slot proof |
| 31 | no stock T1/T2/T3 widget binding | forklift | `B2EFE3BF4D8E066DC7D187660AD76A2437F2B8D6ED00C33E495DEC509F479C10` |

Frame filenames do not encode registry IDs. In particular, the existence of
`carsheet_025_000.dxt` does not make it ID25's icon, and neither frame25 nor
frame31 is currently bound to T3_Car12.

Retail's 25 car widgets reference frames
`[3,10,18,27,19,17,16,23,1,2,12,20,9,24,6,13,5,11,8,7,0,28,26,21,30]` in
widget order. Frames 25 and 31 are not in that sequence.

## Historical comparison

The demos are separately unpacked builds and contain no `Data.sma`:

| Build | Vehicle Select widgets | Carsheet indices | T2_Car8 | T3_Car12 |
|---|---:|---|---|---|
| demo-8.4.1 | T1=7, T2=8, T3=10 | 16 indexed images (0–15) | present; X ID 7, Button7XPos, frame 15 | absent |
| demo-9.3.1 | T1=7, T2=8, T3=11 | 22 indexed images (0–21) | present; X ID 7, Button7XPos, frame 15 | absent |
| retail | T1=7, T2=7, T3=11 | 32 indexed images (0–31) | absent | absent |

The shared T2_Car8 pattern is comparative evidence that the scene format is
not unique to a T3_Car12 object. Its demo frame15 is build-specific and is not
identified as retail artwork. Demo identities remain separate: demo-9.3.1
Forester is not retail NewRav, and demo-8.4.1 LandCruiser is not retail
WildCat.
