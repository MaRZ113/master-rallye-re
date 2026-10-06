# R-AI1 — mixed-class opponents

Correction: previous static model **STILL VALID**; fresh-profile T3 frontend
reachability assumption was incorrect. Current proof is T1 player + T3 AI.
[Correction note](correction.md); old handoff is SUPERSEDED / DO NOT USE.

Status: **R-AI1 — MIXED-CLASS OPPONENTS: CLOSED / CONFIRMED_BY_RUNTIME**.
Fixed mixed-class existing participants passed the full race/Results proof.
The fixed fresh-profile proof passed; [verified capture and human observations](runtime-result.md).
Generalization is also closed in [R-AI1.1](../r-ai1-1/runtime-closeout.md).
Participant-count questions are deferred to separately authorized R-AI2.
The historical runtime handoff below is completed and superseded for new tests.

## Starting state and boundary

Main checkout `master-rallye-re`, starting branch `research/r-mat1`, HEAD
`ce05003`. R-MAT1 was already present. Created local `research/r-ai1` at that
HEAD without rewriting history. Starting tracked tree was clean; existing
untracked `_ghidra_project/` and `master-rallye-re-blend.zip` were preserved.
No sibling checkout/worktree, material code, assets, registry, participant
capacity or published history was changed. No push.

This proof is ordinary offline **Quick Race / Race (mode 2)**, one player and
three opponents. Practice skips opponent generation; campaign, two-player,
attract and network paths are outside the proof.

## Static completion gate

| Question | Recovered answer | Evidence |
|---|---|---|
| Player class source | Frontend selection screen class at +0x10; later registry-derived Race/Car0/CarClass | `0x481340`, `0x47B780` |
| Player absolute ID source | Per-class local index +0x14/+0x18/+0x1C, converted by `0x481E20`; saved absolute Frontend/QuickRace/Car0 | `0x481417`, `0x481456` |
| AI requested class | Car0 class passed by Quick Race to chooser | `0x47B92C`, `0x47B95E`, `0x458090` |
| AI absolute ID source | Class-filtered pool of absolute IDs; shuffled, consumed into [ESP+0x14] | `0x458127..0x458424` |
| Homogeneity owner | Quick Race supplies player's class; chooser filters vehicle pool by it | `0x47B780 -> 0x458090` |
| Smallest supported intervention | Change Car1's chosen absolute ID after pool/driver bookkeeping; retain stock class/name/physics derivation | `0x458428` |
| Downstream hazards | AI balance scalar and race-description class label still use Car0; retain both. No later AI ID/class normalizer found in audited ordinary path | `0x42CFF1`, `0x42E020`, `0x4BBE8C`; [audit](downstream-consumers.md) |

These answers are **CONFIRMED_BY_EXE** at the traced boundaries; the bounded
fixed runtime result is recorded separately. Broker key storage is not a native
participant array; distributed actor, AI and result records are distinguished
in [participant-structure.md](participant-structure.md).

## Stock map and controlled proof

Named pristine retail records: **25**. Native classes: **0=T1: 7**, **1=T2: 7**,
**2=T3: 11**. Absolute/local mapping: T1 `ID=local`, T2 `ID=7+local`, T3
`ID=14+local`. [vehicle-class-map.json](vehicle-class-map.json) lists every
record and constructor site; it reuses the existing canonical registry and a
fresh hash-locked `r5v_a_exe_registry` extraction, rather than another parser.

| Participant | ID / native class | Identity |
|---|---|---|
| Car0 | 0 / 0 (T1) | Landcruiser, TOMMEK DIRTBEAST, normal fresh human path |
| Car1 | 14 / 2 (T3) | Wildcat, BOWLER WILDCAT, existing AI driver |
| Car2, Car3 | Distinct normal stock IDs1..6 / 0 | Unchanged stock chooser outputs; two AI controls |

Use a fresh stock profile without bonus unlocks. Neither controls' IDs nor
driver IDs are hard-coded. Exactly one chosen AI identity changes; the RNG,
original pool consumption and driver allocation remain intact. NumCars stays
four. No canary or asset edit is needed: the T3 buggy is visibly distinct from the
T1 SUV player.

## Evidence and deliverables

Pristine source SHA256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Human candidate SHA256:
`bae5de6aa3ba6cfcd08425c5a00341a3c374ec503b4ba944db6fc2c0d6a77a57`.

Latest installed Ghidra 12.1.4 and ghidra-bridge read-only exports were used;
temporary disassembly/emulation transactions were rolled back without saving
the project. Direct-call cross-checks used objdump. Raw exports/dumps and the
generated EXE/manifest stay ignored in this checkout's `.research-output/r-ai1`.
No proprietary EXE or assets are committed.

See [player-selection](player-selection.md), [opponent-selection](opponent-selection.md),
[class-homogeneity](class-homogeneity.md), [driver-coupling](driver-coupling.md),
[intervention](intervention.md), [validation](validation.md) and the
[human runtime plan](runtime-test-plan.md).

An incidental uncalled result fixture at `0x47D1E0` sets five entries, and a
network mirror contains a larger slot guard. These are deferred capacity clues,
not an active race capability or R-AI1 intervention. R-AI2, Courses, Ghost Mode
and registry expansion were not begun. Stop at this mixed-class handoff.
