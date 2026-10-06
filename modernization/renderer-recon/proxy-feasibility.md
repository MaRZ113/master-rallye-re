# Transparent D3D8 forwarding feasibility

Verdict: **CONDITIONAL**, with a strong static basis. The exact EXE statically
imports d3d8.dll by ordinary name and obtains the root interface through
Direct3DCreate8(120). Local loading is plausible: the unpackaged Windows search
order includes the executable directory before system directory, after redirection,
loaded-module/KnownDLL and other earlier rules. Actual loaded path must be logged;
no local-load test was performed. [Microsoft loader rules](https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-search-order).

Required export from IAT: Direct3DCreate8. Linked assembler can additionally resolve
ValidateVertexShader and ValidatePixelShader dynamically. Minimum conservative
export audit includes all three, with signatures/calling conventions checked against
the chosen native runtime. No other D3D8 export name/ordinal was recovered in this
EXE, which does not restrict exports that overlays may request.

**STATIC_INFERENCE:** an initial observational wrapper can wrap IDirect3D8 and
IDirect3DDevice8 and pass raw child resources unchanged. It must forward the complete
16/97-slot ABI, not implement only the currently observed methods. Preserve HRESULTs,
SDK120, creation flags, caps, parameters, resource pointers, reference counts and
MULTITHREADED semantics. Use an explicitly resolved real runtime to avoid loading
itself again. QueryInterface/IUnknown must preserve COM identity and cannot leak a
raw device through an unhandled query. Child GetDevice/GetDirect3D escape routes
need auditing: they can bypass logging if children remain raw.

No unusual pointer comparison against a COM vtable/address was established.
Engine resource identity/cache comparisons are present; that is not proof of a
complete identity audit. Resource wrappers are likely needed later for creation,
Lock/Unlock/upload content, resource identity, GetDevice consistency and lifetime:
textures/base textures, VB/IB, surfaces; swap chains/cube/volume interfaces if used.
Logging raw pointer identities is initially possible without modifying children.

Risks: a pre-existing d3d8.dll occupies the same name; widescreen wrapper chains
can alter presentation/projection; overlays can introduce methods/exports outside
this map; Wine/Proton selects runtime via its own configuration; dgVoodoo-style
backends may alter caps/formats/reset behavior. These are compatibility hypotheses,
not verified failures. Inventory the loaded chain in the next phase. Do not promise
parity across those environments from a static EXE scan.

The smallest next implementation is unchanged native forwarding plus bounded logs
in an isolated copy, validated by [runtime handoff](runtime-handoff.md). R-GFX1
creates no wrapper, DLL or hook.
