# Untuned-engine warning path

## Retail control flow

Pristine retail SHA256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

The exact warning string is referenced by `FUN_00408F20` at `0x00408F20`.
Ghidra reports one in-program xref, from this constructor. The constructor is
called once for each active participant by the `Race/NumCars` loop in
`FUN_00408660`.

Within `FUN_00408F20`, the participant slot is retained in the object at
`+0x54`. At `0x00408FB4`, the constructor calls `FUN_004AC660(slot)` and saves
its returned absolute CarID for audio selection. The broker schema registers
`Race/Car` and `/CarID` separately; the getter combines the slot-specific
`Car%d` component with `/CarID`. This value is the audio lookup input; the
object's retained participant slot is not replaced.

The first native switch has explicit tuned vehicle cases for physical IDs
0–24. Those arms choose a stock sample family and case-specific scalar(s).
The default arm constructs the `vehicles/rev9` sample object, then formats the
untuned warning using the original CarID. A later switch selects the vehicle's
curve-table pair and additional tuning value. IDs without an explicit tuned
arm take the default pair/value path.

Thus ID26's present behavior is a functional fallback, not a crash: the code
uses `vehicles/rev9` and default settings, but emits the warning and does not
use a normal tuned profile. The warning is not an asset-loader failure.

## Candidate hook contract

The research candidate redirects only the five-byte getter call at
`0x00408FB4` to a small wrapper. The wrapper:

1. forwards the original slot argument and ECX to `FUN_004AC660`;
2. returns the original CarID for every value except 26;
3. substitutes the selected `stock_audio_profile_id` only for the audio
   constructor's returned selector; and
4. preserves the original four-byte argument cleanup (`RET 4`).

No warning check, warning string, race Broker path, physical registry field,
or VehicleRecord identity is changed. Static control-flow and exact candidate
identity show that the selected tuned switch branch should avoid the untuned
warning arm. The literal warning's absence was not directly recaptured:
Observatory supplied Broker dumps, not DebugView warning logs.
