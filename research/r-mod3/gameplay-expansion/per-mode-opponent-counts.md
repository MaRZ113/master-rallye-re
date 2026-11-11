# Opponent counts by game mode

Quick Race is not a generic count owner. The game has separate event builders,
roster lifetimes, persistence, UI and scoring paths. The table distinguishes
engine participant capacity from an event mode's qualified count.

| Mode | Exact native generation owner | Minimum feasible / current native count | Maximum structurally supported | Maximum practical evidence and blockers |
|---|---|---|---|---|
| Quick Race, Type 2 | `0x0047B780` -> `0x00458090` | One AI is the smallest exposed opponent choice; the prior native baseline selected up to three, and the current extender exposes one through seven. | Eight total CarN slots (one human + at most seven AI) in the normal one-human path. | The released feature has worked at multiple counts, including seven in some policies/configurations. Seven-AI strict T1/T2 with a same-class player is reported unstable; cause unknown. Cross-course clearance is not established. Fully qualified global max: **unknown**. |
| Rallye Cup, Type 6 | New event: `0x0045BE10` -> `0x0045ABC0(first=1,count=3,class)`. | Current native path creates three AI; no lower configurable count has been established. | Shared race ceiling is eight total, but Cup-specific max is **unknown** until arrays/scoring/results are audited. | Three AI is the runtime-confirmed native baseline with stage reuse. Higher/lower counts are not qualified. Must check `RaceData/CompetitorN`, event points, standings, results and three-stage persistence; only a new Cup may adopt a new count. |
| Invitation, Type 8 | Frontend selects special cup class 5; shared `0x0045BE10` -> `0x0045ABC0`. | Current native path creates three AI; no lower configurable count has been established. | Shared race ceiling is eight total; Invitation-specific max is **unknown**. | Three AI is the runtime-confirmed baseline. Ordinary pool is T3 IDs 14..20 and special-event eligibility is distinct. Check three-race progression and retained roster; don't infer a count limit from the shared Cup builder. |
| Master Rallye, Type 5 | New competition: `0x00452590` -> `0x00451DD0(first=1,count=3,class)`. | Current native path creates three AI; no lower configurable count has been established. | Shared race ceiling is eight total; serialized competition max is **unknown**. | Three AI is runtime-confirmed, including fresh-process save/Resume persistence. Must audit all `CompetitorN`, `MasterRallye/CarN`, points/standings and save readers/writers. Only new competitions may use a new count. |
| Challenge, Type 7 | `0x0045EA60` screen lifecycle -> `0x0044FEC0(event)`; fixed event identity is consumed at `0x0045010E`. | One authored AI + one human is the only established count. | Engine slot ceiling is eight total, but Challenge authored maximum is **unknown**; no multi-opponent contract is established. | One opponent is the tested event model. Need event-by-event preview, objective, success, retry, result and authored human/opponent checks before increasing count. |

## Evidence and structural limits

`research/r-ai1-2/mode-map.json` and its companion owner/lifecycle notes are
`CONFIRMED_BY_EXE` for the exact pristine retail image. R-AI1.2's current
randomizer work changed vehicle class/identity selection, not event counts.
Cup and Invitation generate once and reuse the same competitor identities
over their three-stage event. Master Rallye generates only at new-competition
creation; stage advance and fresh-process Resume load the saved roster. These
lifetimes are `CONFIRMED_BY_RUNTIME` for the prior qualified candidate.

The shared race engine has Car0..Car7 actor, physics, AI, progress, HUD,
Results, and replay paths, with 6..8-participant Quick Race runtime evidence
on a separate fixed-roster candidate. This does not establish that Cup points,
Invitation rules, Challenge conditions, split-screen arrays, save serialization,
or each course supports those counts.

For Cup/Master/Invitation, the current builder arguments express the standard
AI range; the calling mode chooses it. Their current value of three is not
evidence that three is the only structurally possible count. The eight-slot
race engine is an upper structural bound only, not proof that any campaign
array can hold seven AI. Conversely, changing only the builder count is
insufficient: enumerate event standings, save, UI, Results and stage readers
before selecting a supported count. Thus the mode-specific practical maximum
for any new count remains unknown; only the current native baselines are
runtime-qualified in these persistent modes.

## Per-mode implementation boundary

- **Quick Race:** count already flows through frontend and native setup. Keep
  the existing one-to-seven count feature independent from Randomizer policy.
  For seven AI, qualify repeated IDs and start-grid safety separately.
- **Rallye Cup:** change only the new-Cup roster construction boundary. Freeze
  count in the generated competition state; do not reroll at each race or
  retrofit an active Cup.
- **Invitation:** keep normal T3 core eligibility and explicit mode policy.
  Do not insert reward/special T3 records simply because the count grows.
- **Master Rallye:** change only new competition creation. Audit the maximum
  serialized CarN keys and all competitor/points loops before adding entries;
  never rewrite a saved roster at Resume.
- **Challenge:** do not add more opponents until each authored challenge's
  goal logic, preview, scoring and retry behavior is proven to support them.
  A larger Race/NumCars value alone is not a valid test.

Challenge's examined builder reads an event-specific authored vehicle pair,
and the current UI/preview path presents one opponent. This establishes the
existing single-opponent contract, but does not prove that every event's
objectives are fundamentally incompatible with multiple opponents. The data
schema, success checks, ranking, preview and retry semantics need per-event
tracing before making that claim.

Minimum practical qualification should begin with the native current mode
count and one increment at a time. The current data does not justify publishing
per-mode min/max values other than Quick Race's designed 1..7 AI choice and
the existing fixed event counts above.

**Status:** owner and lifecycle map `CONFIRMED_BY_EXE`; existing roster reuse
`CONFIRMED_BY_RUNTIME`; configurable counts outside Quick Race are feasible
with localized changes but require substantial mode-specific testing. No
other-mode count was changed here.
