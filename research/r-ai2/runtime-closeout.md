# R-AI2 final runtime closeout — exact five-car target

**CLOSED / CONFIRMED_BY_RUNTIME.** One human and four AI completed the ordinary
Quick Race lifecycle. Human observations are the owner's final closeout report;
capture facts below were independently checked against JSON/raw pairs. No new
game launch, capacity experiment, EXE or randomizer change was made here.

Candidate: `retail-r-ai2-five-car-hardened`, 3,121,214 bytes, SHA256
`806ebedcd6d174682fcc4619fb75eaabca2a1281eda4d4d784807b3583f5f2e2`.
The existing executable, tool verifier and [manifest](patch-manifest.json)
agree. Composition remains pristine + Loading/Dump hardening + guarded R-AI2,
with randomized class selection off. Build-time manifest status is historical;
the current runtime result is in [derived summary](runtime-summary.json).

Active capture **20261004-214059_five-race**: NumCars5, NumPlayers1, Type2,
AttractFalse, all class0/T1:

| Participant | CarID | DriverID | PlayerType | Own car/wheel family |
|---|---:|---:|---:|---|
| Car0 | 0 | 30 | 1 human | Landcruiser |
| Car1 | 3 | 4 | 2 AI | Terrano |
| Car2 | 6 | 0 | 2 AI | Frontera |
| Car3 | 2 | 8 | 2 AI | Tata |
| Car4 | 4 | 7 | 2 AI | Chevyblazer |

Car4 named values: WheelBase2.75, TrackWidthFront1.70, GearRatioDiff3.50;
independent Vehicles/Car4 and Physics/Car4 state exists. Network/Car4 contains
IpAddress/Finished/FinishTime/MaxTime; this proves captured offline mirror
state, not multiplayer packet capacity. Human saw five independent spawned
models/wheels; Car4 drove, followed the course, collided, took damage, progressed
and finished without aliasing or corrupting other racers. These combined
observations establish **FIFTH ACTIVE PARTICIPANT MATERIALIZATION**, actor,
physics, collision, damage and four-AI operation **CONFIRMED_BY_RUNTIME**.
Broker path presence alone is not actor evidence.

Human observed functioning five-participant HUD/markers and player **5TH**.
Results capture **20261004-214833_five-results** and visible rows:

| Place | Name | Displayed time | Result image ID |
|---|---|---|---:|
| 1 | TESSA BAMFORD | 04:07:55 | 22 |
| 2 | BRUNO SELLIER | 04:09:35 | 20 |
| 3 | BAMBOS KOUYIOUNTA | 04:45:04 | 15 |
| 4 | ALAIN PEACOCK | 04:49:82 | 1 |
| 5 | 1P | 04:51:32 | 9 |

PositionList/NameList/TimeList each have five items, retaining native quoted
StringList representation. Five finishers, timing, ranking and correctly
rendered rows are **CONFIRMED_BY_RUNTIME**. Competitor indexing is participant
index, not result row order:

| RaceData record | RacePosition | RaceTime / TotalTime |
|---|---:|---:|
| Competitor0 | 5 | 291.32 |
| Competitor1 | 3 | 285.04 |
| Competitor2 | 2 | 249.36 |
| Competitor3 | 1 | 247.56 |
| Competitor4 | 4 | 289.82 |

These JSON/raw-bound completed-race records are **CONFIRMED_BY_RUNTIME**
capture evidence for the internal five-participant result pipeline. The first
two numeric times differ by0.01 from displayed centisecond strings; both forms
are preserved exactly, and formatter/rounding attribution is not investigated.
Nothing here establishes Competitor5+.

Results Car0..4 values22/20/15/1/9 are **registry image IDs, not Vehicle IDs**;
Car5..7 are blank image12. Eight authored image positions/browser rows remain
a static capacity clue. Five actual rendered rows are now runtime-confirmed;
eight active participants remain UNKNOWN.

Native hardened Dump emitted empty PointsList and continued into later entries;
human confirmed game survival. Textual `{}` does not distinguish NULL payload
from allocated empty list. Five-car Replay worked; Results/Replay/frontend
return completed without observed crash, hang or corruption. HUD, Dump safety,
Replay lifecycle and tested teardown are **CONFIRMED_BY_RUNTIME**. This does
not prove every replay-camera path, complete heap reclamation or long-run
memory stability; [stock ownership caveats](native-storage.md) remain.

The unchanged checkers return **BROKER_STATE_MATCH_ONLY** and
**BROKER_RESULTS_MATCH_ONLY**, both `runtime_full_pass=false`. Those verdicts
are intentionally limited. Human observations establish the behavioral FULL
PASS, rather than upgrading automated checks. Derived summary retains capture
IDs, JSON/raw/selected-block hashes and exact values; raw dumps/screenshots/
EXEs remain ignored and are not committed.

Architecture: for this verified Quick Race pipeline the stock four-car limit
is substantially a policy/setup boundary. Relaxing two effective opponent
getter calls lets five cars traverse existing engine subsystems. No physical
participant storage expansion, race-loop widening or table relocation was
required. Exact nine ranges and reproduction remain in
[intervention](five-car-intervention.md); no intervention bytes changed here.

**Five: CONFIRMED_BY_RUNTIME. Six/seven/eight/generic-N: UNKNOWN.** R-AI2 closes
only this target. Future public deployment remains a removable exact-build,
fail-closed external runtime mod with the original EXE unchanged on disk.
[Randomizer follow-up](randomizer-follow-up.md) is a design note, not new work.
Stop; higher capacity and R-AI1.2 implementation require separate authorization.
