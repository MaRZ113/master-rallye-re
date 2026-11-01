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
for complete eligible source material groups, with a separate three-quarter
orthographic miniature view. The large rotating frontend and ordinary 3D source
preview are unchanged. Generated highlights approximate icon presentation;
they are not recovered original MR reflection/shader behavior. Source textures,
models and original artwork remain intact. Existing explicit v1 recipes still
compile. Compare generated images before Apply; applying to a derived project
supports normal history, Restore and deterministic native UI compilation.

The TOMCAT pilot uses recovered original blue CarSheet/HUD artwork rather than
replacing authentic images with generated ones. Accepted RAV4/Forester files
remain untouched. Private v1/v2 and same-car original-art comparisons are linked
from docs/sdk/V_DEF4_TOMCAT_RESULTS.md. Launch only the final isolated CMD for
owner D3D8 testing; no automatic new AI entry or full-game success is claimed.
