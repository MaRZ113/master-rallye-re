# Human Runtime Handoff — J.1 Live Native Dump

## Candidate and safety boundary

Use the updated read-only Observatory package against the existing J.1
`--integrated` launch. Do not replace or edit `MRallye.exe`; the expected
on-disk SHA256 is
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` and size
is 3,121,214 bytes. The updated 0.2.2-beta package is installed in
`D:\Game\Master Rallye Pristine\MasterRallye-Observatory-0.2.2-beta` and its
14 release-manifest files were hash-verified after staging. The Observatory
process only queries the game and reads memory; it does not install hooks,
write memory, or alter game files.

## Test sequence

1. Launch the J.1 integrated process using the existing loader procedure.
2. From the Observatory folder, run
   `python mr_observe.py --verbose status` and select/connect to that running
   process if prompted.
4. Confirm the disk identity is pristine retail and the effective live
   `native_dump_walker` is reported as the approved J.1 hardened runtime
   variant. The details must include walker SHA256
   `16d85b7cae971b50f0ad1fd33425bae992cc758c0416c856199eb5ea3dfe2fe9`,
   StringList target `0x0068E6D0`, and XmlData target `0x0068E6F0`, with their
   expected trampoline hashes.
5. During a normal race, run
   `python mr_observe.py capture j1-live-normal-race`. Keep the generated JSON
   and raw `.dump.bin` pair together and verify the raw sidecar SHA256 from the
   JSON.
6. Confirm Broker state for physical ID26 Mercedes and ID27 R5VQualifier. Keep
   the Observatory loader/runtime attestation distinct from Broker evidence.
7. Only after Status confirms the in-memory hardened walker and
   `Native Dump from Race Results: verified safe.`, optionally run
   `python mr_observe.py capture j1-live-results` from Results. Otherwise skip
   the Results capture.
8. Exit the game normally. Rehash the on-disk executable; it must still equal
   the pristine retail SHA above.

## Expected provenance fields

- `image_sha256` and `image_size`: exact on-disk pristine executable.
- `module_base` and mapped image identity: exact verified PE mapping.
- `disk_broker_dump_variant`: `native_stock`.
- `effective_broker_dump_variant`: `native_hardened` only after full live
  verification; otherwise `unknown` or `native_stock`.
- `native_dump_post_results_safe`: true only for the verified J.1 in-memory
  variant; false for exact stock; null if not verified.
- `native_dump_walker_sha256`, `native_dump_walker_variant`, and
  `verified_trampolines`: process-memory evidence.
- `runtime_verified_capabilities`: passive Broker and native Dump attestations
  remain separate.

## Stop conditions

Do not request native Dump if Status says `not verified`, a hash/target differs,
the mapped base or size differs, or an unrelated Broker anchor fails. Passive
Broker capture may remain available under its independent gate. Preserve the
full error text and stop; do not use a bypass flag.
