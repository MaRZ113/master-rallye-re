# REA readiness and handshake

## Connected installation

The REA MCP tools were available and answered this task. The observed tool
stack reported REA agents `6.4.0`, MCP client `0.162.0-alpha.17.2`, and 170
tools under catalog digest
`85d80276ecacf937bf3e803b7a31748ae1a8286f556fa5cf734eef768cc7d72a`. The
Windows Ghidra provider reported Ghidra `12.1.4` and JDK `25.0.2`. These are
observed tool-reported versions, not independently hashed installations.

REA was useful on the original PC retail PE: it confirmed target identity,
mapped addresses to file offsets, exposed procedures where Ghidra had defined
them, decompiled the PC alpha-variant selector and shader registration, and
returned their call/data evidence. The exact source is still the immutable PE
identified in [target compatibility](target-compatibility.md).

## Unsupported PS2 lane

An exact `open_binary` request for the canonical `SLES_509.06` was rejected
with typed `capability_unavailable`. The configured Windows Ghidra P0 lane
accepts PE x86/x64, not the game's MIPS R5900 ELF. Hopper was unavailable for
Windows/MIPS and IDA was not configured. REA's ELF layout capability was
limited to ELF64 x86-64 and therefore did not apply to this 32-bit console ELF.
No processor override or transformed copy was used to force an import.

The official [REA Ghidra/MIPS support guide](https://github.com/morluto/rea/blob/main/docs/ghidra-mips.md)
describes a bounded MIPS32r2/o32 lane; it does not make this R5900 target a
supported REA analysis. A generic statement that “MIPS is supported” would be
too broad for this result.

## Result

REA readiness: **CONNECTED**.

PC PE analysis: **SUPPORTED AND USEFUL**.

PS2 `SLES_509.06` analysis: **UNSUPPORTED BY THE CONFIGURED PROVIDERS**.

This provider limit narrows what was independently revalidated in this pass;
it does not invalidate earlier canonical-byte evidence or justify silently
downgrading it. Conversely, prior Ghidra conclusions are not described here
as fresh REA results.
