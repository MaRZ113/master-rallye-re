# R-OBS3 runtime handoff

## Package

The separate internal package is generated under ignored
`.research-output/general-re/observatory-research-r-obs3-final/`. Start it with
`MRallye-Observatory-Research.cmd`. It does not contain an executable or game
assets. Keep the original candidate executable in its existing isolated game
copy; the Observatory reads its identity and process memory only.

The supplied R5V-H forced-ID26 proof executable was audited from the actual
file. Its SHA256 is
`688653245b916ae7aae2a8e22fd47e76963f3afb1c23936b47b57bb40c76f0c5`; the
handoff's expected `dc821c09…` digest did not match that file. The actual file
passed all ten retail Broker-family anchors and the independent `merc-id26`
registry fingerprint. Confirm the candidate you intend to test before launch.

## Active-race capture smoke

1. Launch the exact audited AI candidate, then enter an ordinary active race
   with the forced Addon/Mercedes AI behavior. Keep the executable path
   unchanged while it runs.
2. Run the package launcher with that exact executable path:

   ```text
   MRallye-Observatory-Research.cmd --exe "<path-to-MRallye.exe>" status
   ```

   Confirm the resolved SHA, family, and capability matrix. The actual AI build
   should show Broker read and native Dump enabled, with post-Results Dump
   safety disabled for the stock walker.
   Expected: the selected process resolves as locally audited with Broker read,
   Broker Editor, and native Dump enabled; its registry is `merc-id26` and
   post-Results Dump safety is disabled for the stock walker.
3. While the race is active, request the native Dump using the same path:

   ```text
   MRallye-Observatory-Research.cmd --exe "<path-to-MRallye.exe>" capture forced-id26-ai-race
   ```

4. Confirm the capture JSON and raw sidecar are written below
   `.research-output/general-re/broker-observatory/captures/` and that metadata
   records the locally audited profile, family, capabilities, and runtime
   anchor checks.
5. Confirm metadata says `profile_origin=locally_audited`,
   `compatibility_family=retail-broker-v1`,
   `vehicle_registry_profile=merc-id26`, and the expected live anchor checks.
   The game capture should contain the expected ID26 race state; that semantic
   check is separate from Observatory compatibility.
6. For a degraded build, separately verify that passive recovery remains
   available while unsupported native commands are rejected. Do not use the
   stock Results Dump path after Race Results; this candidate's Dump walker is
   not NULL-safe.

The human result should report whether status resolved the expected running
process, whether a capture pair was written and integrity-checked, and any
capability mismatch. This handoff does not claim that runtime validation has
already occurred.
