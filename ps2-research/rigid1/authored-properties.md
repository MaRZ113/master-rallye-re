# Authored parameters and actual consumers

`19fe98` invokes existing typed property helpers. The diagnostic follows the first matching correctly typed value and preserves original spellings, duplicates and unknown properties. Its malformed-input rejection is diagnostic policy; it is not a claim that retail code validates every value equally.

| Property | Owner field | Constructor default | Reader | Proved runtime effect |
|---|---|---|---|---|
| Mass | +14 | 500 | 1e2510 | init writes body+20=m, body+24=1/m |
| MOI Vector3 | +1c..+24 | 100,100,100 | 1e2a48 | diagonal local inertia +28..+48; inverse via 203358 |
| Trigger Distance | +18 | 5 | 1e2510 | parsed/stored; **not read in 1a0258** |
| Casts Shadow | +10 | false | 1e2470 | parsed/stored; selected init/update contain no consumer |

`mass_inertia` covers original 1a0058..1a00df operations. No density, model-volume conversion or XML override is present in that init segment. `MOI` is direct local-axis inertia, not inverse inertia: the inverse is produced separately. State restoration computes world inverse inertia `R * IbodyInv * transpose(R)`; angular setter computes `L = R * Ibody * transpose(R) * omega`.

No original positivity clamp was found before these inversions. The source inventory retains finite unusual values. The evaluator refuses nonpositive mass/inertia for its bounded inverse calculation rather than inventing an engine fallback. The diagnostic reciprocal of diagonal entries is `MATHEMATICALLY_EQUIVALENT`, not proof of bit-exact generic 203358 inversion.

`Trigger Distance` and `Casts Shadow` retain **UNKNOWN** consumers outside the traced schema/init/update. Do not label them globally unused, collision radii, proven shadow toggles or physics wake thresholds.
