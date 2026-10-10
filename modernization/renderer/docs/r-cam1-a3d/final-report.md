# R-CAM1-A3d final report

**READY_FOR_IN_GAME_VALIDATION** — actual functional Freecam candidate.
In-game validation remains **PENDING**. No deployment or game launch was performed.

Repository: `D:/Game/Master Rallye/master-rallye-re-general`, `master`.
Starting HEAD: `4de97f086cdae687360df335878235932d0bafa3`.
The phase commit and final clean-tree receipt are recorded in Git and the ignored
handoff/archive manifests. No branch/worktree or push.

| Area | Result |
| --- | --- |
| Event 4 | A3c permanently rejected a normal request during frontend execution. A3d records bounded native ancestry; normal requests do not permanently poison |
| Scene 7→8 / 19→20 | Observed owner initialization precedes later Hud0 request. Scene counters differ from owner/race lifetime. Actual poisoned traces contain no valid later success jobs |
| Root/HUD relationship | Proven by active parent job lifetime plus native selector return `0x004AA0C1`, initialized owner, Hud0 and native 1/0 flags; not adjacency/name alone |
| Job reuse | New lifetime serial; active reuse rejects. Bounded table protects active/root/parents |
| Race lifecycle | Separate candidate serial, matching successful root and HUD jobs, owner attachment/initializer/liveness. Unknown ancestry and failed/old callbacks cannot certify |
| Restart/teardown | New non-HUD request revokes; Reset/retirement/destruction set a fence. Current native registration/AI slot and attachment lifetime protect actor ABA |
| Owner reader | Storage readability, unique native live membership and temporal permission are separate; stale scene generation no longer prevents structural examination |
| Context | Native QuickRace mode→Type producer and mode1 branch verified. Type1 accepts one car; Type2 accepts 1..8 ready cars; one human, no network/replay/ghost/attract |
| Course | Owner job must copy RaceTest/France1 and DataScene/RaceTest/France1.xml. Numeric 9269 is not used as a course certificate |
| Camera admission | Exact pristine SHA/base/thread/intact hooks, one device and one camera with manager/current-holder agreement |
| Shared traversal | CALL `0x006532DD` → `0x00509680`, two arguments / RET8; common GameFov owner |
| Completion | CALL `0x005B0166` → scheduler `0x00653080`, float / RET4; verified x86 pre/native/post preservation |
| Owned CameraFrame | Planes +08..37, Previous +38..77, Current +88..C7: 176 bytes. Native viewport/source/flags/snap survive |
| Coherence | Effective endpoints/CPU planes persist through traversal, finalize, particles, late builder/debug and EndFrame. Present does not end the scope |
| VIEW/cache | Native builder interpolates equal effective endpoints. Its comparison sentinel -1 is checked; no cache flag forced. Inversion of actual displayed VIEW initializes flight |
| Restoration | Guarded exact owned-field restore after scheduler; safe lifecycle cancellation. Changed identity is abandoned without stale dereference |
| Freecam | Implemented, default OFF; configurable F8, WASD, physical Numpad, Custom, mouse yaw/pitch, vertical movement, fast/precision speeds |
| Input/focus | Optional game-HWND subclass forwards native input; no WH_CALLWNDPROC/RET/global keyboard hooks. NumLock-independent keypad, cleared focus state, fresh toggle edge |
| Deactivation | Current native stock pose resumes next render. Scene/Reset transitions deactivate and require fresh certification; not initial activation pose |
| GameFov | Both Off / FOV only / Freecam only / both combinations covered; Freecam does not require FOV or tracing |
| Baseline | Accepted R-OBS1b Broker/Dump/F10 and R-ATTR1 behavior preserved by source/regressions; new DLL smoke test pending. Prior unapplied-guard telemetry remains separate |
| UI/display/visuals | Windowed/Borderless, R-UI1, PreserveMargins, AF, MSAA, shadows, vehicle semantics/reflections preserved. Exclusive remains deferred |

Executed: renderer Python **153/153**, root synthetic **630/630**, native CTest
**13/13**, **62** observer ABI cases and **7** scheduler cases; existing RET8
traversal fixture passes. Compileall, production JSON serializer, 89 static
anchors, Win32 Release build, PE verifier and diff-check pass. Details and limits
are in [validation](validation.md) and [candidate manifest](../../research/r-cam1-a3d/candidate.json).

DLL: `modernization/renderer/.build-msvc/Release/d3d8.dll`, **1,718,784 bytes**,
SHA256 `6cd7c3e48de1548c9bfbbb58d25c17ae200aba2b46ea54706edcee77ccea9610`.
PE32/I386, direct required exports, no recursive d3d8 import.

First flight uses [actual opt-in INI](first-flight.ini): Windowed 1280x720,
physical Numpad, **F8**, Trace ON. Place INI beside root DLL. France1, one human,
initially one total car; wait for live certificate then toggle. Expect
`free_camera_state`, first effective scope and verified scheduler restore records.
Test stock return, dust/visibility, focus, same-course Restart, Trace OFF and
baseline smoke. On failure provide one settled France1 F10 plus session identity.
See [handoff](runtime-handoff.md).

Remaining unknowns are live flight/particle correspondence, the freshly observed
owner job source lost by A3c poisoning, unreviewed native F8 shortcuts, earlier
camera-dependent ordering/caches and distant car-centered streaming. None is
declared a runtime PASS. No teleport, HUD hide, roll, photo mode, lighting, asset
change or Exclusive repair is included.
