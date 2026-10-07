# Widescreen UI, independent camera ownership

Original UI authored640x480 is horizontally stretched when its unchanged orthographic matrix feeds16:9. Stock retains that control behavior. Centered4x3 preserves shapes and the centered original canvas. ConfigVersion1/exact pristine gate both new modes; gameplay FOV is separate.

Pristine orthographic owner **VA0x00561DF0/RVA0x00161DF0** uses x0..640,y0..480,near-1000/far1000. Shared cached transform0x0053F9E0/RVA0x0013F9E0 calls D3D SetTransform, returnRVA0x0013FA75. Stock matrix _11=2/640,_22=2/480,_33=-0.0005,_41=_42=-1,_43=0.5,_44=1,all others0. Owners CONFIRMED_BY_EXE; new appearance pending runtime.

Centered4x3 rewrites only this recognized PROJECTION at known executable return site. Effective viewport aspect a -> width480*a,half=(width-640)/2,bounds[-half,640+half], _11=2/width,_41=-640/width; Y/Z unchanged. Logical GetTransform remains original. Helper bounds aspect1..4;4:3 identity,16:9/16:10/21:9 synthetic tests. No90/45 legacy FOV code.

SetViewport recomputes cached UI projection when only viewport/aspect changes and current logical matrix matches exact UI shape. Rejected native wide matrix restores logical UI and disables UI only. Unreviewed state blocks/multiply paths retain existing fallback. Gameplay VFOV/CPU frustum and frontend preview remain separate.

PreserveMargins adds reviewed old left/right anchors to Centered4x3. Pristine sort **VA0x00509A21/RVA0x00109A21**, context `d987b8000000d86030d9c0d8c9d9c2d8cb`; overwrite/replay5bytes `FSUB [EAX+0x30]; FLD ST(0)`. Required ECX entity+0x4C packet nonnull,EAX=packet+0x24,mode+0x68=1/2. Static entity+0x50 fallback excluded. Text owner **0x0056D110/RVA0x0016D110**, draw site **0x0056D7BE/RVA0x0016D7BE** confirms packet modes1/2 orthographic; other modes Stock.

Only selected x shifts +/-half,y/z unchanged. [Reference exceptions](third-party-widescreen-analysis.md) are not guessed semantic element labels. Frame-owned edits bounded512, once per storage address, restored at Present/Reset/disable/release only when current XYZ still matches our effective point. Intervening engine writes win. Overflow skips/counts; restoration failure disables UI/logs. No persistent packet identity.

Bridge preserves flags/integer registers/stack/x87/SSE, replays both instructions then resumes pristineVA0x00509A26/RVA0x00109A26. Check exact context/base/SSE; pin DLL; single owner and installing-thread shifts only. Failed install selects Stock UI. Pinned bridge still replays stock safely if hook removal fails. Production bridge tested on synthetic executable memory, never a launched game.

Margin half follows effective viewport/Create/Reset. Packet sorting may precede a new camera viewport: **split-camera per-packet margin aspect remains unproved**, despite correct synthetic full/split/quarter viewport arithmetic. Centered4x3 is initial Stock+ candidate; PreserveMargins separately opt-in. Aspect outside helper bounds stays unchanged; no arbitrary projection guessing.

F10 quality records mode/reason/canvas width/extra/half; UI metadata hook/shift/restore-failure/overflow. Feature masks:UI32,viewport16,FOV2,reflection8,AF1. Native rejection or unknown shape does not authorize guessed UI mutations.
