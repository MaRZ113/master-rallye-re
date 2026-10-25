# V-FIT4 FIX1 — whine crash and shadow admission

Two implementation defects were missed by the previous offline tests.

1. Windows WER reports EIP1001296A and10012A29 inside whine map writes.
   The launcher protected the entire extension RX. The fixed layout places
   map/cursor in a separate sealed4096-byte page, admitted RW/NX by the trusted
   profile. Code remains RX. Old RX policy now reproduces WRITE_PROT in replay;
   fixed replay uses real page protections, unmapped page zero and deliberately
   clobbered volatile registers in native-service stubs.
2. The shadow guard compared serialized bounds against an incompatible native
   layout. The loader removes marker1339 and adds radius-squared. The corrected
   guard compares the actual44-byte loaded structure. Original loader instruction
   replay now precedes admission/arithmetic checks, rather than constructing the
   previously assumed header in a stub.

Details: [whine](whine.md), [shadow](shadow.md).

## New candidates

- `.research-output/vehicles/vfit4-fix1/candidate/Launch-Vehicle.cmd`
- `.research-output/vehicles/vfit4-fix1/candidate-no-whine/Launch-Vehicle.cmd`

Old candidates are preserved. Both new bundles pass all launcher preflights;
main allocation test verifies offset77824/size4096 is RW/NX. All235 declared
resources of the main candidate are unchanged, as are all234 in the audio A/B.
Physics, geometry, collision, wheel attachments, engine, UI and the intended
shadow footprint are unchanged. Original EXE/DLL SHA256 still match.

699 synthetic tests: zero errors/failures, one skip. Whine replay28 cases;
shadow replay58 cases plus original bounds-loader replay. Evidence and Windows
crash records are private under `.research-output/vehicles/vfit4-fix1/`.

The game was not launched. Actual race loading and shadow appearance still need
human confirmation. Test the no-whine build first for shadow admission, then
the main build on a stock car and Lancer; include another race entry. Previous
synthetic success did not establish gameplay safety, and the updated results
also remain offline qualification.

No commits, push, publication or original executable/graphics DLL modifications.
