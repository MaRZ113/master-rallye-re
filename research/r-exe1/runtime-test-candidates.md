# High-value runtime-test candidates

No test below was run during R-EXE1. These are preparation notes for a human-controlled future phase. Every test uses an isolated install/profile or read-only debugger observation; restore means discard the clone and verify its baseline hash, not modify authoritative corpora.

## RT-01 — Loose file versus Data.sma precedence

- **Hypothesis:** `0064D530` returns a loose file when the same virtual resource is present loose and in the retail archive.
- **Build / target:** Retail; `0064D530` opener and `00652570` archive-member fallback.
- **Observation/change:** In a byte-for-byte disposable install, choose a harmless resource opened through a known path; put distinct test sentinel content at the matching loose path and in a copied `Data.sma` entry. Break at the open return and identify the selected backing stream/content.
- **Expected outcomes:** Loose content proves local override for that path; archive content suggests an alternate root/path or non-exact match; open failure indicates path normalization/entry naming needs review.
- **Interpretation:** One path only; do not generalize to every resource root until repeated.
- **Safety/restore:** Never edit corpus Data.sma. Hash both source and clone before, keep a copy of the cloned archive, then discard the entire test install and confirm source hashes unchanged.

## RT-02 — Broker progress value persistence

- **Hypothesis:** `SavePlayerState` progress broker entries are serialized by normal gameplay save flow.
- **Build / target:** Retail; progress wrappers `004AF3B0/004AF430`, `004AFCC0/004AFD40`, broker entry at `00601D00`.
- **Observation/change:** Clone the user profile. Record file inventory/hashes. Change one ordinary progress field through normal play; observe broker writes and OS file writes; exit cleanly and compare only files in the clone.
- **Expected outcomes:** Matching save-file diff supports persistence mapping; broker change without a file write suggests deferred saving or another state; no broker change weakens the assumed normal-play trigger.
- **Interpretation:** Do not claim the file format until load path and re-load are separately observed.
- **Safety/restore:** Copy/rename profile to a unique backup, run only against the clone, verify no writes under source profile, restore by discarding clone.

## RT-03 — BuildData UI reachability and output scope

- **Hypothesis:** Retail's callback at `005B2F80` is exposed by an editor/development UI and invokes `005B2DA0` on a selected folder.
- **Build / target:** Retail; callback table near `00692F8C`, wrapper `005B2F80`, walker `005B2DA0`.
- **Observation/change:** First inspect/trace menu dispatch without invoking. If a normal command is visible, invoke against a copied minimal DataGx test folder and capture chosen root, output extensions, counts and overwrite calls.
- **Expected outcomes:** Visible command plus call entry confirms reachability; callback reference without UI selection supports registration-only; output outside chosen root reveals path policy/needs immediate stop.
- **Interpretation:** A command can still be unsafe for real data; no original data directory may be selected.
- **Safety/restore:** Disposable retail install and synthetic inputs only; inspect all output paths before running; discard test tree after recording hashes.

## RT-04 — Route-state broker transitions

- **Hypothesis:** `Race/Car0/LastMarker` and `WrongWay` update as route progress/direction changes.
- **Build / target:** Retail; dynamic broker path resolver `004D0580`, route candidate strings and race vehicle state.
- **Observation/change:** With a cloned profile and unchanged France1 baseline, set read/write breakpoints on broker access; record values through forward RaceLine progression, brief reverse travel, and a controlled route departure.
- **Expected outcomes:** LastMarker increments or changes near markers; WrongWay toggles on reverse/off-route; no access or unchanged value means dynamic path was constructed elsewhere or string is dormant.
- **Interpretation:** Correlation is not proof of marker-specific semantics until repeatable event boundaries are observed.
- **Safety/restore:** Do not alter course data or the active R5T-C experiment; record debugger values only; discard clone.

## RT-05 — Pace-note owner/current-note lifecycle

- **Hypothesis:** Race/CarN/PaceNoteOwner and PaceNote are updated from `gaRacePaceNoteAI` triggers.
- **Build / target:** Retail; pace-note factory/property path around `0048C230/0048C5F0` and broker paths.
- **Observation/change:** Keep course baseline unchanged; watch the two broker values and relevant AI update calls while approaching and passing one known pace-note trigger.
- **Expected outcomes:** Value change aligned with trigger and display supports owner/current-note relation; update without display separates logical trigger from HUD; no access weakens the candidate link.
- **Interpretation:** Record car index and trigger ID; do not infer all courses from one event.
- **Safety/restore:** Read-only debugger on a cloned profile; no RaceTest XML edits; exit without saving if any unrelated file changes.

