# Paris-Dakar neutral source research

Paris-Dakar PajeroRED, PajeroSilver and the validation Nissan Patrol are neutral
source scenes. Create them with tools/paris_dakar_source_lab.py using your local
installation, then choose Source Garage → Reopen source scene and scene.json.
The final private pilot scenes are beneath
.research-output/vehicles/paris-dakar-source/validated/<vehicle>/scene/.

Preview/Open neutral3D use original meshes, UVs and palette samples. The scene
records CW exterior culling as a neutral viewing choice; source/normalized
coordinates, original materials and unresolved fields remain inspectable.
The four wheels use original source attachment datums and side rotations;
this is not a recovered gravity-settled suspension pose. No MR native authoring
or installation is enabled for these research scenes. Evo2 detail choices are
unavailable when the donor has no qualified alternate wheel resources.

Michelin decoded textures/structural geometry are private research outputs;
complete car assembly is not yet qualified. See PARIS_DAKAR_SOURCE_REPORT.md
and MICHELIN_SOURCE_REPORT.md for exact commands and evidence limits.

---

# Universal source scenes and the first 4Runner native pilot

Source Garage retains the qualified original Evo2 4Runner scene. Its neutral
preview is separate from an MR addon. Source material flags, unspecified TIFF
samples and dynamic suspension are not qualified source-renderer behavior.

Use Source Garage to reopen scene.json, inspect original identity and select
Create MR Source Fidelity. Supply the clean retail Data.sma, its unpacked
resource root, the qualified stock SUV model directory and a qualified base
roster. Creation writes a fresh project; it does not install a slot. The
immutable original scene and generated Source Fidelity resources remain
separate from editable MR authoring. Preview choices do not change source data.

The 4Runner pilot uses an independent retail SUV physics family, explicitly
selected MR audio and MR crew. Those are MR adaptations, not recovered Evo2
physics, engine recordings or crew. The source scene retains all six original
L/R wheel-detail resources. Check the conversion report for exact runtime
wheel routing, material decisions, dimensions and any unresolved semantics.
The selected Terrano physics donor receives measured axle/radius parameters
and an explicit RWD adaptation from source front0/rear1 torque records. Other
Terrano solver parameters remain donor-based, not recovered Evo2 dynamics.

Source provenance opens the original scene identity, hashes, material/mesh
origin, coordinates and unresolved fields. Open original neutral source scene
returns to the original evidence. Changed scene, manifest, texture sidecars or
conversion report fail validation rather than silently becoming a new baseline.

The normal Vehicle Studios, Material, Glass, Physics, Gameplay Camera 2.0,
Audio, Shadow, Identity and Frontend controls edit only the independent MR
project. Save/reopen, Undo/Redo and Restore retain their normal meanings. Restore
returns to that project's recorded MR baseline; it does not overwrite the
original Universal Vehicle Scene or the accepted source adapter.

Do not use opacity to hide wheel culling mistakes. The extra TIFF sample has
unspecified meaning and must not become an alpha mask. Glass transparency,
glass damage, brake illumination and reflections are distinct authoring choices.
Glass damage and lamp controllers must target explicit geometry; tyre, headlamp
and body materials must not inherit rear brake ON/OFF states.

Static hub locations and MR suspension behavior are different. Source hubs
have a documented 8.88 ft separation while the catalog says 8.78 ft. The pilot
keeps these records and applies only a documented reversible MR frame/datum
conversion. Do not visually lower the body, raise wheels or apply a global 1.05
scale to hide the source's high static stance. Contact behavior needs owner
testing in the real D3D8 game.

Build uses a separate alternative 30-entry roster. CarID29 alternatives are
mutually exclusive in a selected roster; Pajero, Heritage Trooper and Clio
projects are preserved. This does not add a 31st slot. Open the delivered
candidate launcher only when ready for owner testing. D3D9 images, static
checks and native emulation do not mark D3D8 gameplay as passed.

Owner checklist: vehicle-select identity/art and large preview; race spawn;
four wheels, tyre interiors, stance and suspension; body/window culling and
texture mapping; glass damage; rear brake ON/OFF; camera reset; audio; collision,
crew, shadow and AI; finish/results name; return to menu and race re-entry.
Record failures with candidate identity and a screenshot/log. Review this one
pilot before converting more vehicles or beginning a Classic profile.


## 4Runner Stable after owner D3D8 review

Stable retains accepted front side panes, windshield and lower rear brakes.
All five old Visual Polish options are disabled and refused by generation:
paint patches, mirror caps, cabin wheel/backing, rear glazing and disconnected
frame were rejected by the owner in D3D8. Original paint/mirrors, dark rear
windows, source cockpit/crew and simple underbody are retained. An old adapted
project remains historical comparison, not a qualified preset. Create Stable.

