# Human runtime acceptance — pristine native Windows

**Pending.** Codex built and tested infrastructure; it has not launched Master
Rallye or claimed stock pixel parity. The local DLL is not installed by this task.
Use the pristine executable hash below; retain the original game and assets.

Target SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
(3121214 bytes). Proxy identity: [proxy-build.json](data/proxy-build.json), including
current SHA/size/imports/exports. Do not mix an older DLL with the new manifest.

1. Select an isolated copy of the game's directory using pristine MRallye.exe and
   stock assets/settings. Verify it with `Get-FileHash <MRallye.exe> -Algorithm SHA256`.
   Record resolution, fullscreen/windowed, graphics settings, track/car and OS/GPU.
2. Run the original native game there **without** a local d3d8.dll for the baseline
   menu→Quick Race→race→results→frontend sequence. Keep comparison notes; screenshots
   are optional unless a visual regression needs documenting. Do not reuse a
   widescreen/patched executable as the pristine baseline.
3. Check the destination's d3d8.dll slot is empty. If another wrapper is present,
   use another clean copy; preserve it. This proxy does not chain other local DLLs.
4. Copy `.build-msvc/Release/d3d8.dll` beside that copy's MRallye.exe. No EXE patch,
   registry change or injection is needed. Optional INI goes beside the DLL, copied
   from MRRGFX2.ini.example. Native system d3d8.dll is never copied or replaced.

## Stage A — visual and lifecycle parity

Run boot/menu, choose the same Quick Race/car/track, drive, inspect results, return
to frontend and exit normally. Compare startup success, resolution/aspect, car
body/glass/wheels, terrain/vegetation/sky, stock shadows/dust, fog, HUD/fonts/menu
and stable performance against the baseline. Check no new overlay or draw appears.
An explicit capture hitch is acceptable; persistent slowdown is not.

PASS requires the complete sequence, unchanged visible behavior/settings, no
proxy-specific crash/hang and correct startup provenance. The session must show
the expected EXE and proxy SHA, native system requested/actual DLL path, SDK120,
successful CreateDevice and unmodified observed parameters. Compare those values
with R-GFX1 rather than assuming a fixed resolution. Expected imports/ABI alone
cannot pass this stage. Any unsupported QI/parent-mismatch record is a fail to
investigate. Device Release should appear on clean exit; report leaks/missing closure.

If tracing appears to cause a difference, repeat the same sequence with:

```ini
[Trace]
Enabled=false
FrameSummaries=false
```

Forwarding remains active, with small startup/create/Release provenance. Record
whether the issue occurs in wrapper-only mode, tracing mode or both. Do not change
graphics options to mask it. Rollback is removing **this copied proxy** and its
optional INI from the isolated copy; preserve logs for diagnosis.

## Stage B — three complete F10 frames

With default tracing enabled, press and release F10 once in each state:

* frontend/menu with visible text and preview, if present;
* active Quick Race with visible vehicle/world, stock shadow and some dust;
* results screen after the race.

Wait for each one-frame capture to finish before the next press. One held key must
produce one capture, not continuous recording. Preserve the session plus three
`frame-<pid>-d<device>-<frame>.jsonl` files in `MRRGFX2/logs`. Associate filename,
scenario in notes; frame numbers alone do not name a game state.

Process each file using annotate_trace.py and summarize_trace.py with --session
(commands in trace-format.md). Store generated summaries in this phase's ignored
`.analysis/` or ignored MRRGFX2 directory, keeping R-GFX1 read-only.

PASS for infrastructure requires complete/nontruncated frame_end, successful
Present, valid provenance, module/base/return_rva, draw args, observational state,
matrices where written, resource associations where observed and an ordered API
sequence. Expect Clear before BeginScene, mapped draw owners, EndScene then Present;
multiple viewport/camera sequences are valid. Unknown inherited state and UNKNOWN
shared-mesh categories are valid, not capture failure.

A visible scene with zero intercepted draws, repeated missing Begin/EndScene,
unexplained absence of expected billboard/shadow/UI owners, incorrect RVA matches,
unexpected native DLL path, malformed files or multiple frames per held F10 fail
and require investigation. Do not equate no bypass warning with proof that every
raw call was intercepted. Counts can validate only observed routes.

Shader/light counts must come from the capture/session; do not assume zero. A
specific callmap match plus appropriate scenario/state can support an owner-level
CONFIRMED_BY_RUNTIME_TRACE finding. It still does not prove each shared mesh is a
vehicle/sky/terrain draw. Record corrections solely in static-runtime-comparison.md
or new data under this phase, retaining the original static claim.

## Stage C — optional device loss and multiple cameras

Try Alt-Tab and restore under the selected presentation mode. If stock invokes
TestCooperativeLevel/Reset, record HRESULT progression, both original Reset
parameter snapshots, restored resource creation and renewed Set* calls. A capture
interrupted by Reset should be incomplete; a later deliberate capture must start
with invalidated state and repopulate from observed calls. PASS is stock-comparable
recovery without stale-state assertions or proxy-added repairs. If no Reset occurs,
label NOT_OBSERVED, not failed or confirmed.

If available, capture stock split-screen to validate multiple viewport/projection
writes within one interval. Multiple-camera support is observational only.

## Return package and closure gate

Return baseline/proxy notes, optional regression screenshots, EXE/proxy hashes, graphics settings,
session log, three labeled raw captures and offline summaries, and optional reset/
split-screen evidence. Keep assets/binaries out of commits; no raw system DLL is
needed. Do not submit the native mock test files as game runtime evidence.

Only after Stage A parity and Stage B trace correctness are accepted may R-GFX2 be
closed as TRANSPARENT NATIVE D3D8 PROXY / CONFIRMED_BY_RUNTIME. R-GFX3 Classic+
requires a separate explicit next-phase request. This handoff implements no
anisotropy, FOV, lighting/fog/sky/shadow changes or backend translation.
