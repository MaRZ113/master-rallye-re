# HUD-PORT2 roadmap — deferred, no implementation

Priority after reflection/vegetation A/B acceptance: presentation with original
PC semantic feeds and the once-per-D3D-frame HUD cache. Physics is paused.

| Feature | Existing evidence | Required next gate | Small implementation boundary |
|---|---|---|---|
| SpeedDial plate | Original class/vtable, key-map/subimage/XY/UV and stage0 argument contract; PS2 plate assets | Current key0 plate joined to native texture generation, player/race/UI lifetime and Reset retirement | Replace plate only; preserve original needle, speed, gear and logical layout. Unknown key is never treated as index0. |
| Orange damage state | PS2 damage bank/controller exists; source images alone do not prove a threshold or current tint | Identify original damage-channel/state-to-color selection and its PC semantic owner | Restyle only confirmed channel packets; do not infer numeric damage from screenshots or replace unrelated status icons. |
| Independent rising/fading damage notification | Requested visual feature; relationship to current icons is not established | Find original PS2 event owner, message/sprite selection, timer, rise/fade equations and PC event feed | Separate event lifetime, presentation and fade; no synthetic damage, polling each UI draw or assumption that an orange icon is the notification. |
| Procedural RaceLine minimap | PS2 model-Null gaHudAiMap uses RaceLine segments, heading/participant inputs and clipping; PC GPS is a different widget | Current route/player/heading mapping and scoped native UI replacement identity, plus source clipping/scale equations | Source-derived route geometry with a cached once-per-frame semantic snapshot. Preserve split/progress/gameplay logic; never use a minimap background texture as a substitute route. |

Start with the SpeedDial one-shot recipe in `hud-port1.1/runtime-recipe.md`.
Do not enable a broad HUD replacement until each widget owns a distinct current
packet/resource contract. Compose with Free Camera, Clean View, HUD hiding and
PreserveMargins; preserve strict admission each draw while reusing the existing
frame cache. No new per-frame resource scans, Broker-per-draw reads, source
texture edits or HUD implementation belong to Visual Parity Expansion.
