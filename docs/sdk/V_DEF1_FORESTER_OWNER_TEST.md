# V-DEF1 — owner D3D8 test

**Completed:** the owner reports the corrected Forester fully working/tested.
Retain this checklist as V-DEF1 history. The new active test is
`V_DEF2_RAV4_OWNER_TEST.md`; do not treat Forester's acceptance as RAV4 success.

Private candidate:
`.research-output/vehicles/v-def1/owner-fixes/release/workshop/builds/first/candidate/Launch-SDK-Roster.cmd`

Workshop project:
`.research-output/vehicles/v-def1/owner-fixes/release/Open-Forester-Workshop.cmd`

**Owner evidence already received:** selection/race entry screenshots and explicit
confirmation of Darren Sutherland in race. Do not ask to reconfirm the name as
if it were unknown. Full race/Results/re-entry remain unverified.

**Priority retest for this revision:**

1. Large menu model: Forester should now sit near stock height. Race body/wheel
   geometry has not been lifted or rescaled.
2. Race HUD: use the original pink SIDE-view mini icon from Demo9.10.0, not the
   three-quarter menu CarSheet or Demo9.3.1 Results art.
3. Rear brake OFF/ON: compare both sides and oblique angles with WOOLDAND.
   Confirm white hot cores, separate halo, no floating patch or flicker/body glow.
4. Drive long enough to compare tyre wear and handling. This candidate uses a
   complete independent RETAIL Forester clone, with stock retail tyre tables.

Previous `release-candidate` is preserved for rollback. See
`V_DEF1_FORESTER_OWNER_REVISION.md` for exact source/resource changes.

This is an experimental31-record CMD build, classes8/11/12. Original retail,
accepted30-entry builds and installed wrappers are unchanged. The launch
preflight targets the existing qualified retail build and approved D3D8 proxy;
Randomizer coexistence is not newly qualified. Do not install or copy DLLs.

1. Run the candidate CMD. In T2 select the eleventh entry **SUBARU FORESTER**.
   Check the authentic pink Demo CarSheet and large3D frontend. Confirm retail
   WOOLDAND and the existing Subaru/Lancer/Trooper entries remain independent.
2. Enter a race. Inspect original body/livery,crew,wheels and both wheel sides.
   Drive,reverse,steer and test bumps/landings. Report clipping,float/sink or
   suspension behavior. Physics is an independent exact RETAIL WOOLDAND clone.
3. Compare brake OFF/ON at rear/rear-quarter angles. Both source lens assemblies
   should light, with separate original retail ON core and native halo. Check against body/bumper leakage,
   excessive brightness and disappearing effects while turning.
4. Test body damage and front/left/right glass. Pane frames and doors must stay
   opaque. There is no qualified separate rear-pane zone: original rear artwork
   is intentionally preserved. Cracked UV/shading is an explicit MR adaptation.
5. Check cameras/reset,sound and shadow. Complete one race and verify **DARREN
   SUTHERLAND** in Results,then return to menu and re-enter a race. Also test a
   stock vehicle after Forester to expose retained state/resource problems.
6. If convenient,check Forester AI in Quick Race/Cup/Master Rallye. CPU helper
   emulation is not proof of real race AI,Campaign or save behavior.
7. Exit and start again. Check selection/save persistence. Candidate state is
   isolated; keep it out of ordinary retail/accepted builds. To disable this
   test,close it and use the original retail or an accepted candidate launcher.

Please supply corrected frontend/HUD/rear brake OFF/ON captures and tyre-wear
feedback. A Results capture and race completion/re-entry confirmation can close
the remaining lifecycle gates later. Corrected behaviors stay **PENDING OWNER**;
retain the baseline confirmations above without extrapolating them.
