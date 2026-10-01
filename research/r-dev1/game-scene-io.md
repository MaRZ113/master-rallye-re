# Game and Scene XML open/save

## Game configuration

- ID 0x31 → 005B14D0 opens Game XML constrained to DataGame\\ and queues it into the broker.
- ID 0x33 → 005B16C0 saves Game values.
- IDs 0x34–0x37 route through 005B18A0 modes 1–4: Game, Options, Player State, PS2 variant.
- Save paths check read-only/writable state through 0064D980.

## Scene configuration

- ID 0x4F → 005B2260 opens DataScene\\ XML and consults Scene/HatchEggsOnLoad / Scene/ResetSceneOnLoad.
- ID 0x51 → 005B2480 saves Scene.
- ID 0x52 → 005B2620 Save As.
- IDs 0x53/0x54 route to related scene actions; exact UI labels remain uncertain.

Game serialization passes through 0052D700; Scene uses 00522550 → 0052D570. 005FE460 walks broker entries and filters:

| Mode | Save bit | XML annotation |
|---:|---:|---|
| 1 Game | 0x1 | selected entries |
| 2 Options | 0x4 | SaveOptions=True for selected entries |
| 3 Player State | 0x2 | SavePlayerState=True for selected entries |
| 4 PS2 | 0x1, excluding Type 11 XmlFilename | selected entries |

Serialization is in-memory and deferred through the resource writer. The writer opens with CREATE_ALWAYS after a read-only check. No application backup was found; common-dialog overwrite flags were not recovered conclusively. Any future save test must use a new basename in a disposable copy. User-profile save format is outside this path and UNKNOWN.
