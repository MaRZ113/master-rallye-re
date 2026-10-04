# Future R-AI1.2 — design notes only

**NOT STARTED.** Owner observations supplied with the R-AI2 closeout: the
R-AI1.1 randomizer works in its previously validated three-AI Quick Race setup;
changing participant count can fall back to stock same-class behavior. Rallye
Cup, Invitation and Master Rallye were reported to retain stock same-class
behavior; Challenge fixed/scripted opposition is mode-specific. These reports
are coverage observations, not newly traced mechanism or this five-car
candidate's behavior. R-AI2 deliberately has class randomization off.

Future design goals: participant-count-aware iteration; per-mode enable flags
for QuickRace, Challenge, RallyeCup, Invitation and MasterRallye; selectable
Stock/Mixed/Diverse policy; per-mode roster lifecycle and persistence. No config,
hook, variable-count chooser or persistent roster sidecar is implemented here.

Quick Race new-race regeneration versus Restart composition reuse is already
runtime-confirmed for the earlier four-car R-AI1.1 test. Preserving a roster
through a Rallye Cup/championship is a **HYPOTHESIS / DESIGN GOAL**. Master
Rallye roster persistence coordinated with its save lifecycle is likewise
**HYPOTHESIS / DESIGN GOAL**, not confirmed save semantics. Challenge should
potentially require explicit opt-in to respect intentional fixed opponents.
Per-mode owners and persistence must be traced in a separately authorized
R-AI1.2 phase. Capacity beyond five is a different future R-AI2.1 decision.
