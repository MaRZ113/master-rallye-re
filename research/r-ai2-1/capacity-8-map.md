# Exact index5 /6 /7 static capacity map

Canonical addresses/categories/physical owners are in [JSON](capacity-8-map.json).
Index4 is independently CONFIRMED_BY_RUNTIME by R-AI2. Index5/6/7 remain runtime
UNKNOWN; audited bounds/allocation evidence is CONFIRMED_BY_EXE or CORPUS.

| Subsystem | Physical owner | Index5/6/7 |
|---|---|---|
| Race/CarN, participant identity | scalar wrapper0xCC, decimal key construction4AC590; separate setters | ready; no flat participant4 array |
| Vehicles / actor spawn | Car0..7 boot eggs in all36 scenes;4B6A00 keeps index<NumCars; linked-list eggs | ready for8 authored actors; actual spawn pending |
| Controller/CarN | 44A320 ->44A450/44A510/44ED50 loops current N and uses own ID/family | ready; bounded publication enumeration reaches highest index |
| Physics | 43EF80 constructsN; manager+18/+1C/+20 grows pointer vector via43BB70 | ready; native enumerator/vector and destruction tested |
| Collision | 43A800 grows pointer vector+0C/+10/+14;43AC80 scans actual length | ready storage; four-wheel inner stride188/bound620 is per vehicle |
| Damage | each vehicle receives own DamageParams through family publication44ED50 ->4938C0; independent body/scene ownership | no shared four-car table identified; behavior remains human gate |
| AI | 42A890 allocates0xD4 per PlayerType2; manager+88/+8C/+90 vector;42AC10 alternates halves | ready; seven distinct controller allocations/bindings and dtor traversal |
| Network/offline mirror | 4333D0 writes8 flags, object+60..7C; following+80 is separate | CAPACITY_8; native test preserves+80; no packet claim |
| Grid | 48EB40 generates rows/columns from first StartArea edge and current count | DYNAMIC_N; all36 have data; no terrain-clearance proof |
| Finish | 489AF0 two N*4 arrays;489EC0 normal FinishingType0 loop | ready; FinishingType1's explicitCar0..3 excluded |
| Timing/progress/ranking | 48A880 five N*4;48B520 byte[N]+six N*4;48AE30 rank pairsN*8;48CFE0 split keys | ready; native N6/7/8 init/records/rank publication bounded |
| Reset/recovery | 4CC5F0 fifteen N*4 and4CDF00 seven N*4; cached-N ticks/dtors | ready static ownership; actual reset behavior pending |
| HUD | Hud0/Hud1 ProgressCar0..7;4A74A0 index<NumCars;4AB040/4AB390 scanN | CAPACITY_8 authored markers; three comparison rows are ahead/self/behind |
| Results | result0x1C dynamic vector+2C/+30/+34;47C840 lists actual count, real icons then N..7 blank12 | CAPACITY_8 presentation; eight real backend records have storage |
| Replay | 4CADF0 allocatesN*16+4/cookie;4CB9B0/4CBB50 and4CB150/4CB410 cached-N | ready storage/index7; actual playback and cameras require human |
| Camera | 4B7A70 focus+210 versus human viewport+214, cached count+218;4B8810 enumeratesN | no fixed four-car focus table; human viewport stays0; exotic cameras unproven |
| Cleanup | list/vector-length destruction43E020/42A6B0 and owned count arrays; Replay cookie | ready; exact highest vehicle/AI destruction, redzones preserved |

Existing stock reclamation caveats remain:48ADC0 retains two key arrays and
complete Results-pointee reclamation is unproven. This task does not repair
leaks or claim long-run memory stability. See closed [native storage](../r-ai2/native-storage.md).

Literal classification: frontend3 = stock policy; getter substitution5/6/7 =
research effective AI count; existing N5 = prior runtime target; four wheels,
four intra-egg AI slots and four camera modes are unrelated; N*4 is byte stride;
8 mirror flags/HUD markers/Results rows = authored capacity; driver IDs0..9 =
profile set, separate from participant capacity. No global literal4/8 replacement.
