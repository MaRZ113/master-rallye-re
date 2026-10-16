# Vehicle continuity2: runtime A/B and next CAR control

## Release and confirmed boundary

Main final DLL includes X-Trail atomic damage re-certification, frontend tread U-wrap,
WOOLDAND/UFO COMPLETE modes5/21, cover and reflective front-lamp deformation support,
and an opt-in read-only full-fleet source/owner probe. No generic fleet CAR rendering
is enabled yet. Existing working X-Trail CAR/crew/wheels and20 exact glow profiles remain.

User-confirmed earlier candidates:684045fe... eliminates impact flicker and fixes COMPLETE
tread;6e1e31e0... replaces WOOLDAND/UFO and retains transparent damaged front covers.
User also confirms rear lamps reflect. New roots5/11 reflection continuity requires final
DLL gameplay validation; native replay alone does not establish visual acceptance.

## Manual installation

Install final d3d8.dll manually. Preserve the current configuration and accepted assets.
The two new assets under assets/ belong in FrontendModelAssetDirectory (normally PS2Vehicles):
WOOLDAND-COMPLETE-CONTINUITY2-V1.ps2model and UFO-COMPLETE-CONTINUITY2-V1.ps2model.
If already installed for6e1e31, do not replace them; their bytes are unchanged.
Keep FrontendModelMode=2, RacePS2ModelMode=1, ReflectionMode=4 and existing crew/wheel/glow
opt-ins. All feature/diagnostic defaults remain Stock/OFF. Native physics is untouched.

## X-Trail final lamp check

Fresh race: compare front lamps healthy, after an impact and after another impact from
the same camera. Expect covers to remain transparent AND underlying reflective PS2 roots5/11
to retain reflections while following native deformation. Number decal/body/wheels/crew
must remain coherent. Inspect rear brake released/held/released separately; do not confuse
OFF base reflection with bright ON core or additive glow. Check MSAA4x and window Reset.
RacePS2DamageCapture=1 optionally records three F10 frames, including conditional10v/6f OFF
candidates, under the existing bounded damage probe. Diagnostics remain OFF by default.

## Next fleet CAR control: one KiaSportage session

Set RacePS2FleetCapture=1, keep RacePS2ModelMode=1 and enter an original KiaSportage race.
This setting DOES NOT replace Kia: it only records current original PC owner/buffers.
F10 at start with brake released; drive/steer briefly and F10 again; hold brake and F10.
Exit normally. Collect race-fleet-PID-dDEVICE-fFRAME.jsonl and the session.
The observer is bounded to32 F10 activations/process, first active frame each,
64 unique actual CAR/WHEEL submissions/frame and128KiB/file. No raw textures or raw
geometry, no GPU readback, no controller polling, no work on normal non-F10 draws.
It joins current native queue→instance→selected original/private tree→actual VB/IB ranges,
full original geometry digest and WORLD. Tree walk is capped64 nodes; source tags/draw
ordinals never authorize replacement. CAR matches cover25 original paired families;
wheel matches cover24 source-backed wheel resources. Ambiguous shared wheel hashes remain
multiple metadata candidates. rendering_authorized=false is mandatory in every record.

A subsequent batch can record one healthy race F10 per other family without restarting,
within the32 activation limit. Unknown/modified/deformed source records are omitted,
not accepted through a relaxed hash. Captured pointers are same-session evidence only.

## Regression indicators

Duplicate people/body, rigid/floating wheels, disappearing body, loss of lamps after impact,
non-restored menu/race state or Reset failure are regressions. Report model, frame, config
and DLL hash. Source-ready25 CAR conversions are NOT installed or silently enabled.
