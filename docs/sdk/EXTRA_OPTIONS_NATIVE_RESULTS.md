# EXTRA-SET1 — native implementation candidate

## Changed

The private `extra-set1/integrated-11` CMD candidate combines SDK33 with the
installed G1 Randomizer source line and a private build of the existing PS2-enabled
D3D8 Proxy. Nothing is installed. The released `dinput8.dll` name and its six
DirectInput exports remain; the G1 core gains a versioned SDK roster provider,
not another vehicle registry. Its seven-AI/eight-participant limit, G1 duplicate
fallback, grid code and legacy INI parser remain. The owner's legacy INI is copied
byte-for-byte. The core DLL is **extended**, not byte-identical to the release.

Vehicle Setup's **GEARBOX** page now contains native PAINT / LIVERY, TIRES,
APPLY, CANCEL and DEFAULTS controls. They use the game's original multistate,
button, text, arrow and Broker implementations. Up/Down reaches every action;
native lists own the choices. Apply persists per physical CarID, Cancel restores
the committed draft, Defaults proposes Stock without changing other setup values.
The pilot application scope is **single-player Quick Race, player 0**. Other
race modes retain their existing SDK/Randomizer behavior; customization there is
not qualified by this candidate. No new CarID is allocated.

TIRES supplies Stock, Tarmac, HardDirt, Gravel, Grass and Mud. The original front
and rear writers run first, then a selected non-Stock Name is published at both
`Vehicles/Car0/Suspension/{Front,Rear}/TyreType` before vehicle construction.
The existing native loader consumes five surface records with twelve float
coefficients per family. All 300 original coefficients remain unchanged. Stock
does not override either writer. Geometry, wheel radii and source physics tables
are not edited. Actual driving differences still require the owner test.

Livery mappings are per-car data in `rmod1/research/extra-set1/vehicles.json`:

| Physical ID / family | Available interpretations |
|---|---|
| 2 / Tata | Existing PS2 presentation; complete native PC visual bundle |
| 18 / megane | Existing PS2 presentation; complete native PC visual bundle |
| 21 / SeatBuggy | Existing PS2 presentation; **partial** PC sponsor-panel texture transfer; complete native PC visual bundle |

The renderer queries a versioned interface in `dinput8.dll`. Texture-only uploads
use private copies and exact atlas ownership, preserving alpha. Complete PC mode
allows the original compatible body/wheel/lamp draws instead of the PS2 replacement;
returning to PS2 mode reuses the existing proxy. Texture revisions invalidate the
derived upload cache. Race replacement is restricted to player 0; same-family AI
does not consume the player's replacement. CarID, physics and registration stay
stable. These are source variants under the owner's renderer settings, not a
claim of original PC/PS2 pixel parity. An independent second shipped PS2 SeatBuggy
livery has **not** been recovered; the partial transfer is labelled accordingly.
Distinct accepted demo sponsor assets are not merged or overwritten.

## G1 and SDK composition

The installed Pristine G1 proxy/core hashes match the preserved G1 package,
not F3. The G1 plan and its three different Quick Race hooks are used. The two
previously qualified SDK/Challenge replay compositions are reused. A live launch
reached `SDK_ROSTER_REGISTERED`, `SDK_BINDING_PROFILE_MATCH`,
`NATIVE_INSTALL_COMPLETE operations=16` and `BOOT_B_READY`; this goes beyond the
earlier suspended F3 proof. The provider imports physical IDs, classes and mode
masks from the accepted SDK plan, including IDs 30–32; it does not infer physical
IDs from display ordering. Challenge's relocated human field is derived from the
existing SDK table layout (`0x6dc`); its authored eligibility exclusions remain.

Runtime admission uses the relevant code/data layout and hook/API preimages,
not a whole-EXE/core SHA allowlist in the Extra Options bootstrap. Hashes identify
the researched inputs and offline deliverables. The existing SDK launcher still
selects its qualified retail profile. Other executable/hook layouts have not
been qualified here; this is not a universal-version installation release.
There is no Proxy SHA admission gate.

The private source-root stage supplies missing stock resources through the
existing native directory layout, using verified hardlinks when possible and
archive bytes otherwise. Existing accepted resources take precedence. The
archive itself is unchanged. A native intro-player wait at TitleMode 0 was
observed; the candidate uses the existing `Frontend/SkipTitles` switch and a
private fullscreen/borderless configuration. No movie, renderer or original
installation patch is used for this workaround.

## Validation and evidence boundaries

| Check | Result |
|---|---|
| G1 shared core | 326 checks, zero failures |
| Relevant Randomizer Python regression | 45 tests, one existing optional skip |
| Binding Python regression | 4 tests |
| Renderer Windows CTest | 44/44; private graphics build reused unchanged in the final package |
| Production menu callbacks in x86 Broker harness | Apply/Cancel/Defaults, six tire routes, both axles, Stock/AI/replay isolation, independent toggles, texture alpha and mismatched-atlas checks pass |
| Compiled SDK provider | Valid registration; duplicate IDs, wrong class/mask/count/offset rejected; participant default preserved |
| Compiled composition / forwarding | SDK bytes and writable state, altered/partial input checks, composed stubs; all six name/ordinal DirectInput forwards match the system DLL |
| Addon/SDK Python regression | 61 tests, zero failures |
| Native page authoring | Three tests: component ownership, reachable actions and typed paths, uppercase stock-font labels, deterministic output, unsupported scene rejection |
| Final bundle | 8,004 resources; 413 accepted resources byte-identical, with only private editable options intentionally changed; accepted addon plan, patch plan and extension exact |
| Installed files | Baseline hashes preserved; detailed list in private `validation.json` |
| Actual game | Main menu and attract rendering observed; real Gearbox AI and new native controls rendered in a separately labelled UI fixture |
| Normal interactive selection / frontend-race A/B / tire behavior / Results | **OWNER TEST PENDING** |

