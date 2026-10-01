# Sparse T1 class mapping

Existing retail absolute IDs remain fixed:

| Class | Existing local → absolute IDs | Candidate capacity |
|---|---|---:|
| T1 / class0 | local0–6 → ID0–6; local7 → ID26 | 8 |
| T2 / class1 | local0–6 → ID7–13 | 7 |
| T3 / class2 | local0–11 → ID14–25 | 12 |

The mapping is sparse. T1 local7 does not renumber T2 or T3, and ID26 does not
become T3 local12.

## Forward mapping: UI state → absolute ID

Retail helper `0x481E20` reads class from UI state `+0x10` and class-local
indices from `+0x14/+0x18/+0x1C`. Its original branches return T1 local directly,
T2 local plus 7, or T3 local plus 14. The candidate redirects only:

```text
class == 0 && T1 local == 7  ->  EAX = 26
```

For every other input it replays the overwritten `MOV EAX,[ECX+0x10]` and
`SUB EAX,0` instructions, then continues at the original function branch.

## Reverse mapping: absolute ID → UI state

Retail helper `0x481E50` receives the absolute ID on the stack, stores class and
local index into the UI state, then joins the common update at `0x481E89`.
The candidate adds:

```text
ID == 26  ->  class = 0; T1 local = 7; join common update
```

All other values replay the original first two instructions and resume at
`0x481E55`, preserving existing threshold behavior.

## Capacity and navigation

The frontend UI object has three class capacity fields at `+0x20/+0x24/+0x28`.
The constructor's first count is 7; candidate changes that T1 value to 8.
The T2 count remains 7. T3 remains 12 from the already confirmed E0.2 profile.
Retail's `0x481950` updater iterates 12 position properties, and
`Button7XPos` is present. The new scene widget uses that existing key.

Navigation still uses the class-local state. The forward and reverse hooks make
the eighth T1 entry round-trip to physical ID26 while leaving all prior class
maps untouched. The test should repeatedly cross local6/local7 and switch
classes during P0.
