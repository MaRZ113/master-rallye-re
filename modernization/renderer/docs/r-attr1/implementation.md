# R-ATTR1 — initial factory installation only

Independent change on top of the separate R-OBS1 commit, on the existing `master`
checkout. R-CAM1-A3c race epoch logic is unchanged. The research EXE writer and
its unrelated Broker NULL-list/XML fixes are not shipping dependencies.

`CONFIRMED_BY_EXE`: primary owner constructor VA `0x00558D50` publishes
global owner VA `0x006F9D80`, clears initialization/device flags and calls
enumerator VA `0x00558EE0`. The latter clears native COM pointers and invokes
Direct3DCreate8 via CALL VA `0x0055905B`, returning at VA `0x00559060`.
The renderer singleton stores owner+0x20 only after that constructor returns;
it is therefore deliberately **not** used as an already-live ownership proof
at this earlier factory seam.

`ProxyDirect3DCreate8` attempts the guard once **before** loading/creating the
system D3D8 factory. Admission requires exact disk SHA, ImageBase `0x00400000`,
the exact native return PC, complete factory/thunk instruction contexts,
published primary owner with exact vtable, primary flag=1, initialization and
device flags=0, both COM pointers=0 and Loading counter=0. Recreated/later/foreign
factory calls fail closed. The full original 374-byte Loading function must
match, not just five bytes at a guessed address.

Peer threads are bounded to 64 handles, suspended, and their EIPs checked
against the entire Loading function. An inaccessible thread, active Loading
PC, capacity failure or new peer found in a second inventory rejects. Phase
and bytes are reverified under that quiescence. This uses the exact native
pre-initialization seam; it is not permission to patch arbitrary code during
an active race, nor a universal lock against external process injection or
arbitrary new remote threads. No module loading, logging, heap allocation,
Broker call, or scene callback occurs while peers are suspended.

The production PatchMemory path protects only the five-byte region, writes,
reads back, flushes instruction cache and restores protection. Failure rolls
back and verifies original bytes/cache/protection before resuming peers. An
unverified rollback records `restart_required` and returns no D3D8 factory,
preventing Loading execution with a partial unknown instruction. A verified
rejection/rollback permits unchanged D3D forwarding. There is no per-frame
retry. An already redirected or foreign site is never overwritten or claimed.

The JMP targets original game code, with no proxy trampoline. An owned
successful patch lasts for this process, including Reset and race Restart;
it is not removed on device Release. Normal process exit discards it. Disk
EXE bytes, assets and Broker data are never written by this feature. Unknown
EXEs preserve original behavior; other renderer feature-local capabilities
are unaffected. There is no new public INI option.

Session record `legacy_loading_attract_guard` includes exact gate, phase,
context, quiescence, applied/owned/rollback flags, bytes, RVA and reason.
For a meaningful live test, `applied=true` is required. A skipped guard and a
normal lucky first load are not installation/runtime acceptance.
