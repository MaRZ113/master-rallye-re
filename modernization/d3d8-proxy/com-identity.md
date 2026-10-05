# COM ownership and identity

The complete ABI contains 16 IDirect3D8 slots and 97 IDirect3DDevice8 slots,
including IUnknown. [interface-map.json](data/interface-map.json) is generated
from the pinned header; synthetic checks compare names, order, counts and hashes.
All wrappers have one primary interface, so its address is also its canonical
IUnknown address. Their virtual methods are noinline and STDMETHODCALLTYPE.

| Operation | Native reference | Local wrapper reference / result |
|---|---|---|
| Factory / CreateDevice | Initial returned ref is adopted | New wrapper starts at1; raw root/device does not escape |
| Known QI | Native QI receives original IID/output and increments on success | Adopt that acquired reference and replace only the output with the same wrapper |
| AddRef | Exactly one native AddRef | Atomic local increment; return the native count |
| Release | Exactly one native Release | Local decrement; delete wrapper at zero, even if raw child refs keep native device alive |
| GetDirect3D | Original native call acquires parent reference | If native parent matches, adopt and return the original Root8 |

Device construction holds an additional parent Root8 AddRef until wrapper
destruction. This guarantees GetDirect3D and the registry remain alive after the
caller releases its original parent. Those ownership refs also retain native
parent lifetime. Returned native refcounts include that hold; COM refcounts are
diagnostic and must not be interpreted as application-owned refs alone.

Each root keeps a raw-device→wrapper map. CreateDevice reuses a live wrapper if
the native runtime returns the same raw identity again, adopting the acquired ref.
The final device Release removes the registry entry under the same lock before
destruction. QI never creates another wrapper. Native tests exercise known IID
round trips, rejected cross-interface QI, native result/counts, and parent release
before device release. Every ordinary ABI slot is invoked via SDK interface
pointers against mocks with distinct arguments/results.

An unexpected supported IID is forwarded honestly and logged as a possible raw
escape. The proxy does not claim canonical identity for unknown extension
interfaces. A GetDirect3D native-parent mismatch is similarly logged. Target
runtime acceptance requires neither condition; investigate any such record.
[Microsoft's QI identity rules](https://learn.microsoft.com/en-us/windows/win32/com/rules-for-implementing-queryinterface)
govern the known interfaces, and the raw-child limitation is explicit in the audit.

The process-pinned Session logger uses no teardown callback from DllMain. Final
wrapper Release logs closure and flushes any incomplete armed capture as such.
If the game leaks a wrapper until process exit, there is no fabricated Release or
loader-lock COM cleanup; missing orderly shutdown remains evidence to investigate.
