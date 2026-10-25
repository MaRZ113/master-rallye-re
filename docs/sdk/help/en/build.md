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
