# Cross-build command correspondence

The ID is the `WM_COMMAND` ID accepted by the main-window dispatcher unless explicitly called a tool-local ID. Handler addresses are semantic matches established from switch cases plus window titles, constructor/menu paths, file dialog behavior, and neighboring calls. Addresses are build-specific; they are not matched by proximity.

## Embedded tools

| Tool | 8.4.1 | 9.3.1 | 9.10.0 | retail |
|---|---|---|---|---|
| Broker Editor | `0x26 → 00543670` | `0x27 → 00619480` | `0x27 → 0064B010` | `0x27 → 0065E990` |
| Egg Editor | `0x2D → 0053CE50` | `0x2E → 00612E20` | `0x2E → 00644650` | `0x2E → 00657FD0` |
| Flow Builder | `0x2F → 00547A00` | `0x30 → 0061D8D0` | `0x30 → 0064F490` | `0x30 → 00662D90` |
| Marker Editor | `0x3A → 00540870` | `0x3B → 00616680` | `0x3B → 00647EF0` | `0x3B → 0065B870` |
| Particle Editor | `0x49 → 0053AB60` | `0x4A → 00610620` | `0x4A → 00641E40` | `0x4A → 006557C0` |
| Generic tree/editor | `0x3F` and `0x40–0x49` family | `0x3F` and `0x40–0x49` | `0x3F` and `0x40–0x49` | `0x3F` and `0x40–0x49` |

The 8.4.1 IDs are one lower for the five named editor openers; the shift occurs by 9.3.1 and then remains stable. This describes observed correspondence only.

## Game file commands

| Build | Dispatcher | Open | Reset | Save family |
|---|---|---|---|---|
| 8.4.1 | `004EC580` | `0x32 → 004EC8D0` | `0x31` | `0x33–0x36 → 004ECAB0(args 1–4)` |
| 9.3.1 | `006005C0` | `0x31 → 00600720` | `0x32` | `0x33 → 00600910`; `0x34–0x37 → 00600AF0(args 1–4)` |
| 9.10.0 | `00632010` | `0x31 → 00632170` | `0x32` | `0x33 → 00632360`; `0x34–0x37 → 00632540(args 1–4)` |
| retail | `005B1370` | `0x31 → 005B14D0` | `0x32` | `0x33 → 005B16C0`; `0x34–0x37 → 005B18A0(args 1–4)` |

The 8.4.1 open/reset numbering differs from later builds. Save variants map to mode arguments; they are not safe inspection commands.

## Scene file commands

| Build | Dispatcher | Open | Reset | Save and other mapped actions |
|---|---|---|---|---|
| 8.4.1 | `004ED190` | `0x4E → 004ED470` | `0x4F` | `0x50 → 004ED690(0)`, `0x51 → 004ED830`, `0x52 → 004ED690(1)`, `0x53` alternate, `0x54–0x55` toggles |
| 9.3.1 | `006011D0` | `0x4F → 006014B0` | `0x50` | `0x51 → 006016D0(0)`, `0x52 → 00601870`, `0x53 → 006016D0(1)`, `0x54` alternate, `0x55–0x56` toggles |
| 9.10.0 | `00632C20` | `0x4F → 00632F00` | `0x50` | `0x51 → 00633120(0)`, `0x52 → 006332C0`, `0x53 → 00633120(1)`, `0x54` alternate, `0x55–0x56` toggles |
| retail | `005B1F80` | `0x4F → 005B2260` | `0x50` | `0x51 → 005B2480(0)`, `0x52 → 005B2620`, `0x53 → 005B2480(1)`, `0x54` alternate, `0x55–0x56` toggles |

Retail `0x55` and `0x56` read/write the Scene `HatchEggsOnLoad` and `ResetSceneOnLoad` broker keys. Save handlers reach `CREATE_ALWAYS` serialization paths. Labels for the 8.4.1 `0x53–0x55` variants remain conservative because the internal flow differs.

## BuildData

Retail global ID `0x58` creates a command object at `005B2960`, assigns vtable candidate `00692F88`, then calls execute slot `+0x04` at `005B2F80`; its recursive walker is `005B2DA0`. No semantically matched handler was recovered in 8.4.1, 9.3.1, or 9.10.0. Retail execution is write-capable through ordinary resource/cache loaders and excluded from runtime testing.

Machine-readable crosswalk: `command-correspondence.json`.
