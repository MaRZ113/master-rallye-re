# HUD-PORT1 — bounded live semantic join readiness

Status: **PARTIAL / CURRENT_STRUCTURAL_CANDIDATE_WITH_CAPTURED_NATIVE_DRAWS**. HUD replacement remains absent.
The original `gaHudAiSpeedDial` constructor/vtable evidence from
`semantic-mapping.md` is retained; this iteration adds no broad binary reverse.

## Established inputs and preserved boundaries

- Exact original PC PE: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- SpeedDial AI vtable `0x00690F38`; Egg AI pointer slots +4/+8/+C/+10.
- Native consumer Egg+4C -> packet; packet+8 -> content storage;
  packet+54 -> point; packet+68 -> mode. These offsets already belong to the
  frozen renderer's validated UI ownership observer; no new engine layout guessed.
- The existing F10 observer captures current native consumer scope, original
  packet identity, texture COM generation, race generation, UI epoch and draw
  signature at original consumer return RVA `0x16D7C4`, FVF `0x142`.
- Target Trace automatically requests the existing UI ownership observer. There
  is no new option, hook, native renderer read, draw override or build seam.

No MRallye process was running when the new helper was prepared. Recent logs
are previous PID lifetimes. Their pointer values must not be dereferenced in a
new process, even if addresses happen to recur. No live join is claimed.

## Smallest read-only control

Use the accepted DLL and existing Trace/F10 diagnostics. Keep HUD visible (H
must not hide it), enter Turkey3, and capture one F10 frame with no restart,
course change or exit afterward. Root runs the helper immediately (within 60s):

```powershell
python ps2-research/pc-port/docs/hud-port1/live-semantic-probe.py `
  --pid <current-MRallye-PID> `
  --frame 'D:\Game\Master Rallye Pristine\MRRRenderer\logs\frame-<PID>-d1-<FRAME>.jsonl' `
  --output 'ps2-research/data/rigid-port1.2/hud-speed-dial-current.json'
```

This is an executed-tool recipe, not a completed live test. No automatic game
launch or debugger attachment is performed. The helper opens only
PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ; it reuses the existing
exact PE/hash/loaded-base checker and per-sample 64 KiB ceiling.

It requires one complete same-frame certified race F10 roster, rejects
suppressed HUD packets and mismatched packet/mode/storage, and reads at most
64 distinct entities. For each, four AI slots, class vtables and packet tuple
are revalidated after the bounded read. Multiple SpeedDial candidates fail
closed rather than being arbitrarily assigned to the current player.

Output carries frame/PID creation identity, proxy hash, capture race generation,
UI epoch, texture pointer/generation and original draw metadata. It never
relabels AI+0C or another unproved field as image bank index0.

## Meaning of a positive result

`CURRENT_STRUCTURAL_CANDIDATE` proves only that a currently readable Egg from
that fresh captured roster still has the SpeedDial class fingerprint and the
same packet/storage tuple. It does **not** prove an atomic same-frame current
race generation, exclude ABA pointer reuse, identify the current player's HUD,
or prove native bank0 plate selection. No replacement gate is opened.

To strengthen this to a draw-time join, use explicit user-assisted debugger
pause/logpoint at the already verified `0x0056D110` consumer, filtered by the
candidate Egg identity with current AI vtable revalidation; observe the current
packet and original return without calling the engine. Preserve original
thread/race/UI epoch and reset/lifetime context. Historical Egg addresses cannot
be reused as a future-session filter. Do not add a global/per-frame UI logpoint.

## Independent gate report

| Gate | Result | Reason |
|---|---|---|
| Native class fingerprint | PASS | Prior exact original instruction evidence retained |
| Current Egg/AI slot join | PARTIAL | Helper ready; live process/capture pending |
| Packet identity and draw ownership | PARTIAL | Existing native-scope F10 contract; no new current join |
| Current player HUD ownership | BLOCKED | SpeedDial class alone does not select player/lifetime |
| Image bank0 | BLOCKED | Authored XML index0 known; native selection offset unproved |
| Plate texture / geometry | BLOCKED | Draw texture generations known in F10; bank/plate-specific resource join missing |
| Lifetime / reset authorization | PARTIAL | Stale process and changed tuple rejection; no atomic native generation read |
| HUD replacement | NOT_PERFORMED | No replacement source/config/integration added |

## Focused validation

`python ps2-research/pc-port/docs/hud-port1/live-semantic-tests.py -v`:
**8/8 PASS**: exact class, wrong class, changed owner, changed packet, changed
storage, ambiguous candidates, missing complete frame, wrong executable.
These are synthetic structural checks, not original HUD runtime confirmation.
The frozen renderer, overlay, accepted DLL features, once-per-frame HUD context
cache and canonical `.build/` roots are untouched.

## User-assisted runtime result — 13 October 2026

The initial frame2468 was already older than60s and was rejected before any
process opening. The user then produced fresh frame35007 and stayed in the
same Turkey3 session. Exactly **one** bounded read-only process observation
succeeded, PID48104, original PE hash above, accepted DLL hash
`6edc2426e2602545121f16959cdbb2055fb205a907b36173cb85a447b7051deb`.
Total process bytes read: **5996**, including the original loaded PE header.
No further process samples were taken.

The fresh F10 captured32 distinct current UI entities and268 original UI draws
without drops. One entity had AI slot0 vtable `0x00690F38` and retained its
packet/storage/mode and AI identity across double reads. Captured race
generation6 / UI epoch2 are preserved with their explicit non-atomic limits.

Its packet's two original `DrawPrimitive` submissions are:

| Capture UI sequence | Global trace sequence | Native arguments | Stream0 generation | Stage0 generation |
|---|---|---|---|---|
| 95 | 656 | `(4,15220,1)` | 603, stride24 | 799 |
| 96 | 657 | `(4,15223,1)` | 603, stride24 | 799 |

Both return HRESULT0 and FVF0x142. The traced world translation is
`(565,75,0)`, independently consistent with original PC `Hud0.xml` SpeedDial
placement. The correspondence uses captured current Egg/packet/class plus a
complete268-record consumer-return-filtered order join; it is **not** a future
classifier based on those historical ordinals, addresses or screen position.

**Evidence: CONFIRMED_BY_RUNTIME** for the read-only structural observation and
original captured native draws; **STATIC_INFERENCE** for naming the combined
non-atomic observation an original SpeedDial plate candidate. Bank0 runtime
selection, original quad XY/UV contents, current-player resource ownership and
restart/reset lifetime are not proved. The two one-triangle draws are a useful
plate geometry lead; absent vertex bytes must not be invented.

Compact identities and frame/snapshot hashes are in `live-evidence.json`; full
raw source capture and passive snapshot remain local/ignored. HUD replacement
remains blocked pending the exact bank0/plate resource join. No DLL, source
asset, overlay patch or frozen renderer changed.

Updated tests: **13/13 PASS**, adding certified current roster, generation
mismatch, suppressed HUD, capture overflow and unknown race-context negatives.