The native UI fixture exposed a real crash: the String-path Broker overload
received an interned Name ID (`0x4d5267`). Publishing UI Name values through the
correct overload fixed it. The adversarial harness now rejects that misuse.
The stock font also requires uppercase labels, and arrow states are Int datums.
These corrections are reusable and are present in the normal candidate page.

The UI fixture substitutes the Gearbox scene at startup only to inspect real
game rendering; its screenshot is **not** proof of normal menu navigation or a
race. The delivered CMD retains the normal frontend flow. Automated synthetic
key presses did not move the stock control game's menu either, without the new
DLL; interactive confirmation cannot be claimed from that automation session.

## Owner test

Run the private `Launch-Extra-Options.cmd`. Use ONE PLAYER → QUICK RACE →
VEHICLE SETUP → GEARBOX. Start with the ordinary TATA (ID2), then test SeatBuggy
(ID21) when available. Use the game's usual Up/Down, Left/Right and confirm keys.

1. Select a livery and tire family, choose APPLY, return to Vehicle Select and
   inspect the large preview. Enter the next race; compare PS2 and complete PC
   choices, including wheels and lamps. The partial SeatBuggy choice must remain
   visibly labelled partial.
2. Test all five tire families and Stock; check `host/MRallyeExtraOptions.log`
   for paired `TIRE_PUBLISHED` Front/Rear records. Check handling separately from
   the log; a publication record alone is not solver-consumption proof.
3. Verify Cancel, unapplied Defaults, Back, re-entry and restart persistence.
   Toggle Enabled/Liveries/Tires independently in `host/MRallyeExtraOptions.ini`
   between launches. The legacy Randomizer INI remains separate.
4. Check Forester30, RAV4 31 and TOMCAT32, custom order, addon AI, eight-participant
   limits, grid behavior, Results and race re-entry. Compare other race modes and
   championship resume with the accepted baseline; do not certify them from a
   successful Quick Race alone.

Keep `host/MRallyeExtraOptions.log`, `host/MRallyeRandomizer-boot.log` and
`host/MRRRenderer/logs` with screenshots for any failure. Candidate state is
`host/MRallyeExtraOptions.state.ini`; original saves/installations are not the
candidate's settings store. No push, installation or release was performed.
# Owner feedback and follow-up, 2026-11-02

The owner confirmed that the native Paint and Tires controls are visible and
operable in integrated-11, but reported no visible livery change, undersized
action buttons, and no navigation after Apply. The owner's log records front
and rear TyreType publication for Grass and Mud; it does not establish that the
active solver read the selected coefficient records.

The follow-up retries graphics API lookup after early initialization and
distinguishes the proxy from the system DLL when both share a basename. It
records visual requests and texture matches/rejections, initializes race visual
identity independently of the tire writer, enlarges action controls, and
routes Apply/Cancel through the original Back command (-3). The original
0x483e28 jump table maps -3 to the native 0x4842e0 handler. Defaults remains a
draft. These are code and offline-test findings: actual menu navigation,
GPU upload/bind/draw, visual differences and active solver consumption remain
unverified. Do not treat a request log as rendered evidence.

The integrated-11 owner race diagnostics repeatedly reported `fleet_gate_3`
and `missing_or_wrong_size_local_env_gxi`. The packager had preserved a
relative `ReflectionSourceGXI` while moving the host to a separate directory.
The original local `PS2Grass/PS2EnvSource64x64.gxi` has the exact 16392-byte
layout and SHA-256 expected by the existing renderer. The corrected packager
points to that existing file; the file itself remains unchanged. This removes
the observed missing-resource cause, but does not prove that every later draw
gate passes or that a livery is visually correct.

# Owner confirmation — 2026-11-02

The owner tested integrated-13 and confirmed that native Paint/Tires controls
and the SeatBuggy PC Original, PS2 Original, and PS2 geometry with PC texture
choices work. This confirms those tested appearance paths, not tire-solver
consumption or appearance switching when PS2 reflections are disabled. The
owner subsequently reported that the latter is dependent on reflection mode,
and that reflections and brake effects need broader vehicle coverage.

The new optional `MRExtraVisualV2` export distinguishes PC bundle, PS2 bundle,
and the currently qualified PS2/PC-texture variant; the existing V1 export,
diagnostics and six DirectInput forwarders remain available. This is an ABI
extension, not a completed renderer milestone. The frontend and race replacement
paths still require `ReflectionMode=4`: their mixed second pass carries both
environment and layered-material information, and no independent replacement
for those operations has yet been qualified. The original/native fallback stays
in force. The 212-entry retail reflection geometry registry and the original
brake-lamp ownership registry do not by themselves bind SDK material semantics or
addon brake state to draw ownership. A universal reflection and addon brake
implementation remains outstanding, as do actual rendering tests for those paths.

