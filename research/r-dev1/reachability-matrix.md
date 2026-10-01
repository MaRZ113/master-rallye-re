# Reachability and write-safety matrix

| Feature | Code | ID/command | Main-menu item | Ordinary retail route | Write risk |
|---|---|---|---|---|---|
| Main Game menu | confirmed | Reset 0x32 / Exit 0x2F | yes | built; runtime not separately captured | reset changes runtime state |
| Debug window | confirmed | startup capability | no | prior combined-flags observation only | no game-data writer identified |
| Broker Editor | confirmed | 0x27 | no | not confirmed | live broker mutation; save is separate |
| Egg/Particle/Marker | confirmed | 0x2E/0x4A/0x3B | no | not confirmed | unknown |
| Generic tree/object editor | confirmed | 0x3F/index family | no | not confirmed | unknown |
| Flow Builder | confirmed | 0x30 | no | not confirmed | build/converter may overwrite |
| BuildData | confirmed | 0x58 → vtable +4 | no | not confirmed | high; recursive scan and DX/DXT CREATE_ALWAYS |
| Game/Scene XML Save | confirmed | 0x33–0x37, 0x51–0x54 | no | not confirmed | CREATE_ALWAYS after writable check |
| FL-to-SFL | confirmed | local ID 10 in Flow Builder | internal only | parent window route not confirmed | sibling .sfl CREATE_ALWAYS |

“No” means no item in the specific retail menu builder 005B1320; another sender is not excluded. No WM_COMMAND injection or hidden-ID runtime experiment was performed.
