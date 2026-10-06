# ID26 audio-only policy

## Final Mercedes policy

The Mercedes remains physical Vehicle ID26. In the `gaAiVehicleSound`
constructor only, a bounded wrapper maps the CarID returned by the original
Race broker getter to the configured `stock_audio_profile_id`:

* Canonical: physical 26 -> stock profile ID0 / Landcruiser.
* Diagnostic A/B oracle: physical 26 -> stock profile ID19 / Mattserati.
* Every other CarID: returned unchanged.

ID0 is the **HISTORICAL-COMPATIBLE STOCK TUNED PROFILE**: analyzed demo builds
map Mercedes ID2 through the ordinary `vehicles/rev9` / curve-A route also
used by ID0. It is not claimed to be an authentic unique Mercedes recording.
Human runtime testing found ID0 ordinary/normal on retail Mercedes; ID19 is
clearly bass-heavy and remains an optional stylistic oracle, not the default.

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

The manifest retains the full G.1 profile and G.1 locked/unlocked semantics.
The only new semantic input is `stock_audio_profile_id`, validated against the
hash-pinned tuned retail profile matrix (IDs 0..24). The whole native profile
is selected atomically; sample family and raw tuning fields are not split into
independent settings.

## Future addon field

The reusable semantic definition is `stock_audio_profile_id`, separate from
`physical_vehicle_id`. Retail uses one absolute profile key to choose separate
sample and tuning switch arms; future tooling must preserve the independent
identity field. This phase does not build the generic addon SDK or modify AI
pools.

Runtime evidence: [runtime-results.md](runtime-results.md).
