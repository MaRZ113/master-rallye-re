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
