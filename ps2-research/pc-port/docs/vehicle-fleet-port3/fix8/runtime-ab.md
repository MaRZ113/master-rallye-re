# PORT3 fix8 runtime check

1. Replace `d3d8.dll`; copy the four `PS2Vehicles/*-CREWFACE1|WINDOW1.ps2model` files beside the
   existing assets. Replace `PS2Port.ini` by `PS2Port.ini.migrated-pristine` (rename), or keep the old
   INI (still accepted) and add `PS2ContentFixes=1`.
2. Navara race: co-driver face textured. Tata race: right window intact at the start; Kamaz race and
   Kamaz in the menu: right window intact. Session log: `ps2_content_fix` … `loaded`.
3. UFO race, brake released: F10 → `fleet_private_off_submission` (fix7).
4. Control: `PS2ContentFixes=0` → original PS2 content again.
