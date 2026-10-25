# Offline validation and human handoff

## Passed

- Focused SDK/GT4/Subaru regression suite:231 tests,230 passed, one skipped old
  private fixture (`test_stock_profile_preserves_tyre_and_refuses_second_pass`).
- Frozen Subaru semantic plan reproduces byte-exact:
  `e5ee7bc3c0eae64bc6bbb817ab3c23c0d7a8a3577552d83d73e27d22669dfafe`.
  All190 immutable resources of the frozen bundle rehashed successfully.
  Existing user-editable options/state were not overwritten or copied as saves.
- Final29 bundle:291 resources. Final30:391. Each preserves185 immutable parent
  resources exactly; five shared XML/bank files are explicit composition outputs.
  Existing bank records, Subaru textures/models, donor originals and physics
  values stay intact. Each new family has98 genuine stock DX/DXT resources plus
  its own two UI textures. DX parse and texture format validation pass.
- Both sealed bundles independently re-derived and launcher-built. Native
  `--verify` and `--verify-launch-environment` pass against the original EXE and
  the approved existing graphics proxy. Legacy profile rebuilt/preflighted too.
- Final30 Windows allocation self-test passes RW write/readback, RX protection,
  cache preparation, cleanup and occupied-address rejection. No payload was
  executed; no game process was created. This is not a target-process ASLR test.
- Separate disposable fixture rejects modified-hash, truncated and missing
  native-extension.bin. Restoring it passes. Candidates were never modified.
- 29–32 record resource derivations and CPU-helper emulation pass. All stock
  and existing addon forward/reverse maps are covered. Generated initializer
  destinations, stack ABI, three T2 AI chains, every display bridge, Results
  literals, unlock mirror, locked reason and audio argument cleanup are checked.
  Native allocator/Broker/string/audio/unlock/append bodies are mocked.
- Final Lancer qualification decodes30/30 menu body,93/93 race body,2/2 menu
  wheel,10/10 race wheel. Header counts match. Three packet-local shared DX/DXT
  probes validate; four-view diagnostic previews remain explicitly partial.
- Original EXE SHA256 remains
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`;
  d3d8.dll remains
  `eb7ea3d9501b514bff668f1e75e86041906c5fe4e8afa89f06d658751429aaf4`.
  All four original GT4 inputs retain their recorded hashes.

Private evidence: `.research-output/vehicles/scale1/evidence/` includes
`regression-tests.{json,txt}`, `final-preservation.json`,
`capacity-final-increments.json`, `emulation-final-29..32.json`,
`native-payload-negative-tests.json`, `legacy-launcher-regression.json` and
`gt4-final-summary.json`. Each final candidate has its own `validation.json`.
Raw native dumps, CORE/ELF, intermediates and textures stay outside review ZIP.

## Ready for human testing, not newly gameplay-qualified

Start final29 first using its HANDOFF. It contains unchanged Subaru and a
clearly named stock Navara capacity probe atID28/T2local8. If it passes, try
final30 separately (ID28/29, T2local8/9, private code block). This second profile
tests both an extra row and the new code-storage backend; it does not isolate
those variables. If it fails, retain its log and test the one-row private
profile through the reproducible builder/emulator helpers before diagnosing
the higher count. No user-save migration is implied.

Required human observations: all class navigation/bounds, Subaru and probes,
both player selection actors, race resource loading, eligible AI, stock/subaru
Results names/thumbnails, return/re-entry, reflections enabled/disabled and
bundle-local state restart. Campaign progression, persisted competitions,
networking, rare rollback/error paths and full indirect native consumers remain
unqualified. Never infer safe gameplay32 from emulated helpers or catalogue
growth from an unchanged race participant count.

## Deferred

Lancer assembly/material gates are in gt4.md. There is no complete Lancer
car.dx/complete.dx/wheel family or combined Subaru+Lancer runtime package yet.
This checkpoint ends at a validated **capacity** candidate requiring human game
evidence. It is not a claim that every SCALE1 objective has been achieved.
Physics tuning, race wheel placement, T1/T3 expansion, default-profile promotion,
save migration and a general arbitrary-roster installer remain future work.
