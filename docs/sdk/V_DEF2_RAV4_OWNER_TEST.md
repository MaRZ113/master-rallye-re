# V-DEF2 — Demo RAV4 owner D3D8 checklist

Launch:
`.research-output/vehicles/v-def2/owner-candidate/workshop/builds/first/candidate/Launch-SDK-Roster.cmd`

Workshop:
`.research-output/vehicles/v-def2/owner-candidate/Open-Restoration-Workshop.cmd`

This isolated32-record candidate appends **TOYOTA RAV4**, ID31, T2 local11
(twelfth/last T2 entry). Forester remains ID30 and is already owner accepted.
No files need copying into the original game. Old accepted builds stay intact.

1. Select RAV4. Confirm white/blue PERFORCE/AIWA model, generated matching
   three-quarter menu icon and proper large-model height/rotation. Original
   historical green/white artwork is intentionally not used.
2. Enter a race. HUD mini should be a separate SIDE view of this white/blue
   RAV4. Check both wheel sides, steering/spin, contact and suspension travel.
3. Drive over bumps, brake/reverse and compare tyre wear over a longer run.
  100 compatible Demo8.4.1 physics fields are used; torque curve, old damage
   fields, application offsets and tyres have explicit retail substitutions.
   Static source hub wheelbase2.553561 differs from physical2.4 and is not
   automatically adjusted. Report any mismatch rather than tuning around it.
4. Compare rear brake OFF/ON from rear and quarter angles. Check white cores,
   halo depth/flicker, disappearance and body/bumper/headlight/tyre light leakage.
5. Test body damage and front/left/right glass. Intact frames/doors remain
   opaque. No independent rear glass zone was invented. Cracked appearance is
   an MR adaptation, not recovered original Demo damage playback.
6. Check audio, camera/reset and shadow. Complete a race, enter Results, return
   to menu and re-enter. **TOYOTA RAV4** is intentional in the driver/Results
   field: the original driver's identity remains unknown. Do not expect Reece
   Russell or infer a name from a crew texture.
7. Switch to Forester and a stock vehicle, then restart the candidate. If useful,
   check RAV4 AI in Quick Race/Cup/Master.32-entry save/AI/full lifecycle remains
   unqualified until actual owner testing; CPU helper tests are not a substitute.

Please provide menu/HUD, side/wheels, rear OFF/ON, damaged glass and Results
captures plus handling/tyre feedback. Preserve the original save and accepted
launchers; no DLL replacement is required. The launcher recognizes the locally
qualified collision-debug1/2 proxies but rejects other unknown updates. Send
the exact error if another parallel renderer update changes the launch check.

Forester success is recorded independently. RAV4 stays **PENDING OWNER** until
this test, and no additional imports begin automatically.
