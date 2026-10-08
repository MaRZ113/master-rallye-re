# J.1 loader decision

## Decision

Use a dedicated external x64 launcher that starts the exact x86 retail process
with `CREATE_SUSPENDED`, verifies the mapped process, writes the audited
retail-relative RVA operations as one prevalidated set, restores protections,
then resumes. Use an external, hash-pinned resource root as the process CWD for
the integrated launch. This is a research candidate, not a qualified product
loader. The human bootstrap and addon tests remain pending.

The source image is fixed-base PE32/I386, image base `0x00400000`, with base
relocations stripped. Therefore the launcher refuses any process whose PEB32
image base differs from the preferred base. It translates every patch file
offset through the audited PE section table and validates the mapped target as
part of the exact retail image before using the resulting RVA.

## Options examined

| Option | Evidence | Decision |
|---|---|---|
| Dedicated launcher / suspended process | MSVC x64 and Windows SDK are available. Windows can create the original executable suspended. The launcher can pin/hash the source file, check WOW64 identity and PEB32 image base, then install all audited ranges before the first user-mode resume. | **Selected for J.1.** It owns startup ordering and keeps the original EXE path intact. |
| DLL proxy/bootstrap | Current vehicle checkout contains no proven external proxy loader. It would compete with common D3D8, input, sound, and legacy wrapper names and could load after important native constructors. | Rejected for this phase. The design adds no proxy DLL and refuses integrated launch when common adjacent proxy names are present. |
| Existing project runtime mechanism | H.2/I.1 builders produce patched EXE research instruments; the former general-RE randomizer DLL is reached through audited patched-EXE seams. Observatory reads Broker state. None is an original-EXE bootstrap. | No reusable unchanged-EXE mechanism was found in the current vehicle checkout. Historical patched EXEs remain analysis inputs only. |

## Startup and failure ownership

Before spawning, the launcher verifies the exact retail hash/size, J.0 plan,
native manifest, RVP1 operation table, resource manifest, resource index,
all inventoried file hashes, and exact resource file set. The process is
created suspended from the original path. The launcher then checks x86 WOW64
identity, mapped path file identity, fixed base, mapped headers, and mapped
code sample. All operation preimages and page targets are checked before any
write. All page protections are prepared before the first memory write.

Any pre-write conflict aborts the child without resume. A failure after writes
beginning terminates the suspended child without resume; it does not try to
roll back bytes in a process that might have partially changed state. The
stock executable is held open with write/delete sharing denied and rehashed
after process exit. There is no on-disk patched image in J.1 output.

The no-op canary applies the identical bytes `File` to its exact mapped
`.rdata` location and restores the prior protection before resuming. It tests
targeting/write/readback mechanics without a gameplay mutation. It is not a
game-visible semantic hook, so it cannot substitute for human bootstrap or
addon validation.

## Resource root and compatibility constraints

The integrated launch sets CWD to the external bundle's `resource-root`.
That is the narrowest current overlay strategy: it avoids changing the retail
install and stages the exact verified Data.sma, loose family resources, and
native VehicleSelect XML. The earlier I.1 captures used an EXE and resources
co-located in one package; they do not distinguish executable-directory
lookup from CWD lookup. The effective root must be confirmed in a J.1 capture.

Changing CWD may also affect paths that the game treats as relative. The
previous I.1 package contains generated PlayerState files, but its EXE and CWD
were co-located, so that observation does not isolate which base directory
owns save paths. J.1 stages a fresh resource root without copying those
profile files; the external runtime folder is disposable test state. Do not
use a valued profile for the first integrated run.

The launcher scans common proxy names beside the original executable and
refuses the integrated path if any are present. It does not yet enumerate all
loaded modules, mediate arbitrary hooks, or prove coexistence with third-party
graphics wrappers. It does not hot-unload. Removal between runs means using
the original EXE normally and removing the generated J.1 launcher/bundle.

## Remaining uncertainties

1. Human-confirmed stock startup through `--bootstrap-only`.
2. Human-confirmed no-op canary launch and normal frontend.
3. Resource Root and resource lookup when executable path and CWD differ.
4. Save/profile path ownership when the process CWD is the external root.
5. Graphics-wrapper coexistence beyond the conservative adjacent-name check.
6. Actual ID26/ID27 in-memory materialization and gameplay under the original
   retail file path.

Until these gates pass, status remains
`READY FOR HUMAN RUNTIME`; no J.1 full-pass claim is made.
