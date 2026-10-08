# Runtime deployment boundary

## J0 status

The J0 compiler writes offline plans and optional validated resource staging.
It does not patch an executable, inject code, launch a process, or install a
DLL. Original `MRallye.exe` remains untouched. No public runtime architecture
is yet qualified.

## Candidate approaches and current evidence

The vehicle checkout contains exact-build EXE builders used as research
instruments, loose-resource staging tools, and separate Observatory capture
support. Those establish how to construct and inspect a test candidate; they
do not establish an unchanged-EXE bootstrap or safe in-memory patch lifecycle.
The earlier R-AI1.2 randomizer was a research DLL reached through audited
patched-executable seams. That demonstrates modular policy code in the
research composition, not a loader for the original executable.

A DLL proxy is not selected: proxy-chain compatibility with graphics wrappers,
bootstrap ownership, load order, and uninstall behavior have not been proven.
A process launcher/in-memory patcher is also not selected: no tested launcher
currently verifies the retail image before startup and rolls back all changes
on a partial failure. A general-RE Observatory integration is an evidence
consumer, not by itself an addon runtime loader.

The next deployment investigation must compare these options against the
actual host and any graphics wrapper used by the player. Required properties
are exact known-build verification, in-memory-only integration, atomic
fail-closed behavior, complete resource overlay resolution, conflict
detection, clean process teardown, and removable installation. Missing or
unknown components must leave the original game runnable without partial
patches.

Until that proof exists, generated plans report
`NOT_IMPLEMENTED_FAIL_CLOSED` and `runtime_installable: false`. No patched
research EXE or generated DLL is a public deliverable.
