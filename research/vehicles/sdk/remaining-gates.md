# Remaining gates after J.2 two-addon runtime qualification

R5V-J.0 is accepted as the offline manifest/compiler foundation. J.1 is
closed with human runtime evidence for the byte-unchanged retail executable
and external integration. J.2 is **FULL PASS / CLOSED**: the supplied capture
batch confirms dual-addon SplitScreen and Cup/Master persistence; the owner
confirmed the corrected ID27 re-entry candidate in human runtime. See
[`j2/closeout-2026-10-09.md`](j2/closeout-2026-10-09.md).

## J.3 productization work

J.3-A offline authoring/compiler work is implemented: project initialization,
VehicleProject validation/build integration, deterministic asset staging,
exact-retail DataGame physics-family cloning, and an independent third T2
manifest. Preserve the exact mapping invariant
`local_field_offset = 0x14 + 4 * class_id` in generated sparse reverse maps.
This output remains an offline build with `runtime_installable=false`.

J.3-B now has a bounded collection compiler and static launcher preflight for
exactly the ID26/T1 plus ID27/T2 layout. Its GlacierSprint bundle is
`READY_FOR_HUMAN_RUNTIME`, not runtime-qualified. T2-only input is explicitly
rejected; other layouts remain unsupported. The J.0 offline artifact continues
to report `runtime_installable=false`.

J.3-C and public SDK release are not started. Only the exact ID26 Mercedes and
ID27 R5VQualifier identities have runtime qualification. See
[`j3/release-boundary.md`](j3/release-boundary.md) and
[`j3/plan.md`](j3/plan.md).

## Already confirmed by the supplied 2026-10-09 evidence

All 19 JSON/raw pairs and raw sidecar SHA256/length fields were independently
verified from the supplied archive. The batch confirms:

* ID26 Mercedes and ID27 R5VQualifier as independent human participants in one
  SplitScreen race.
* Rallye Cup RACE 1/3 -> RACE 2/3 with the same roster, including ID27 / native
  DriverID 7.
* Master Rallye stage 0 in PID 42244 -> stage 1 in fresh PID 41800 with the
  same native roster, including ID27 / native DriverID 4.
* The approved hardened live Dump walker in every capture.

The owner's stock launch without the loader is recorded as
`HUMAN_CONFIRMED_UNINSTRUMENTED`; there is no new instrumented stock-launch
capture. See [runtime evidence](j2/runtime-evidence.md) and the
[machine-readable report](j2/runtime-evidence-2026-10-09.json).

The J.2 candidate has a separate exact-build native launcher trust profile.
It passed static verification and owner human runtime testing. The historic
candidate profile retains its generation-time qualification field; see the
J.2 closeout for the later human report provenance.

## Profile and removal notes

The J.1/J.2 process working directory is the external `resource-root`, so
game-generated profile state is expected under that root's `DataGame` tree.
Keep `PlayerState.xml`, `PlayerState.xml#`, and `options.xml#` when disabling
the loader. No hot-unload is supported. Normal removal occurs between runs by
starting the original EXE without the loader; leave the external resource root
and saves in place. The original installation and executable are not modified.
