Phase: PS2-REFLECTION-PORT1.1 — audited mixed-source iteration
Repository: D:/Game/Master Rallye/master-rallye-re-general
Branch: master
Starting HEAD: 3f837f4ddcb27ee1034a4b0753634c92009360ec
Ending HEAD: unchanged; no commit of pre-existing uncommitted work
Preflight: six pre-existing modified port docs and existing untracked port/revalidation files preserved
Frozen renderer tree: 7f9f5a7d9464b7b86ff09a9bf6c34b7ce341682d; source unchanged
Target: original Tata car.dx record19, hood AND roof regions;55faces/48vertices
Classifier: unchanged; exact geometry/current generations/live owner/native material
Source image: verified original ENVSOURCE64X64; private local GXI, not bundled
New source: Mode4 weighted ENV plus flipped live PC framebuffer
Dynamic target: private64x64 A8R8G8B8; one bounded copy per eligible frame
Timing: before first verified target draw/frame; explicit difference from PS2 after-model/pass update
Coordinates: original PC camera-space normals and texture matrix preserved
Native draw: one original55-face draw, original HRESULT
State restoration: masks1/2/3 plus retained capture transaction; attempted failure rollback/repair
Reset: DEFAULT resources released before real Reset; echo preserved
Foliage/PixelProbe/CourseObjects defaults:0/0/0
Reflection default:0Stock
Build: baseline and PS2 Win32 Release PASS; serial --parallel1
CTest: baseline24/24;PS2 29/29 PASS
Python:44/44 PASS;0FAIL/0SKIP
Generator: exact patches and repeat generation PASS
Exports: both DLLs PASS
Compileall/diff-check: PASS
Baseline DLL SHA256: f2fe1625fc1b5db56712cb41bb905e456a104ba6b534505afe8a01740cbb10c8
PS2 DLL SHA256: 645a1104e1f73ba1478125d25766291ce1951b84be21e90baf12a3dcf9c960f2
Prior Mode1 runtime: technical success confirmed by supplied original F10/logs
New Mode2/3/4 runtime: NOT_PERFORMED
PS2 visual parity: NOT_ESTABLISHED
Original assets/Course SDK: unchanged
Commit/push/automatic deployment: none
Overall status: IMPLEMENTED_PENDING_USER_RUNTIME

The audit is accepted as technical runtime success for the previous static-only
pilot. It demonstrated warmer/darker hood/roof, not PS2 parity. Independent
component/projection analysis supports the scope correction: compiled record19
contains28 hood-region and27 roof-region source faces. See runtime-audit.md and
body-panel-components.json; semantic projection remains STATIC_INFERENCE.

This iteration separates image replacement from COLOROP, and implements the
missing framebuffer image term for that same proven material. Modes0–4 are
Stock, previous static+ADD, static image only, ADD only, and mixed-source+ADD.
Their actual override masks are0/3/2/1/3. Mode3 needs no private image. Unknown
build/owner/geometry/native state, missing GXI or unsupported capture remains
Stock. No other material or model group is selected.

Mode4 uses original ENV RGB floor(channel*80/128) plus flipped framebuffer RGB
96/255 in two draws on a PRIVATE target. It neither replays the car nor writes
additional geometry into the application framebuffer. It saves/restores all
mutated native slots, target/depth/viewport and UP stream0 side effects before
the original draw. Pending repair is guarded before affected API access and
native-interface escape. No CPU color/depth readback or scene traversal is added.

The stage18 equation is Current+Current.alpha*Environment, versus stage7 ADD's
Current+Environment. At Current.alpha=1 these RGB operations coincide; the old
A/B alone therefore cannot assign the darker result to COLOROP. Source-contract.md
records the exact original and diagnostic equations independently of screenshots.

The original PS2 writer is a MIXED_STATIC_AND_FRAMEBUFFER producer, not a proved
cube map or extra environment camera. This PC implementation preserves the
original PC coordinate generator and base shading. It approximates FIX48/128
with96/255, uses32-bit targets and captures before a target draw rather than
after the original PS2 model/pass boundary. PS2 PSMCT16, VU basis, body grayscale/
passes and queue timing are not reproduced exactly. No exact-looking claim is made.

The new capture needs a non-MSAA32-bit main backbuffer, suitable native caps,
<=16MiB copy storage and successful CopyRects/composition HRESULTs. Actual
driver support remains pending. Do not interpret selected mode or an uploaded
static image as successful mixed capture. On copy failure no static fallback is
mislabelled as Mode4. Main-target state must be restored even after partial failure.

Both independent builds, focused tests, original local asset Reset subcases,
exports and generator checks passed. A first stale-test staging compilation failed
on CHECK include order; an intermediate run found a real Stock getter regression.
Neither result is hidden: final guards trigger only for PS2 pending work, and
the baseline reflection-contract regression passes unchanged. A final null-COM
identity check rebuilt/retested the PS2 variant while reusing the unchanged
independently built baseline. Command-log.md records this sequence.

All permanent changes are in pc-port. Frozen renderer, original assets, old
PILOT1.4 artifacts and Turkey3 source implementation remain intact. Earlier
uncommitted work is preserved, so this iteration does not create a broad commit.
The handoff includes sources, exact staged patches, compact witnesses/tests and
two proxies; original GXI/PSM/DX, screenshots and full logs are excluded.

Follow runtime-ab.md: same Tata, paint, Free Camera bookmark and lighting;
all other experiments off. Compare0/4, then use2/3 to isolate image/COLOROP.
Confirm copy/apply/draw/restore HRESULTs and hood/roof/background controls.
This single runtime comparison is the next recommendation; no other phase starts.
