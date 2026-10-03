# Decision gate and non-blocking boundaries

| Item | Classification | Why / action |
|---|---|---|
| Slot0/1 binding and lack of promotion | CLOSED_STATICALLY | Complete loader -> compiled vector -> pass map -> SetTexture proof |
| Byte2 diffuse and byte3 source UV consumers | CLOSED_STATICALLY | Descriptor/FVF/vertex-copy chain; no new runtime candidate needed |
| All stock vehicle masks/families | CLOSED_STATICALLY | 1478 classified draws, no UNKNOWN fallthrough |
| Opaque/alpha separation and composite depth key | CLOSED_STATICALLY | Queue records, key assembly and flush comparison recovered |
| Stock decal/glow family choice | CLOSED_STATICALLY | Selector has no names; all named stock examples classify base/env or their normal alpha variants |
| Pixel output of the three NULL-base helper records on original D3D8 drivers | UNKNOWN_BUT_NON_BLOCKING | Binding exact; documented fixed-function cascade applied as HIGH_CONFIDENCE_INFERENCE, no authorial-intent or human pixel claim |
| Inherited alpha-test state for shaders that do not reset it | UNKNOWN_BUT_NON_BLOCKING | Explicit setup writes distinguished from full device state; no complete scene-state snapshot claim |
| All scene callers configuring queue grouping/stable full-key ties | UNKNOWN_BUT_NON_BLOCKING | Relevant queue/key proven; scene reconstruction unnecessary for honest preview |
| Damage RemoveEnvMap / EnvMapFadeStrength mutation path | OUT_OF_SCOPE / OUTSIDE STATIC MATERIAL PREVIEW | Shallow configuration ownership trace ends at renderer+8C; further work would be damage-system research |
| Optional material variant object (raw unknown_0x18), other control words/scalar | UNKNOWN_BUT_NON_BLOCKING | None used by stock ordinary branch; raw values retained, optional variant produces explicit UNKNOWN |
| Slot2 / mask08+ / particles / water / courses | OUT_OF_SCOPE | No stock vehicle draw uses them; no engine-wide generalization |
| Exact Blender/Direct3D8 pixels, depth overrides and runtime queue | OUT_OF_SCOPE | Approximation explicitly marked, no node graph can encode the whole scene queue |

NEEDS_RUNTIME items required to close this phase: **none**. No binary/multi-way
ambiguity remains in a stock vehicle-used material family; remaining pixel
validation and damage behavior lie within the documented preview boundary.
No EXE patch or runtime candidate was created, and no human runtime result
was invented. Existing R4D.1/R4E/R4E.1 labels are retained with their scope.

Final verdict: **CLOSED WITH NON-BLOCKING UNKNOWNS** for the vehicle runtime
model; **APPROXIMATE WITH DOCUMENTED LIMITATIONS** for Blender preview. STOP.
