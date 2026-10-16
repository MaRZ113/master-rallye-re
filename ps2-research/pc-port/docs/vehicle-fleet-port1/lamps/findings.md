# FLEET-PORT1: bounded original brake-glow identity extension

## Result and boundary

Twenty legacy profiles are retained byte-for-byte. Five previously excluded
families have independently identifiable native glow records and original PS2
mode14 counterparts. A 25-profile draft is ready for main-agent integration.
No renderer, baseline, integration patch or build tree was changed by this
subtask. Original executable analysis was not repeated: existing byte-verified
mode14 and native brake-selector evidence answers the material question.

This extends the accepted **original PC emitted glow geometry + original PS2
RGB-fade texture/state** approach. It does not replace glow geometry with PS2
geometry. The five shapes differ between releases; those differences are
reported rather than hidden inside a looser geometry tolerance.

| family | original PC record | PS2 conditional path | faces | maximum original XYZ difference | UV triangle multiset |
|---|---:|---|---:|---:|---|
| Frontera |32|root.23.0.1|16|0.039209842681884766|byte exact|
| Jump |28|root.21.0.0|16|0.0024013519287109375|byte exact|
| Mattserati |24|root.21.0.1|48|0.00802314281463623|byte exact|
| RMonster |24|root.18.1.1|24|0.020730972290039062|byte exact|
| Tata |32|root.24.1.1|28|0.04579043388366699|byte exact|

These are compiled-resource record indices, never live draw ordinals. Each
source record owns the original `breaklightsonglow-tga` primary. Frontera,
Jump and Mattserati additionally author perspex in slot1; mode14 does not
activate that secondary reflection pass. Ordered slots remain recorded.

`audit_missing.py` rereads canonical PackFS payloads, verifies each PS2 CAR SHA
against the previous source inventory and each protected PC CAR SHA against
the established fleet corpus, then computes original triangle positions and
UVs. A whole triangle UV multiset is byte-exact in each unique glow candidate,
not merely a matching texture name or a UV bounding box. Mode1 ON geometry is
separate, with a different primary and source identity. Unrelated same-face-count
draws are retained as comparison negatives, never admitted.

`generate_registry.py` emits exact **native PC** geometry and position+UV corner
SHA profiles. Runtime matching uses no position tolerance and never compares
a deformed upload to a nearby PS2 shape. Unknown or changed geometry remains
Stock. The authored source comparison establishes revision correspondence,
not PS2/PC position equality.

## Existing contract preserved

The original PC `gaSFXBrakeLights` selects the named blight branch through its
existing controller update; this pass adds no key polling, per-frame Broker
reads or branch writes. OFF lamp/base, selected ON lamp and additive glow remain
independent sources. Only the selected native glow draw gets the established
transaction. OFF and ON sources must not satisfy the glow identity.

Original mode14 is additive Cs+Cd, textured/fog-off, alpha-test-off and masked
depth writes. Use the original PS2 16x16 RGB-fade GXI
`b6350f92f674bf2b63200ce4bb39c0c26f03fd99856ac0b89e7fc0797861af09`,
ONE/ONE and no body environment layer. Its alpha is zero; source-alpha blending
would erase it. The original PC texture instead carries fade in alpha and
must not be retained under ONE/ONE. Original PC depth convention stays intact.
No MSAA toggling, source-alpha recoloring or global lighting change is needed.

The similarly named unregistered `carbrakelight` shader is not carshiny.
`vehicle-continuity2/frontend/findings.md` proves generic two-slot material
fallback before explicit texture-name mode14 override. It must not cause a
whole rear light to be marked reflective or emissive.

## Focused validation and runtime limits

Four focused inventory tests pass: five unique original sources; no ON source
admission; byte-identical legacy20; explicit native-shape limitations.
`prepare_native_fixtures.py` creates only an ignored local fixture from all774
physical CAR records in25 protected PC families:25 glow positives and749
body/OFF/ON/other negatives. It uses the existing PS2LMP01 format, kind2 positive,
kind3 negative. This enables main-agent native hash tests across the entire
corpus. It is not evidence of25 live brake transitions.

The five most recent session files were searched read-only for exact
`ps2_brake_glow` events. Four contain none; session52340 contains one UNKNOWN
rejection. Several sessions reach the established16MiB cap, so absent events
cannot establish absence of rendering or a successful OFF/ON transition.
Prior Terrano session30176 remains the explicit measured successful glow
transaction; user X-Trail observations remain separate runtime evidence.
Do not promote source eligibility or fixture success into fleet runtime PASS.

## Integration notes and bounded A/B

Main agent copies the draft registry, updates diagnostic profile bounds from
20 to array-size25, and uses array-size as the UNKNOWN diagnostic slot. The
current uint64 bitmap supports25 profiles plus UNKNOWN (52bits). Keep the
old20 generator as historical evidence and add a new25-registry check rather
than weakening its expected count. No new material mode or private asset is
required if the accepted PS2BrakeGlow.gxi is installed.

For each newly enabled family: same race/camera, released brake -> held brake
-> released; F10 at each state. Confirm OFF lamp reflection is independent,
ON core appears only on the native branch, glow fades smoothly to black and
does not reflect surroundings, then release restores OFF. Inspect a window
Reset and MSAA4x. Record current family/source hash and draw/restore HRESULTs;
never identify the material by those F10 draw sequence numbers alone. Native
damage changing the source hash must explicitly fall back, not match fuzzily.
