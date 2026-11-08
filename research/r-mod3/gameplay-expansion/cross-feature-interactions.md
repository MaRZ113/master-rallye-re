# Cross-feature interactions and lifecycle rules

The stable unit is a **prepared event/roster snapshot**. Configuration may
reload while the game runs, but it should affect only a new preparation
boundary. Once a lobby preview or campaign roster has been published, changing
the INI must not mutate its participant identities, count or grid assignment.
This extends the current F3 generation-snapshot principle and the already
observed Challenge Preview cache behavior.

## Precedence proposal

Human vehicle identity:

`Explicit ForcedPlayerCar > Player Randomizer Policy > native Vehicle Select / authored event`

AI physical identity per slot:

`Explicit ForcedRoster slot > AI Randomizer Policy > native chooser`

These rules apply only when the mode supports the feature and all physical IDs
are registered and materializable. A policy must not silently cross classes.
Each chosen CarID receives a registry-derived CarClass. DriverID, participant
slot, player ownership, controller and grid ordinal remain independent fields.

The opponent count is a separate event-level value. `MaxOpponents` controls
the supported UI/configuration ceiling; an exact event count chooses one
roster size. Randomizer mode controls eligible vehicle identity. Forced
CarID controls a specific identity. Starting-grid order controls where a
participant starts. These must not share one overloaded numeric setting.

## Interaction table

| Combination | Safe contract | Current uncertainty / gate |
|---|---|---|
| Forced player ID equals an AI ID | Permit only if separate CarN participants are constructed and all per-slot runtime state stays independent. Keep IDs explicit. | Repeated physical CarID gameplay is not qualified; first diagnose the seven-AI crash. |
| Randomized player + seven class-restricted AI | Freeze the player first, then build AI pool under explicit policy and native exclusion rules. Never silently expand to another class. | Seven-AI T1/T2 crash cause and duplicate lifecycle are unknown. |
| Forced AI roster with duplicates | Reuse only a validated eligible physical ID; retain independent DriverID and participant/AI objects. | Native pool refill exists, but end-to-end duplicates/Results/replay are untested. |
| Forced player in Challenge | Prepare a player/opponent pair keyed by event; feed the exact same identity to preview and race. | Authored Challenge player rules and cross-class correctness are unproven. |
| New count in Cup / Master | Apply once on new Cup/competition creation; persist through stages and save/Resume. | Count capacity of scoring, standings and serialization is unproven. |
| Forced grid plus fixed event progression | Reorder native grid ordinals without changing CarN identity or event ranking unless separately intended. | Challenge-specific start choreography is unknown; per-course clearance required. |
| Hot INI edit while preview is open | Keep displayed/prepared snapshot until Back/new event boundary; report pending values if useful. | Current live reload is human-confirmed for supported F3 policies; new dimensions need a generation token/snapshot. |

## Reload scope

Logging and future-pool policy can be read live at a safe generation boundary.
Prepared CarIDs, exact participant count, forced roster and grid permutation
must be frozen for the current event. Current race objects are never rewritten
by a config reload. Existing Cup/Invitation roster and saved Master Rallye
identity remain native state and are not regenerated when a DLL or INI
changes.

## Addon interoperability boundary

Vehicle SDK remains optional. A future adapter may consume only an explicit,
validated registry export that proves a CarID is registered in this process,
has a class and effective family, resolves model/wheel/physics resources, and
declares mode/pool eligibility. Do not scan folders or infer registration
from files. Stock-only Randomizer operation must remain complete without the
SDK, addon manifests, ID26/ID27 runtime expansion or the SDK launcher.
