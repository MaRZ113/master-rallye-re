# Main menu and command dispatch

The retail main window procedure 005B0880 forwards WM_COMMAND's low 16-bit ID to 005B0990. On paint it rebuilds the menu through 005B1320 and Win32 menu helpers.

005B1320 creates only Game → Reset… (0x32), separator, Exit (0x2F). These are the only items in the mapped retail main-menu builder.

The larger dispatcher calls 005B1370 for Game commands and 005B1F80 for Scene commands, then handles editor/debug/tool IDs in a switch. Selected paths:

| ID | Target/behavior | Registered in mapped main menu |
|---:|---|---|
| 0x31 | Open Game XML → 005B14D0 | no |
| 0x32 | Reset Game after confirmation | yes |
| 0x33 | Save Game XML → 005B16C0 | no |
| 0x34–0x37 | Save As modes 1–4: Game, Options, PlayerState, PS2 variant | no |
| 0x27 | Broker Editor → 0065E990 | no |
| 0x2E | Egg Editor → 00657FD0 | no |
| 0x30 | Flow Builder → 00662D90 | no |
| 0x3B | Marker Editor → 0065B870 | no |
| 0x3F | Generic tree/object editor → 005B0720 | no |
| 0x4A | Particle Editor → 006557C0 | no |
| 0x4F–0x56 | Open/reset/save Scene and toggle Scene load keys | no |
| 0x58 | BuildData object → vtable 00692F88 +4 → 005B2F80 | no |

Other switch cases create debug/view-model objects or indexed tree-editor routes. See command-map.csv for selective mapping.

For BuildData, 006018E0 grows a pointer array, appends the object and immediately calls virtual slot +4. The object is retained in that manager at least through the call; its eventual cleanup policy is UNKNOWN. Flow Builder opens directly rather than using this command-object route.

Evidence terms are kept separate: code exists; command ID mapped; menu item registered; ordinary UI route confirmed; runtime action observed. Most hidden tool IDs stop at “command mapped”.
