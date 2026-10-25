# Engine capacity: confirmed observations and limits

Target retail EXE: 3,121,214 bytes, SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
REA/Ghidra recovered assembly/pseudocode, not original source. Private
`evidence/registry-callers.json` retains34 direct callers and REA evidence IDs.
That does not exclude indirect/cached-pointer consumers.

| Retail VA | Observation |
| --- | --- |
| `0045A3C0`, allocation immediate `0045A3E0` | Singleton, original `new 0xC00` |
| `00458CD0`, destructor `00458E00` | 26 records stride34h at+4; 39 RaceTest rows stride2Ch at54Ch |
| global `006F5ED4` | Three direct allocator xrefs; cached uses remain possible |
| `00480A20` | Frontend class counts at+20/+24/+28: 7/7/11 |
| `00481E20` / `00481E50` | Dense class/global mapping, thresholds7/14; no universal ID27 upper guard observed |
| `00481F50` | Navigation reads class count |
| `00481950` | Publishes12 UI position keys; key buffer is not a12-record vehicle array |
| `0044A510`, `0044ED50` and callers | Family/colour accesses at record+24/+28 using52-byte stride |
| `0047C840` and adjacent Results consumers | Smallcarsheet index at record+20, participant index separate |
| `0045A150` | Unlock switches on physical ID using stock progression gates |

Generated extension updates allocation, construct/destruct/unwind counts/bases,
39 RaceTest initialization displacements and11 secondary consumer displacements.
It chains the existing initializer and maps, preserves stock fallbacks, and
extends display/Results, sound-profile and unlock routes. Physical identity stays
distinct from class-local ordinal, driver selector and sound-profile ID.

Three T2 AI loops retain native append/exclusion bodies, feeding new eligible
IDs once after ID27 and restoring the stock sentinel. Participant allocations
and race field sizes are not increased. Authored Challenge/Practice rosters
are not automatically rewritten.

## Engine versus tooling

- ID28 rejection belonged to the previous SDK profile. New routing for28–31
  passes offline CPU checks; this is not yet native gameplay confirmation.
- Existing cave storage fits one new row, then runs out. Private backend
  reserves64KiB at10000000h; the30-record payload uses1341 bytes,32 uses2443.
  It refuses occupied memory or relocation. While suspended: reserve RW, write,
  read back, protect RX, flush instruction cache; failure terminates the child.
  No file-backed game EXE is emitted or modified.
- Current UI admission is twelve slots/class. T3 already has12; further T3 is
  rejected. T1 beyond8 is not packaged/qualified; scene and new AI templates are
  T2-specific. Three times12=36 is only arithmetic, not a qualified global layout.
- Lifecycle emitter count<128 and bank parser max128 frames are SDK bounds.
  32-bit count/ID storage alone gives no safe capacity claim. No universal
  theoretical engine maximum is established.
- New storage extends an exact28-record pinned parent. This is a bounded
  implementation, not arbitrary runtime relocation or unlimited registration.

## Remaining audit and save boundaries

SavePlayerState publishes numeric selected-car fields. No all-car unlock
bitset limiting IDs to28 was demonstrated. Binary save serialization, campaign
progression, persisted competition participants, network encoding, every fixed
array and all indirect registry users have **not** been exhaustively qualified.
Stable reservations prevent silent ID reuse, but do not establish compatibility
with old saves. New candidates therefore use independent disposable state.

Maximum previously gameplay-qualified layout remains28 records (8/8/12);
new29/30 bundles and29–32 helper checks have separate offline evidence levels.
The12-position publisher bound and code-cave exhaustion must not be advertised
as engine limits. Higher gameplay capacity requires the complete human lifecycle
test before promotion of the default capability profile.

Reusable: stable reservations/tombstones, deterministic explicit/automatic
allocation, resource ownership, bank rebasing, generated helpers, sealed profiles
and optional process allocation. Bounded canary pieces: frozen parent, retail
fingerprint,12 UI positions, stock-ID10 unlock oracle, existing T2 AI owners and
Navara/T2 XML template. Arbitrary converted resources still need author-build
integration; old runtime-prepare remains explicitly reference-bounded.
