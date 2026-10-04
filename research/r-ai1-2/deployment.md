# Research package and future external deployment

Verdict: **RESEARCH_EXE_FIRST**. Original EXE unchanged on disk: **NOT YET** for
this proof package. A public removable mod with original EXE byte-identical
remains the target; no public release is proposed.

Retail imports KERNEL32, D3D8, DDRAW, DINPUT8, WINMM, DSOUND, USER32, GDI32,
ADVAPI32, OLE32/OLEAUT32, WS2_32, COMDLG32 and COMCTL32. Existing
LoadLibraryA/GetProcAddress/GetModuleFileNameA/GetModuleHandleA IAT entries are
68F0B8/68F0C0/68F178/68F238. There is no characterized randomizer callback in
data. A D3D8/DInput8/WinMM proxy would need complete forwarding and an audit
against the actual user's graphics/widescreen wrappers. That compatibility
and loader discovery are deferred, not assumed solved.

The exact research EXE bridge resolves an absolute DLL path formed from its
own filename directory, not process cwd. Path reads/copies are bounded.
Missing DLL/export returns Stock. Export ABI is stdcall four integer arguments.
The DLL parses config and selects policy; normal native class cases and
registry-derived identity remain in the game. No in-process hook installer,
WriteProcessMemory, proprietary asset mutation or participant allocation is
implemented in the DLL.

DLL initialization requires game base400000, exact size3121214, exact four/
five profile SHA256, and all live bridge/immutable builder pins. Unknown
identity returns Stock before native game APIs. It supports only the two
generated profiles, not arbitrary patched builds. No force/allow-any option.

## Cave composition

Old R-AI1.1's 68E300..approximately68E463 overlaps R-AI2's 131-byte
68E300..68E383 shim. Old manifests are never overlaid.

New allocation: Quick selector68E400, Master68E700, Cup/Invitation68EA00;
each bounded below its next300-byte interval. Loader68ED00, Challenge68EE00,
names68EE80..68EECD. R-AI2 remains68E300..68E383 and hardening remains
68E2A0/68E2C0. Sorted ranges cannot overlap; only VirtualSize is merged.
All code fits existing text raw padding below68F000 and existing aligned
pages/image; no physical participant storage/table/loop expansion.

Four-car profile composes hardening plus bridge only. Five-car profile adds
the UNCHANGED audited R-AI2 capacity shim. Its special ID0/T1, Track10,
Race, one human, ghost-off, frontend Opponents3 guard still applies.
R-AI1.2 itself has no track/player/difficulty selection guard and no count
writer. Four-AI testing must use that separate proven five-car setup.

Reproduction:

    python tools/r_ai1_2_build_native.py --source <pristine-MRallye.exe> --output .research-output/r-ai1-2/package
    python tools/r_ai1_2_randomizer.py verify .research-output/r-ai1-2/package/four/MRallye.exe
    python tools/r_ai1_2_randomizer.py verify .research-output/r-ai1-2/package/five/MRallye.exe --five
    python tools/r_ai1_2_randomizer.py verify-module .research-output/r-ai1-2/package/MRallyeRandomizer.dll .research-output/r-ai1-2/package/module-manifest.json

Installed MSVC x86 and Windows SDK are used; no compiler is installed by tools.
Input hash/size, original instructions, PE mapping, non-overlap, deterministic
output and inverse restoration to pristine are verified. DLL build source/
compiler/hash metadata is separate. Generated EXEs/DLL/objects stay ignored.
The [build summary](build-summary.json) pins module size/hash/source and both
profiles. The module verifier rejects a self-asserted unknown manifest/hash.
Scoped Git attributes retain LF for the three pinned native source files,
including on Windows autocrlf checkouts; unrelated files are unaffected.
MSVC14.50.35717 builds in two output directories produced byte-identical DLL
and EXEs. Runtime package folders contain EXE plus DLL/config; sample config
is staged only when absent, never over an existing user file.
Remove DLL/config or use all-Stock config to disable randomization on future
rosters. Restore pristine EXE to remove research hardening/capacity/bridge.
Existing saved Master rosters remain governed by stock persistence.
