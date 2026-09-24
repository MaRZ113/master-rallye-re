# September → November → final registry evolution

The counts below distinguish **allocated record capacity**, **explicit literal names**, XML physics sections and asset folders. A literal-free record may use an unresolved global string; it is not counted as a confirmed playable car. Directory order was never used as an index.

| Build | EXE SHA-256 | Data.sma SHA-256 | Capacity / stride | Named EXE entries | Physics sections | Asset folders |
|---|---|---|---|---:|---:|---:|
| Sep 8.4.1 | `bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be` | absent in supplied demo tree | 26 × 0x24 | 6 | 19 | 14 |
| Nov 9.3.1 | `931cfc4e0c520c26581b0c1173d1beb586facd17176b885666f455090f646680` | absent in supplied demo tree | 27 × 0x24 | 24 | 25 | 13 |
| Final | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` | `03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f` | 26 × 0x34 | 25 | 34 | 26 |

XML SHA-256 values and all folder/file metadata are in the three JSON inventories.

## September 8.4.1

Named constructor records: **0 Landcruiser, 2 Mercedes, 7 Trooper, 9 Jump, 15 Wildcat, 19 Megane**. The other 20 initialized records point to a global address 0x5F9114 whose runtime string value was not established. `vehicles.xml` has 19 physical sections, so it is not the six-name registry. No `DataGame/Progress.xml` or `Data.sma` is present in the supplied demo directory. The asset tree has 14 folders, including full three-DX Mercedes and Trooper folders with textures. `Copy of Mercedes` is another full three-DX folder; Alpha folders are tracked separately in JSON. These are candidate historical resources, not evidence of final runtime compatibility.

## November 9.3.1

The 27-entry constructor has 24 literal names and unresolved global-name entries at **12, 14 and 23** (0x67F6F8). Named entries absent by exact spelling from final are Mercedes, `Teranno`, Trooper, Pajerostripe and Citroen. `Teranno` appears to become `Terrano` in the final build, but the rename is an inference. Index 17 uses the literal `Forester` again; this is preserved as an observed duplicate rather than corrected to an expected car. The demo has 25 physics sections, 13 asset folders, 12 progress unlock fields and eight scene `Car Name` references, all to Forester. Its Trooper folder contains three DX roles and 25 DXT files. `Rav4` is a folder without those DX roles. No `Data.sma` is present in the supplied demo directory.

## Final transition

Final EXE constructor records are named continuously **0-24**, with class ranges 0-6, 7-13 and 14-24. Capacity contracts from 27 to 26 even though named entries rise from 24 to 25. Stride expands from 0x24 to 0x34. The corresponding singleton allocations match the complete fixed layouts: September 0x6C4, November 0xA84, final 0xC00. Thus the historical change was a compiled structure revision; copying a numeric bound from a demo is unsafe.

Final adds named Navara, Patrol, Kiasportage, Astero, SeatBuggy and Ufo relative to November, while Mercedes, Trooper, Pajerostripe and Citroen lose named entries. The final XML retains those four physics sections; it also retains other unused physical profiles. Folder inventory and literal names evolve independently.

No demo assets or binaries are included in this repository. A later historical payload could use September Mercedes or Trooper, but a duplicated final stock vehicle is the cleaner first slot test.

## Verified ID changes for names present in multiple builds

| Internal name | September | November | Final |
|---|---:|---:|---:|
| bruno | — | 22 | 20 |
| chevyblazer | — | 4 | 4 |
| forester | — | 8, 17 | 8 |
| frontera | — | 6 | 6 |
| icecream | — | 25 | 23 |
| jump | 9 | 7 | 9 |
| kamaz | — | 24 | 22 |
| kangoo | — | 18 | 17 |
| landcruiser | 0 | 0 | 0 |
| mattserati | — | 20 | 19 |
| megane | 19 | 19 | 18 |
| mercedes | 2 | 2 | — |
| newrav | — | 13 | 12 |
| pajero | — | 1 | 1 |
| rmonster | — | 11 | 10 |
| simmbugghini | — | 16 | 15 |
| tata | — | 10 | 2 |
| trooper | 7 | 9 | — |
| wildcat | 15 | 15 | 14 |
| xtrail | — | 5 | 5 |

These ID changes are a direct compatibility risk for any save or event that persists a numeric car ID across builds. November Forester appears at both 8 and 17 in the constructor. Spelling-only differences (Teranno/Terrano) are kept separate.

## Frontend/progress differences

September has no `DataGame/Progress.xml` in the supplied tree and no matching saved frontend car field. November has `Frontend/QuickRace/Car0=7` and 12 unlock fields. Final has saved `Frontend/QuickRace/Car0`, `Car1`, and `Frontend/Network/Car0`, defaulting to 0, and 17 unlock/cheat fields. See JSON for exact `SavePlayerState` attributes.
