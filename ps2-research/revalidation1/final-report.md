# PS2-REVALIDATION1 final report

Phase: PS2-REVALIDATION1  
Repository: `D:/Game/Master Rallye/master-rallye-re-general`  
Branch: `master`  
Starting HEAD: `61cb84d5c7f28d3bd88a3f1f9a8ce16d4c178390`  
Ending HEAD: unchanged at `61cb84d5c7f28d3bd88a3f1f9a8ce16d4c178390`  
Preflight: existing user changes only under `ps2-research/pc-port/`; preserved  

Canonical PS2: four input hashes match  
PC executable: pristine `MRallye.exe`, `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`  
REA: connected, agents 6.4.0; Windows Ghidra 12.1.4  
REA PS2 support: current provider rejected R5900 ELF  

France1 PS2 `bush01`: PSM node `3,509,209`, material `3,509,264`, 24 source faces  
France1 PC counterpart: DX draw 54 / `course.batch.1.21`, core `3,261,170`, 48 records / 24 unique unsigned faces  
Geometry relation: strict source match 24/24  
Texture relation: different images/resolutions/alpha distributions  
Live D3D8 identity: user-reported previous capture; raw trace absent  
Four-mode outcome: user-reported; raw screenshots/logs absent  
Root cause: unresolved; disabled depth write is a plausible contributor  

Focused tests: 30/30 foliage source; 8/8 port integration; 1/1 focused CTest  
Proxy verification: both existing DLLs PASS  
Builds: prior overlay report PASS; not rebuilt during this documentation audit  
pytest: unavailable in active Python; no package installed  
Renderer baseline: unchanged  
Course SDK: unchanged  
Corrections: none  
Commit / push: none / not performed  
Overall: **REVALIDATION_PARTIAL_PROVIDER_LIMITED**

## A. What REA contributed

REA connected and usefully analyzed the hash-verified original PC PE. It
decompiled the material selector at `0x00580360`, the base-family shader
registrations at `0x00565DA0`, and D3D8 state wrappers. It verified that the
selector reads runtime flags and resolves the base, alpha and alphatest
variants. See [the executable audit](elf-audit.md) and its preserved REA
evidence IDs.

REA did not analyze `SLES_509.06`. The configured Windows provider rejected
the 32-bit MIPS R5900 ELF with `capability_unavailable`; generic MIPS/ELF
support is not enough to claim this console CPU is supported. The prior
canonical ELF work remains historical executable evidence, not fresh REA
output. This limit is documented in [tool readiness](tool-readiness.md).
As a separate provenance check, the original ELF header and `PT_LOAD` were
parsed and all 620 archived TREEBLEND1 instruction words plus 10 data anchors
were matched to their canonical file bytes. This checks byte identity and VA
mapping; it does not decode the instruction semantics anew.

## B. TREEBLEND1 findings

No proven TREEBLEND1 implementation error was found. Prior evidence still
supports the important mode distinction: `tree` uses alpha cutout and permits
depth writes; `treeblend` disables alpha test, enables the GS blend equation
`(Cs-Cd)*As/128+Cd`, and masks depth writes. It selects GEQUAL but inherits
depth-test enable and other state. These conclusions are prior ELF evidence;
the R5900 code was not independently re-decoded through REA in this audit.

The queue drain evidence proves only that bucket 0 precedes bucket 1 inside
one drain. It does not prove global ordering or distance sorting. GS alpha
input, TEXA, frame context, PABE, dynamic texture state and live VU residency
remain unresolved. See [GS state audit](gs-state-audit.md).

## C. PC material and source correspondence

The original PC selector and shader family are independently supported by
REA. The France1 PSM material at offset `3,509,264` names `treeblend`; its PC
compiled counterpart names `tree`. The 24 PS2 visual faces match all 24
unique unsigned faces in the PC record at the strict source tolerance. The PC
record contains 48 winding-specific triangle records; it is not twice the
surface count. This is source-geometry evidence, not runtime identity proof.

The source images differ: PS2 64×64 with 89 stored alpha values, PC 128×128
with 15. Stored alpha does not determine final GS/D3D alpha consumption. The
pilot leaves the stock PC texture bound. See [geometry](geometry-identity-audit.md),
[texture](texture-alpha-audit.md), and [PC material](pc-material-audit.md).

## D. PILOT1.3 runtime review

Earlier live results and the new four-mode qualitative outcomes are user
observations. Raw F10 logs, screenshots, and per-mode capture metadata are
absent from this checkout. I did not manufacture a capture or promote the
reported target identity and state restoration to independently confirmed
runtime evidence.

The reported outcomes make disabled depth writes a plausible primary reason
for the bush disappearing: mode 3 changes only depth writes and reportedly
shows the disappearance, while mode 2 preserves PC depth writes and remains
visible as white cards. But the data does not identify a specific later
occluder or rule out alpha/texture-stage interactions. Mode 2 changes alpha
test and blending together, so its white-card artifact is not attributed to a
single alpha state. The current cause remains unresolved.

## E. Cross-phase review and corrections

The bounded audit of WATER1, REFL1, GRASS1, GEOM1, DRESSING1, AMBIENT1,
AMBIENT2, RIGID1 and the PC port found no source-level contradiction that
justifies changing those phases. Existing evidence boundaries remain: source
surfaces are not live visible draws; grouped mesh records are not object
populations; static owner/update chains do not prove live poses; and
unexecuted VU contracts do not prove runtime residency.

No historical code or research claim was changed. This report only qualifies
the evidence source at PC VA `0x005867a0`: REA maps it to the PE, but Ghidra
has no defined procedure there. A second decoder (GNU objdump) confirms the
instruction-level generic state branch from original bytes. The raw pilot
claims are explicitly kept at user-observation grade.

## F. Validation and handoff

The canonical source hashes, 30/30 focused foliage tests, 8/8 PS2 port tests,
focused CTest 1/1 and both proxy verification checks passed. The existing
build report records both Release builds as successful, but no build was
rerun for this documentation-only audit. `pytest` is unavailable in the
active Python environment. Full results and exact commands are in
[validation](validation.md) and [command log](command-log.md).

The deterministic compact archive is written to the ignored local path
`ps2-research/data/revalidation1/PS2-REVALIDATION1-handoff.zip`; its SHA-256
is printed by `package_handoff.py` and saved beside the archive. The archive
contains reports and compact metadata only, not proprietary binaries, PSM/DX
geometry, or images.

## G. Decision

**Overall status: `REVALIDATION_PARTIAL_PROVIDER_LIMITED`.** REA was useful
for the PC PE but could not independently inspect the PS2 R5900 ELF. Raw
PILOT1.3 runtime artifacts are also missing, so the runtime hypotheses cannot
be resolved in this audit. No speculative correction or renderer change was
made.

The one recommended next action is the alpha-test-only **PILOT1.4** experiment
described in [next.md](next.md). No further phase is started here.