The upper center brake checkbox creates a separate default-off test variant on
original high rear geometry with the existing brake controller. It enables no
rejected kit. Test Stable first, then upper OFF/ON alone. Neither NEW candidate
is automatically owner-approved.

Supported Studios, source provenance and Undo/Redo/Restore remain available.
Restore resets the chosen project's baseline; it does not turn a historical
all-on project into Stable. Use the new Stable project for this rollback.
Immutable scene, native physics/wheels/hubs/sound/camera/collision stay unchanged.
Finish/Results/re-entry remain separate owner qualifications.


## Paris-Dakar Pajero Silver #271

Reopen the exact accepted Silver Universal Vehicle Scene in Source Garage, then
choose **Create Pajero Silver…**. Supply clean retail Pajero resources/Data.sma,
unpacked retail root and the qualified base roster. This creates independent
private authoring/Workshop copies; it never overwrites the original scene or
accepted projects. Only the reviewed Silver catalog/hash is admitted. RED and
Patrol have no native creation policy.

The prepared owner project is Paris-Dakar Pajero Silver #271 in the local library.
Source provenance shows original hashes/scene and recorded unknowns. Standard
Physics, Camera, Audio, Material, Shadow, presentation and history tools remain
available. Physics/audio are MR Pajero adaptations, not recovered Dakar behavior.
Original static crew is retained; independent crew fitment has no qualified map.
Glass supports windshield/front sides only; rear damage is unsupported. Headlight
alpha stays separate from glass damage; brakes affect original red lens regions.

Build creates a private CarID29 alternative within the existing 30-entry roster.
Other CarID29 projects remain separate configurations. Source rest attachments
are retained relative to body through a common origin rebase; original gravity
settlement and renderer parity are unqualified. Source reflections/animation are
not invented. Native D3D8 driving, damage, Results and menu re-entry require owner
tests; see docs/sdk/PARIS_DAKAR_SILVER_OWNER_CHECKLIST.md. Stop after this pilot.

## Dakar 2 initial source research

Use `tools/dakar2_source_lab.py recover` with qualified owner-local Xbox ISO and PAJERO or HINO, then reopen `scene.json` here with its sidecars. Sources remain read-only; a fresh output directory is required. Exact revision/commands are in `docs/sdk/DAKAR2_SOURCE_RESULTS.md`.

Source Garage inspects the recovered rest assembly and launches neutral D3D9 preview. Native Create is unavailable: no Dakar 2 MR policy is qualified. Provenance retains material/pose unknowns. CW/CCW expose unresolved facing; optional two-sided images are diagnostics only. Pajero wheel shader/alpha remains incomplete. GameCube/PS2 inventories do not imply mesh support. These previews do not qualify original-game rendering or gameplay.

## Dakar 2 source renderer research — v7.4

Reopen `.research-output/vehicles/dakar2-fidelity/final/PAJERO/scene/scene.json` (or HINO / NISSAN). Build the current application first with `python tools/build_rally_workshop.py`; derived source-state scenes require the updated previewer (MRPV v2). Original L1 scenes and older MRPV v1 native previews remain supported.

Source-state rendering applies explicit static source evidence for cull/depth/pass order and original colors. This is an approximation: full Xbox shader/UV1/secondary texture stages and actual runtime visibility remain WARN. Separate CW/CCW/NONE captures remain diagnostics. No native Create is enabled for these sources. The old Nissan gate is lifted only by the explicit qualified rigid-basis path, not a guessed transform. Comparison sheets use identical camera and uniform wheelbase scale; perspective prerelease images cannot prove an exact mesh match. See DAKAR2_RENDERER_RESULTS.md and DAKAR2_LOST_VEHICLE_COMPARISON.md.
# Lost Pajero texture research — v7.5

Original red MR Pajero textures survive in clean retail resources, with older TXT material references. They do not establish that the current DX meshes use that livery or that Xbox UVs match. See LOST_PAJERO_TEXTURE_RESULTS.md.

Private A/C source scenes and six-view sheets are under `.research-output/vehicles/lost-pajero-livery/review-ready/`. Open `C/scene/scene.json` through Source Garage: C is a partial original-MR203 badge experiment, with unresolved badge orientation defects on both side views. Other panels keep Xbox artwork. It is not a restored full livery. Native Create remains unavailable. Original source geometry/UVs/alpha stay immutable; the standalone overlay history supports Undo, Redo, Restore and reopening. No new MR project or gameplay qualification is included.
