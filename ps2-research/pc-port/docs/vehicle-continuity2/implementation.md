# Vehicle continuity2 implementation

## Runtime-confirmed fixes

PID43748 transition log identifies four exact one-frame gate8 failures, each recovering at
gate10 next frame:1647→1648,1928→1929,2080→2081,2088→2089. Refresh flags14/12 identify
owner/upload certificate renewal, not a depth-buffer defect. Atomic current-tree validation
now snapshots all13 live source descriptors/mirrors before first suppression. Handle tables
are bounds-checked, source UV/winding and healthy references remain exact, every owner/token
is rechecked, unknown callbacks and multi-material leaves fail closed. Source records are
committed together. Same-vehicle/race environment matrix cache follows the existing normal
frame policy; no geometry certificate survives invalidation. A failed first submission
closes the frame to late replacement, avoiding partial native/private duplicate bodies.
User confirms684045fe... removes flicker.

Frontend COMPLETE uses pinned asset hashes→source tread masks in BOTH material validation
and submission. Only exact tread primary-U changes CLAMP→WRAP; V/rims/body/reflection
sampling and original UV/texture bytes remain unchanged. User confirms the visible fix.

## WOOLDAND and UFO

Original fixed shader registry and constructor consumers prove unknown crashiny and
carbrakelight leave generic authored-secondary fields intact. They are not renamed carshiny.
WOOLDAND adds mode5: primary alpha blend then separate .75 authored-glass secondary.
UFO adds mode21: separate .25 primary and .75 environment additive layers. Both preserve
source texture/vertex bytes. D3D uses64/255 and191/255 constants: an explicit GS quantization
approximation, not pixel parity. Texture factor, fog and blend operation are lazily captured
and exactly restored; mode20 and working Mode4 remain distinct. See frontend/findings.md.
Registry26 includes existing Forklift but it is excluded from gameplay coverage goals;
25 paired playable families are source-admitted. User confirms both new COMPLETE models.

## Damage parts

Front cover source10/PS2root19 changes XYZ with exact UV/winding/current owner. A26-vertex
static map applies verified native deltas. User confirms retained transparency.
Front reflective sources21/22→PS2roots5/11 also deform. New maps cover48/22 vertices;
all duplicate candidate deltas must agree, or native fallback. Their original mode3,
source normals/colors/UVs and native boundaries are preserved. Cold already-damaged state
without a healthy reference fails closed. Native replay includes real healthy/deformed
snapshots and deliberately conflicting duplicates. Final roots5/11 visual test is pending.
Rear OFF13624 retains exact XYZ/UV source identity before/after damage; no hash weakening
was made. User now confirms rear reflection. OFF, ON and glow remain separate branches.

## Full CAR fleet preparation and remaining gates

29PS2 families accounted for:25 paired race families, Forklift excluded, FORESTER/MOONBUGGY/
TANK unpaired. WOOLDAND→PCForester remains distinct from PS2FORESTER.25 authentic source
CAR candidates include static crew/interior once and exclude conditional/wheel geometry.
All25 pass native binary decode/hash checks; this is not runtime rendering admission.
Most native wheel resources have5 records, X-Trail/Kia/Navara/Tata4; UFO has no paired wheel.
The new F10-only observer records actual current owner/geometry/WORLD for CAR and WHEEL,
without suppressing a draw. No non-X-Trail CAR renderer is enabled by this release.
Next integration must close current owner/root/transform/generation certificates and define
per-family damaged fallback/deformation before activating each exact source profile.
20 verified brake-glow profiles are preserved; this phase does not claim20 new visual PASSes.
Generic lamp mode3 can retain authored perspex/rubber; do not substitute a mixed framebuffer
source simply because a lamp is reflective. Further OFF/ON expansion needs exact source
material and current branch certificates. See coverage/ and fleet-car/ matrices.

## Build boundary

Starting HEADcf969a189097cab94281a9b7e7e9771eff97751d; frozen renderer tree
 e33386bcf682db6983380c499e4928726c758fe0 from immutable object baseline
0bddf7c7bc5e95831f98714ff6231da05ab073ea. Original renderer and integration patches unchanged.
Only canonical .build/baseline/.build/ps2-enabled and .staging reused, serial MSBuild parallel1.
The clean handoff records the exact verified working-source snapshot, not an implied commit.
