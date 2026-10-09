# Frontend identity and selection lifecycle

Frontend vehicle identity is multi-channel. The established consumers include
Vehicle Select manufacturer/model (`0x33`/`0x34`), Quick Race combined name
(`0x35`), Race Options split manufacturer/model, Vehicle Setup combined name,
and Race Details combined name. These consumers were qualified for ID26 on
their respective research candidates; one localization fix is not a global
vehicle-name fix. Runtime `CarType` and `WheelType` remain separate from
display selectors.

The J0 planner emits both absolute-physical-ID to class/local and
class/local-to-absolute mappings. For the verified mappings:

| Vehicle | Physical ID | Class | Local ordinal |
|---|---:|---|---:|
| Navara | 7 | T2 | 0 |
| R5VQualifier | 27 | T2 | 7 |
| Mercedes | 26 | T1 | 7 |

## Runtime re-entry divergence

Four earlier captures with executable SHA
`90abfbf9825f1cc7acebb3a1a2811a179e6474f2406433854e1ffdbc60bdd955` were
verified from their actual JSON/raw pairs. `r5vq_navara-reset` retains
`Frontend/QuickRace/Car0=27` while the Vehicle Select scene reports CarModel 7,
selectedCar 7, T2/local ordinal 0, and NISSAN/NAVARA. In
`r5vq_quickrace-preview`, the stored ID remains 27 while CarModel and
selectedCar are 27 and the local ordinal is 7 with R5VQualifier labels. There
are 21 changed Broker paths between these captures.

This is a scene initialization/restoration mismatch. It does not prove that the
physical ID27 record was lost, that `selectedCar` is the persisted commit
oracle, or that a user action committed Navara automatically. The later
`navara_choice` capture may reflect deliberate user selection. The exact native
initializer/writer and the single-player versus SplitScreen ownership
differences remain unknown. J0 does not patch this state. It is a required
runtime-release gate, and synthetic mapping tests prevent a future integration
from conflating physical IDs and local ordinals.

The 2026-10-09 J.2 archive adds `R5VQ-quickrace-menu` and
`R5VQ-carselect-menu` captures where the stored Quick Race physical ID and
visible Vehicle Select `CarModel` are both 27. This is a consistent selection
snapshot, but it does not show the sequence after race completion and a second
Vehicle Select scene construction. The required repeatable post-race re-entry
test therefore remains open; the J.1 runtime bundle still does not claim to
fix or globally rewrite scene-local selection initialization.

The checker reports stored Quick Race CarID, displayed CarModel, selectedCar,
class, and `UI/XYButton/XValue` separately. A divergence is reported without
claiming loss or commit. Class switching and SplitScreen must retain independent
selection ownership in a later frontend integration pass.
