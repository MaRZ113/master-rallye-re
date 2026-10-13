# Full vehicle source coverage

29 canonical PS2 CAR.PSM models;26 PC families;78 retailDX files.174 verified reflective source material groups across24 PC families, including99 paint records. This is source compatibility, not a new-car runtime confirmation.

| PS2 family | PC family | Verified carshiny groups | Paint groups | Qualification |
|---|---|---:|---:|---|
|ASTERO|Astero|8|4|Current owner/generation/native-state gates required|
|BRUNO|Bruno|3|1|Current owner/generation/native-state gates required|
|CHEVYBLAZER|ChevyBlazer|7|5|Current owner/generation/native-state gates required|
|FORESTER|Forester|0|0||
|FORKLIFT|forklift|0|0||
|FRONTERA|Frontera|8|4|Current owner/generation/native-state gates required|
|ICECREAM|IceCream|8|4|Current owner/generation/native-state gates required|
|JUMP|Jump|3|0|Current owner/generation/native-state gates required|
|KAMAZ|Kamaz|9|6|Current owner/generation/native-state gates required|
|KANGOO|Kangoo|8|3|Current owner/generation/native-state gates required|
|KIASPORTAGE|KiaSportage|7|4|Current owner/generation/native-state gates required|
|LANDCRUISER|LandCruiser|4|1|Current owner/generation/native-state gates required|
|MATTSERATI|Mattserati|7|3|Current owner/generation/native-state gates required|
|MEGANE|megane|10|9|Current owner/generation/native-state gates required|
|MOONBUGGY|No exact counterpart|0|0|NO_EXACT_PC_FAMILY_NAME|
|NAVARA|Navara|6|5|Current owner/generation/native-state gates required|
|NEWRAV|NewRav|7|5|Current owner/generation/native-state gates required|
|PAJERO|Pajero|7|4|Current owner/generation/native-state gates required|
|PATROL|Patrol|10|7|Current owner/generation/native-state gates required|
|RMONSTER|RMonster|10|8|Current owner/generation/native-state gates required|
|SEATBUGGY|SeatBuggy|7|5|Current owner/generation/native-state gates required|
|SIMMBUGGHINI|Simmbugghini|7|2|Current owner/generation/native-state gates required|
|TANK|No exact counterpart|0|0|NO_EXACT_PC_FAMILY_NAME|
|TATA|Tata|13|8|Current owner/generation/native-state gates required|
|TERRANO|Terrano|11|5|Current owner/generation/native-state gates required|
|UFO|Ufo|2|1|Current owner/generation/native-state gates required|
|WILDCAT|WildCat|5|2|Current owner/generation/native-state gates required|
|WOOLDAND|No exact counterpart|0|0|NO_EXACT_PC_FAMILY_NAME|
|XTRAIL|Xtrail|7|3|Current owner/generation/native-state gates required|

## Matching contract

Every PC face must match an unconditional root PS2 carshiny material mesh at .001 source units, with matching original texture slots used only as a prefilter. PC flags00000101; rubber/carflat/carglass/carglow excluded. All174 use proved carshiny mode3 and CommonTextures/rendertarget64x64. The75 non-paint groups include actual body regions, trim, decals and wheel-associated geometry. Native opaque-body admission is still mandatory.

Original float32 unsigned geometry digests preserve repeated faces. All174 hashes are unique to their vehicle family across78 DX files. Model/menu/complete repeats within one family are source repeats, not extra vehicles. Native body owner, live race, resource generations/revisions, texture generations and original two-stage environment states remain necessary.

## Exact blockers

Forester: only13/400 side,28/71 rear and8/54 light PC faces match the candidate PS2 sources. No full exact join; excluded. Forklift: authored body/metal1 materials lack proved carshiny interpretation; excluded. PS2 MoonBuggy/Tank/Wooldand have no exact PC counterpart; no guessed aliases.

Tata/Kia user runtime evidence is preserved. All newly registered families require user game A/B. No complete meshes, raw textures, or live visibility claims are included.
