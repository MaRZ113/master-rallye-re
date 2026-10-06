# R-AI1.2 runtime closeout

**CLOSED / CONFIRMED_BY_RUNTIME**, 2026-10-05. Human runtime observations
are the authority for gameplay, completion and lifecycle; native captures
corroborate state. Automated checkers remain BROKER_STATE_MATCH_ONLY with
runtime_full_pass=false. No new feature or capacity work was performed.

## Exact research package

| Component | SHA256 | Bytes |
|---|---|---:|
| four-hardened EXE | 60946990b685390032510c4bbed448674faebf33c929a46f52bc527e219dfc85 | 3121214 |
| five-hardened EXE | 32a09c466b9bb40513d8a801e0e9f420e902d6486ceb7ae76b243c7408404629 | 3121214 |
| MRallyeRandomizer.dll | 517c4aa20e8dc80f2d51a64a79e59183d3ae27d47dbb3e0334ab458695c366f4 | 89600 |

Exact candidate inverse verifiers, module/source pins and package staging pass.
The DLL hash describes the verified package; Broker captures pin the EXE, not
the loaded DLL memory. Human test provenance supplies module-use attribution.

## Mode / policy runtime matrix

| Mode | Human-confirmed result | Boundary |
|---|---|---|
| QuickRace | Stock, Mixed, Diverse; 1/2/3/4 AI; player/course/difficulty/count changes | Existing active participants only |
| QuickRace | NEW generation can change roster; Restart retains IDs/classes/drivers | Restart is not a fresh random sample |
| Challenge | Stock and Mixed opt-in, successful Challenge11 completion | Stock default; exact stock DriverID preservation not confirmed |
| RallyeCup | Diverse roster generation and observed next-stage reuse | Tested in-process cup lifecycle |
| Invitation | Mixed roster generation and observed next-stage reuse | Tested Invitation lifecycle |
| MasterRallye | Diverse generation, native save, fresh-process Resume, next-stage reuse | Exact identity restored by native save/load |

All confirmed entries above are **CONFIRMED_BY_RUNTIME**. Diverse's three-AI
sample has classes0/2/1: every eligible class before repetition. Mixed allows
duplicate classes. No mathematical RNG uniformity or exact probability claim.

## Native capture examples

Capture IDs below have prefix20261005; full filenames, JSON/raw/selected-block
hashes and all participant records are in [derived summary](runtime-closeout-summary.json).
Tuples are absolute CarID / class index / DriverID; class0/1/2 is T1/T2/T3.

| Capture | Active AI tuples | Meaning |
|---|---|---|
| 092531_qr-mixed-ai2-1op | 0/0/8 | One AI |
| 092431_qr-mixed-ai2-2op | 4/0/5, 24/2/4 | Two AI |
| 092652_qr-mixed-ai3 | 4/0/7, 15/2/9, 8/1/5 | Three AI |
| 092734_qr-mixed-restart | 4/0/7, 15/2/9, 8/1/5 | Same identities on Restart |
| 092829_qr-mixed-new | 8/1/6, 7/1/1, 1/0/0 | New generation differs |
| 093104_qr-mixed-ai4 | 12/1/6, 23/2/0, 9/1/2, 20/2/4 | Four AI, NumCars5 |
| 093419_qr-diverse | 5/0/4, 17/2/6, 11/1/8 | T1/T3/T2 cycle |
| 093728_cup-stage1 -> 093834_cup-stage2 | 0/0/0, 10/1/1, 14/2/5 | Same roster |
| 093952_invitation-stage1 -> 094103_invitation-stage2 | 2/0/2, 5/0/1, 12/1/9 | Same roster |
| 094213_master-new -> 094320_master-resume -> 094402_master-next | 1/0/7, 20/2/4, 10/1/0 | Same roster; human6/0/30 |

Master PID changes44796 ->37108 at Resume. Human observed full process exit,
native save/load and further progression. All three captures preserve the
same CarID/Class/DriverID tuples. CUSTOM RANDOMIZER SIDECAR: **NOT REQUIRED**
for tested V1 QuickRace/Cup/Invitation/Master lifetimes. Cup/Invitation disk
resume across a process exit was not tested. Future sidecar remains a fallback
only for state genuinely absent from native persistence.

## Config reload and log provenance

MRallyeRandomizer.ini changes apply at the next roster-generation boundary;
existing race, Restart, stage transition and native load keep their roster.
Human tested edits without process restart. Captures093335 Stock and093419
Diverse share PID44796; matching diagnostic generation groups use config hashes
77b7498e93124814c04019537e484ff8cf439750758963c95b5b8f0c88b624f2 and
6f3a54720bf71ce86e7efca5accd19eef84e7233b2995044e859d7652ea33e41.
This is **CONFIG RELOAD AT ROSTER-GENERATION BOUNDARY / CONFIRMED_BY_RUNTIME**,
not an instant change to an active race.

MRallyeRandomizer.log is external diagnostic evidence for mode/policy/count/
class/config hash and generation calls. It is not a Broker Dump and has no PID
field. Human sequence and matching captures associate it with the tests;
its hash/size are preserved in the summary, raw log remains uncommitted.
Stage/resume compositions match original generation groups; no later generation
was observed during the human stage transitions.

V1 config remains the five mode keys and Stock/Mixed/Diverse. Missing/invalid
values safely fall back to Stock as specified in [config](config.md) and tested.

## Challenge caveats

RaceID35 maps to Challenge11. Human observed Mixed completion. Capture093528
Mixed has humanID18 and AIID2/T1/Driver2 (Tata); capture093635 Stock has the
same human and AIID23/T3/Driver6. Exact stock DriverID preservation is
**NOT IMPLEMENTED / NOT CONFIRMED**. Original driver selection remains native;
separate new-event samples do not isolate why the driver differs. Matched-seed
static driver checks do not establish runtime identity equality across policies.

Won_Challenge11=1 is present, but already exists in earlier captures. That
persistent flag alone cannot prove a newly completed Mixed Challenge; the human
completion report supplies that evidence. Rules/event/progression remained playable.

Human frontend preview still shows authored PRIVATEER ICE CREAM VAN while the
Mixed race uses Tata. **CHALLENGE FRONTEND PREVIEW SYNCHRONIZATION: NOT
IMPLEMENTED / NON-BLOCKING POLISH**. See [future items](future-items.md).

## Evidence integrity and bounds

All20 JSON/raw pairs passed the audited read-only parser integrity check;
freshness is post_baseline_complete_dump_proven. Manual filename alias
092431_qr-mixed-ai2-2op retains internal label/raw-sidecar metadata using3op.
Corresponding raw SHA matches. Historical metadata was not changed; integrity
is unaffected and this is not an Observatory fault. Names alone do not determine
participant counts:092212/092257 also contain three AI despite their labels.

Randomizer applies through Car4 in the separately confirmed five-car setup;
it never creates participants. Five total is confirmed; six+ remains UNKNOWN.
Research EXE bridges call the modular DLL. Original-EXE-unchanged removable
fail-closed loader deployment is **NOT YET COMPLETE** and was not begun here.

Challenge preview sync, optional exact-driver policy, count UI and higher
capacity remain separate future decisions. No proprietary binaries, raw dumps,
logs, screenshots or saves are committed.
