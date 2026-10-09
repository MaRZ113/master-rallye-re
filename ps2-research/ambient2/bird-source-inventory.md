# Authored source and point contract

All original files are the four canonical inputs listed in `bird-course-inventory.json.canonical_inputs`. This phase freshly verified their sizes and SHA-256, used existing `tngtool` decompression, and independently re-extracted the 36 CDELTA1 course pairs. No original XML is edited or packaged.

Each paired PS2 RaceTest XML declares one `gaAnimals_BirdManager` under an Egg's `AI_List`. Its properties name `Flight MarkerList=FlightList` and `Milling MarkerList=MillList`. Exact names, types, duplicates and source order are retained. The `MarkerLists/List` source is separate from that AI configuration. `Marker No` is metadata; the recovered loader appends in source order rather than sorting by No.

| Representation | Count / meaning |
|---|---|
| Authored managers | 36, one per paired course |
| FlightList records | 542 potential flight spawn origins |
| MillList records | 55 milling-origin candidates in10 courses |
| Missing local MillList declaration | 26 courses; distinct from a present empty list |
| Default pool capacity | 16 entities per initialized manager unless global override |
| Spawn candidates per stock triggered burst | Integer0..9, further limited by free-pool count and gates |
| Allocated / active / submitted / visible live birds | UNKNOWN without a captured owner/frame |

`Rnd Fly` and `Rnd Mil` are10 in all36 configurations. `Bird Brown` occurs twice per manager: True/True in19 courses, False/True in17. Neither duplication is silently collapsed nor False silently normalized. Fresh constructor/clone plus the config **writer** call explain why +94 remains1 in the inspected loading path.

Shared marker loader `1ff7a8` consumes typed `Marker Type`, `Marker Pos`, `Marker Dir`. Each runtime record is80 bytes. Direction produces basis rows at+10/+20/+30; position is+40/+44/+48, homogeneous W at+4c. Flight selection reads position, not marker direction. The prototype's Egg matrix does not become an implicit flight curve.

```text
RaceTest BirdManager typed properties
  --1af0b0 exact typed lookup--> manager+a0/a4 interned list names
  --1fde60/1fdba8--> manager+a8/ac registry pointers
MarkerLists ordered Marker records
  --1ff7a8 80-byte append--> runtime record XYZ+40/+44/+48
  --1b0878/1b0780/1b06d8--> one selected origin
  --1afa20 direct XYZ write--> pending bird carrier translation
```

Every arrow is CONFIRMED_BY_EXE; canonical authored names/records make the selected source association CONFIRMED_BY_BOTH. The diagram does **not** claim that a locally missing registry entry is populated at runtime. That link is explicitly **UNKNOWN LINK: external or retained MarkerList registry content**.

Cached selection examines a local interval around the previous nearest **base index**. This gives list order an operational role but supplies no connectivity, waypoint progression, route endpoint or path looping. Diagnostic maps show disconnected points. Full source coordinates stay in ignored `data/ambient2/`; committed metadata includes counts, bounds, order hashes and named resource hashes only.
