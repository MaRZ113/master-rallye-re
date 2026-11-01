# Build, validation and recovery

Validate checks source pins, resource ownership, native structure and supported
editing boundaries. Build uses the shared SDK core and a snapshot of inputs.
Stock projects emit isolated overrides; zero-edit projects pass through unchanged.
Converted-family projects generate resource packages, not a new registered CarID.
Addon projects require their qualified roster/runtime inputs.

Open last build folder to inspect reports and the generated launcher. Test that
candidate in Master Rallye separately. Offline Previewer captures do not qualify
gameplay, damage, AI, performance or audio lifecycle.

If validation fails, retain its exact error. Restore the selected edit or Undo,
then validate again. Do not bypass source hashes or copy unrelated runtime assets.
Private game resources are not included in source review archives.


V-DEF1 adds a separately named experimental31-record profile for one independent
Forester test. It requires explicit`experimental_record_count:31` and three
contiguous appended T2 author entries; ordinary29/30 builds retain their guards.
The resulting CMD candidate is ready for owner testing,not gameplay-qualified
or DLL-installable. Keep its saves and resources isolated and follow
`V_DEF1_FORESTER_OWNER_TEST.md`.


## Vehicle order and class assignment

In the legacy Workshop, **Configure → Configure vehicle order and classes**
opens the reusable roster declaration. `selection_order` is a complete object
of T1/T2/T3 physical-ID arrays. Reorder within each class without changing CarIDs,
resource/UI frames, physics or identities. Use `null` for canonical append order
on existing29–32 profiles. Save creates a private project-owned configuration;
the selected accepted roster is read-only. Return to its existing path in
Configure to roll back.

`class_assignments` maps existing addon physical IDs to T1/T2/T3. It does not
allocate a new car. Reservation conflicts are rejected; new non-T2 AI routes
must be disabled until independently qualified. A33-record13-position trial
requires a complete order and the explicit33 profile; it is not unrestricted
capacity. The author compiler and CMD packaging path are reused.

Configured-order packages refuse active saved championships. Test only fresh
competitions and disposable candidate saves; do not copy trial state back to
retail. V-DEF3's SDK SLOT32 vehicle is a technical retail Wildcat clone, not the
restored Demo TOMCAT. See `docs/sdk/V_DEF3_ROSTER_ORDER_RESULTS.md` for the private
CMD and owner selection/Results/re-entry/save checklist. Offline PASS is not
D3D8 gameplay qualification.


## Historical ratings and brighter generated icons

Vehicle Details now exposes Speed, Acceleration, Handling and Endurance as four
integer display ratings0–10. They affect only native frontend records. The
inspector labels ORIGINAL_CATALOG, CUSTOM or SDK_PLACEHOLDER and retains the
original evidence. Undo/Redo and Restore baseline ratings do not retune physics.
See docs/sdk/DEMO_FRONTEND_STATS.md; missing retired RAV4/Alpha values are not
inferred from Newrav.

Generate vehicle art uses mr-native-v2: brighter studio fill/softbox highlights
for complete eligible source material groups, with the preserved flat side
orthographic miniature view. The large rotating frontend and ordinary 3D source
preview are unchanged. Generated highlights approximate icon presentation;
they are not recovered original MR reflection/shader behavior. Source textures,
models and original artwork remain intact. Existing explicit v1 recipes still
compile. Compare generated images before Apply; applying to a derived project
supports normal history, Restore and deterministic native UI compilation.

V-DEF4.1 keeps TOMCAT's authentic historical Vehicle Select CarSheet. Its separate
race smallcarsheet is RECONSTRUCTED as a flat side32×16 mr-native-v2 image; the
old isometric image remains in heritage storage. Other accepted artwork stays
unchanged. See docs/sdk/V_DEF4_1_FINALIZATION.md for the current CMD and checklist.

In Vehicle Details / Race HUD, choose HISTORICAL, AUTO_DOMINANT, AUTO_AVERAGE or
MANUAL. Recalculate reads exterior model materials and area-weighted UV texture
usage; it shows dominant/average and several livery swatches, confidence and
limitations. It does not replace a manual choice. Select a swatch or type HEX/RGBA
to enter MANUAL, then Apply. Optional contrast gently lifts a dark automatic/manual
choice; HISTORICAL retains original floats. Preview uses the local shared HUD
image without changing it. Verified-history reset is available only with genuine
source evidence. Source policy/result survive build, history and reopening.

Native addon AI flags apply only to new mode-owned rosters. T1/T2/T3 support
Quick Race, Cup and Master Rallye; ordinary T3 also supports Invitation. Leave
Challenge/Practice excluded. Physical CarIDs are independent of display order.
Existing saved participants are not rewritten. Use disposable candidate saves for
owner tests and observe known Randomizer F3 Challenge conflicts. No DLL installer
or tyre setup screen is required or introduced here.


## In-game Setup pilot (V-SET1)

V-DEF4.1 above is now owner-confirmed. Vehicle Studios → In-game Setup pilot
opens separate package authoring, without editing the open vehicle. Select the
qualified PS2 assets, retail unpacked folder, accepted renderer sources, accepted
CMD candidate and original game root. Save/load an independent setup recipe;
build creates a fresh private host and keeps all installed files unchanged.

Launch its CMD in windowed mode. Select SCHLESSER BUGGY 1997 in single-player
Quick Race; on Vehicle Setup/Gearbox press F6. Choose original PS2 or reconstructed
PC sponsor panels, Stock or retail gravel. Apply persists; Defaults is a draft
until Apply; Cancel retains previous choices. Stock passes native selectors
through unchanged. Controller POV/button support requires owner testing; keyboard
F6 entry is required. This is an owned modal, not a new fullscreen MR screen.

Do not edit linked runtime resources. Use only the generated CMD; disable through
Enabled=0 in the private host/VSET1.ini, preserving the package marker. Saved
championships are not rewritten. New in-game behavior is pending owner validation.
See V_SET1_PILOT.md for scope, source boundaries and the exact checklist.

V-SET1.1 fixes an erroneous Quick Race rejection before race state is published.
Use the new scope-fix CMD; the previous launcher redirects automatically.
If refused, host/vset1-runtime.log now records the exact SCOPE values.
