# G2 ConfigVersion 3

ConfigVersion 2 remains the default runtime configuration format for existing profiles and keeps its existing numeric policy mapping. ConfigVersion 3 retains those Randomizer, Opponents, Addons, and Logging fields and adds `[Player]` for Quick Race player 0 only.

```ini
[General]
ConfigVersion = 3

[Randomizer]
QuickRace = 4
RallyeCup = 0
MasterRallye = 0
Invitation = 0
Challenge = 0
Duplicates = 1

[Opponents]
MaxOpponents = 3

[Addons]
Include = 0

[Logging]
Enabled = 1

[Player]
; 0 = Stock, 1 = Forced, 2 = Random
Mode = 0
; Stock physical CarID, required even when not used
ForcedCarID = 0
; 0 = Stock, 1 = T1, 2 = T2, 3 = T3, 4 = Full, 5 = Mixed, 6 = Diverse
RandomPolicy = 4
```

The parser remains strict ASCII and bounded to 4096 bytes. For V3, all three Player keys are required. Mode must be 0–2, `ForcedCarID` must be a stock physical ID 0–24, and `RandomPolicy` must be 0–6. Invalid or incomplete configuration is rejected as a whole; the runtime retains its last accepted snapshot during hot reload.

| Numeric field | ConfigVersion 2/3 meaning |
|---|---|
| `QuickRace` and other mode policies | 0 Stock, 1 T1, 2 T2, 3 T3, 4 Full, 5 Mixed, 6 Diverse |
| `Player.Mode` | 0 Stock, 1 Forced, 2 Random |
| `Player.RandomPolicy` | Same policy mapping as ConfigVersion 2 |

`RandomPolicy=Stock` leaves the player selection native even when `Player.Mode=Random`. Forced or random selection uses verified stock IDs only; it does not discover addon directories or depend on the Vehicle SDK. Player selection does not change AI policy, player controller/PlayerType, native DriverID policy, or participant construction.

The package's `profiles/` directory supplies safe stock, forced-ID12, random-T1, random-T2, random-Full, and optional G1 seven-AI regression profiles. These are examples for the experimental candidate, not separate product modes.
