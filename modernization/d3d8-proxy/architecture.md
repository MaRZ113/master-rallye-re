# Forwarding architecture and limits

`DllMain` only records HMODULE. System DLL loading, hashing, file I/O and COM work
are deferred to an export call. `InitOnceExecuteOnce` resolves the native runtime
using `GetSystemDirectoryW() + "\\d3d8.dll"` and `LoadLibraryW(full_path)`.
The handle is checked against our HMODULE; matching it is rejected. Export calls
use pointers returned by `GetProcAddress` on that explicit system handle.
The module remains pinned until process exit because raw resources can outlive
wrappers. There is no d3d8 import library or local d3d8 dependency.

For the x86 process on this x64 host, WOW64 selects the 32-bit system runtime.
Session logging records requested and actual loaded module paths, rather than
assuming their spellings must agree. The host's inspected x86 runtime is
`C:\Windows\SysWOW64\d3d8.dll`; its exports and SHA are in the export manifest.
Real loading by the game still requires the human startup log.

The core library contains generated exact-header override declarations and all
ordinary forwarders; COM plumbing is separate. MSVC `STDMETHODCALLTYPE`/`WINAPI`,
the pinned interface order and Win32 pointer/structure size assertions enforce
the ABI. No sparse interface is used. All ordinary forwards call the native
method with the original expression arguments and return its original result.

The native call and observer before/after steps share a per-device critical
section while tracing is enabled. State/counters are isolated per device.
There is no global per-draw logger lock. Root device registry changes use a
recursive mutex; local COM refs are atomic. Session file writes have a separate
lock. Enabled=false skips observer locks/state work; no graphics option exists.
This makes metadata consistent between concurrent calls, but serializes those
calls while tracing. Cross-thread ordering/timing parity and overhead remain
human checks; a non-multithreaded native device is not made thread-safe by a proxy.

No extra native Get* calls, AddRef on logged resources, draw calls, device changes
or content reads are issued for tracing. Native-record snapshots are copied
before the forwarded draw. Set/get observations update only after successful
calls; normal forwarding occurs even when observer reads or writes fail.
Metadata pointer reads are isolated by MSVC SEH, and allocation/I/O exceptions
disable diagnostics or abandon output. The trace preserves the FPU environment
around its work. The raw runtime's own FPU effects remain observable.

Wrapper allocation failure is the unavoidable COM-plumbing exception: a native
successful device whose wrapper cannot be allocated is released, output is set
null and E_OUTOFMEMORY returned; factory failure returns null after Release.
This is not a graphics-parameter override. Trace-buffer/logging allocation failure
does not take this path and cannot turn a successful native draw into failure.

Native counters cost one update per method and a small state copy for setters;
large JSON draw serialization happens only after an explicitly captured Present.
Counts are written on the first interval, every 60th interval and captured frames.
There is no per-draw normal disk output. Resource creation metadata is logged
when created. One explicit capture can hitch. Real-game performance is unmeasured.

The implementation targets Windows with the used SDK APIs (Vista or later API
surface, practically Windows 7+). It has not been validated on Windows XP, Wine,
Proton, overlays or another D3D8 proxy. The initial handoff uses native Windows
and a clean local-proxy slot; chaining an existing wrapper is not implemented.
