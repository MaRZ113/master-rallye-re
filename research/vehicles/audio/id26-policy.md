# ID26 audio-only policy

## Chosen policy

The Mercedes remains physical Vehicle ID26. In the `gaAiVehicleSound`
constructor only, a bounded wrapper maps the CarID returned by the original
Race broker getter to one configured stock donor selector:

* Candidate A: 26 -> ID0 Landcruiser profile.
* Candidate B: 26 -> ID19 Mattserati profile.
* Every other CarID: returned unchanged.

The original slot argument and original getter are preserved. The wrapper
uses the existing `RET 4` cleanup convention. The hook is at
`0x00408FB4`; helper code is appended after the verified G.1 payload at
`0x0068E679`. The `.text` extension remains inside its existing raw section
and ends before `.rdata`.

## Preserved channels

The hook does not edit the G.1 registry initializer or any display/vehicle
setup/unlock path. The runtime test must still observe:

* `Race/Car0/CarID = 26`;
* `Race/Car0/CarClass = 0`;
* `Race/Car0/CarType = "Mercedes"`;
* `Race/Car0/WheelType = "Mercedes"`;
* Mercedes model, wheels, physics and frontend identity unchanged.

The static manifest retains the full G.1 profile and G.1 locked/unlocked
semantics. The only new semantic input is the audio-profile donor selector.

## Future addon field

The smallest reusable definition is a configurable `audio_profile_id` (or
stock donor identity) separate from `physical_vehicle_id`. The current retail
engine uses one absolute ID as an implicit key into separate sample and tuning
switches, so a future tool will need to preserve that distinction explicitly.
This phase does not build the generic addon SDK or modify AI pools.
