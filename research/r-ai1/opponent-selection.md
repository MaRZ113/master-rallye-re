# Quick Race opponent selection

**CONFIRMED_BY_EXE** for the ordinary offline mode2 path.

`0x47B780` restores the player absolute ID and derives class. It separately
copies track, mode, ghost and opponent settings from Frontend/QuickRace.
NumCars is written as `NumOpponents+1` through `0x4AC3D0`. Practice mode1 skips
AI generation. The one-human call to `0x458090` passes:

```
firstAI = 1
count = configured opponent count (3 in this proof)
requestedClass = Race/Car0/CarClass
excludedID0 = Race/Car0/CarID
excludedID1 = -1
```

The other call in the same owner is for two human participants; it starts AI
at2 and excludes both human IDs. No direct caller outside `0x47B780` was found.
The singleton helper `0x458950` is not itself an opponent chooser.

## Vehicle pool and independent driver pool

`0x458090` chooses **absolute IDs**, without calling `0x481E20`:

| Requested native class | Ordinary absolute pool | Optional bonus IDs |
|---|---|---|
| 0 (T1) | 0..6 | None in this branch |
| 1 (T2) | 7..13 | None in this branch |
| 2 (T3) | 14..20 | Unlock-gated 22,23,24,21, in that append order |

The switch also aliases selector4 to the T3 branch; this does not establish a
fourth stock vehicle class. Human absolute IDs are excluded from the ordinary
pool. Driver profiles0..9 form a separate shuffled pool. Vehicle and driver
bookkeeping occurs before publication.

At `0x4583EB..0x458424`, the chosen ID is stored in [ESP+0x14], consumed from
the shuffled remaining pool and recorded in the used pool. `0x458980` supplies
the chosen DriverID into [ESP+0x18]. Publication then uses:

- `0x458435`: Race/CarN/CarID = selected absolute ID;
- `0x45843A..0x458456`: registry class for that **same ID** -> CarClass;
- `0x458468`: independent selected DriverID -> DriverID.

CarClass is consequently not a blindly copied numeric field in each AI row:
the class restriction happens upstream in the requested pool. The final class
setter derives from CarID. The intervention after bookkeeping preserves both
the stock driver's choice and the remaining two vehicle choices/RNG sequence.

A fresh stock profile excludes optional bonus vehicles from the controlled
human proof. AI2/AI3 stay distinct stock T1 IDs1..6, while the fresh-profile player is0.
The T1 AI pool is not restricted to the three frontend-visible initial cars.
No participant count, loop bound or allocation changes are involved.
