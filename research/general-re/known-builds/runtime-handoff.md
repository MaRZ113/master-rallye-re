# Exact widescreen/freeze profile — observation only

Runtime evidence: **CONFIRMED_BY_RUNTIME / PASS**, from the owner's exact-build
report: Status identified retail-widescreen-freeze; patched-front-1/2 diff with
revision-only hidden showed zero Added, Removed, Value changed, Metadata changed
and Revision-only. This does not authorize arbitrary patched EXEs, persistence
operations or editor editing. The completed observation plan is retained below.

1. Use a disposable installation with the supplied exact executable, named
   MRallye.exe. Verify SHA256
   `bcf310a79133b03aa89ce51197a37516ee27c1b0e9da19788519e849e7a2f2f6`
   and size 3117118. Preserve the supplied original; do not run either patcher.
2. If needed, enable the existing Menues/Enabled=True setting in loose dev.xml
   using the established quickstart procedure; preserve a backup.
3. Launch that game, then run `python tools/runtime/mr_observe.py` from this
   research checkout. If multiple known instances run, explicitly select its PID.
4. Status must show **retail-widescreen-freeze**. Unknown EXEs must be rejected.
5. Capture `patched-front-1`; observe Broker auto-open and the original Dump.
6. Capture `patched-front-2` without otherwise changing frontend state.
7. Diff Last Two and choose to hide revision-only changes.

PASS requires a fresh complete Dump, normal timeout recovery if needed, paired
JSON/raw publication and a semantically stable second snapshot. Verify source
build_profile_id, image SHA256/size, sink pointer/vtable and freshness proof in
both JSONs. Record actual outcomes and any new differences; do not call unexpected
differences normal without evidence. The tool performs no process writes,
injection or EXE modification. Exit Observatory and the disposable game normally.

Flow Builder is intentionally not enabled for this profile in this task. No
additional developer commands, Save, Commit, Build or broker edits are allowed.
The published v0.1.0-beta ZIP remains pristine-only; use the research source here.