## RT-06 — Ghost playback object initialization

- **Hypothesis:** GhostPlayback plus valid Ghost_StartPosition creates one GhostCar; invalid position clears the flag as seen statically in `0048E9C0`.
- **Build / target:** Retail; `0048E9C0`, `Race/GhostPlayback`, `Race/Ghost_StartPosition`.
- **Observation/change:** On a copy, use an existing game/config route to enable playback; watch the two keys, GhostCar constructor, and file opens. Do not fabricate replay bytes.
- **Expected outcomes:** GhostCar construction with valid setting confirms the static path; flag clear on invalid value matches branch; no file open suggests playback data is already resident or another loader supplies it.
- **Interpretation:** This does not map recording or file format.
- **Safety/restore:** Preserve profile and XML originals, change only clone, restore by discarding it.

## RT-07 — Alpha-test versus alpha-blend runtime state

- **Hypothesis:** 9.10/retail alpha-test shader families select cutout state separately from blended-alpha materials.
- **Build / target:** Retail, with 9.10.0 comparison; selector `00580360`, shader registry `00565DA0`.
- **Observation/change:** Use existing known cutout and translucent assets; break at shader selection and D3D render-state setters; capture selected family, alpha-test/blend states, texture-stage configuration.
- **Expected outcomes:** Distinct state combinations support the hypothesis; same shader but changed render state means selection is partly external; no direct selector hit suggests a different fixed-function path.
- **Interpretation:** Keep exact material fields and runtime states in the evidence log; do not change tool preview behavior from a single asset.
- **Safety/restore:** No asset modification is needed; use a clean cloned game/profile and read-only debugger.

## RT-08 — UDP bind/enable path

- **Hypothesis:** The port-22222 listener is controlled by the network sync configuration and reachable only in a multiplayer/race setup.
- **Build / target:** Retail; listener `00433240`, manager `00653860`, Network/SyncState keys.
- **Observation/change:** On an isolated local machine, watch enable/disable branches and socket creation/bind; record local addresses only. Do not connect external hosts.
- **Expected outcomes:** Bind after a sync setting confirms gating; startup bind in all modes means broader service; never binding despite flag narrows the runtime trigger.
- **Interpretation:** No protocol or player-cap conclusion without send/receive evidence.
- **Safety/restore:** Local loopback only; disconnect networking before launch; close game and confirm socket release.

## RT-09 — Replay recorder producer and file writes

- **Hypothesis:** RecordReplay/RecordSpline control a file-producing path paired with GhostPlayback.
- **Build / target:** Retail; record keys and file API call graph to be resolved statically first.
- **Observation/change:** Only if a normal in-game recording option exists, run one short race with file APIs filtered to newly created paths; record extension, sizes, timestamps and write callers.
- **Expected outcomes:** Race-time writes plus matching replay reads support a producer/consumer pair; no writes despite toggled key weakens reachability; unrelated writes must be excluded by call stack.
- **Interpretation:** File structure remains unknown until a separate static parser/format pass.
- **Safety/restore:** Clone profile; hash inventory before and after; remove/discard only the clone output after evidence capture.

## RT-10 — RaceLine progress consumer

- **Hypothesis:** RaceLine marker/sample index is consumed by AI or split initialization beyond the existing nearest-sample relation documented for SplitTime0.
- **Build / target:** Retail; `gaRaceLineAI` constructor/factory `0048ACB0/0048ADA0`, AI vehicle update path to be selected statically.
- **Observation/change:** On an unmodified course, watch nearest-sample/progress fields for one AI and player vehicle at fixed points; compare state with course RaceLine marker sequence.
- **Expected outcomes:** Monotonic sample progress supports a route-state consumer; only split initialization changes supports a narrower use; no path read requires a different candidate.
- **Interpretation:** Do not move RaceLine points in the active R5T work; first capture baseline state.
- **Safety/restore:** Read-only observation in a disposable profile, no course edits, restore by discarding clone.

## Static-first experiment

Before any of the runtime tests, trace the retail readers/writers of broker save flags and resolve the method table that points at `005B2F80`. These are low-cost and reduce the chance of testing an unexposed or misidentified path.
