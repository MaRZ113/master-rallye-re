# Progress Broker state and persistence

Retail `DataGame/Progress.xml` defines these relevant groups:

| Broker group | Count | Type/default | SavePlayerState | Role |
|---|---:|---|---|---|
| `Progress/UnlockedCars/*` | 16 | Bool / False | True | Named per-vehicle reward predicates |
| `Progress/OpenedModes/*` | 6 | Bool / False | True | Cup/Master/Invitation reachability |
| `Progress/Cheats/*` | 7 | Bool / False | False | Runtime unlock bypasses and developer flags |
| `Progress/WinStatus/*` | 109 | Int / 0 | True | Event/cup result and completion history |

Each unlock field is a separately named Broker value, not evidence of a
CarID-indexed bit array. The capture checker reads those exact path names and
returns UNKNOWN for missing or ambiguous values.

`Progress.xml`'s `SavePlayerState=True` means these values are eligible for the
PlayerState persistence path. Existing research also finds player vehicle
selection fields in `frontend.xml`, `RallyeCup.xml`, and `MasterRallye.xml` with
SavePlayerState metadata. Neither that metadata nor an Observatory dump proves
the binary serialization format, save-file ownership, or when a write is
flushed. The actual PlayerState save file is local game state and is not
included or modified in this repository.

An F.2e Observatory snapshot (`retail-merc-id26-menu`, image hash
`1fb0a1f1ba02cd05fa25f0c94558cf1b281fd12affcdc37bb3c1ca538e6c65af`) contains
all the listed unlock flags as false, class text T1, and `CarModel=26`. That
capture used an F.2e test-unlock executable and is a schema example, not proof
that its profile was fresh or that ID26 obeyed progression.
