# Master Rallye Observatory v0.3.1-beta

## Fixes

- **Works with the modernization d3d8 renderer on the retail executable.** The renderer opens its own menu-less
  presentation window (`Master Rallye (<n> Hz)`) next to the native `Master Rallye` window. Both were accepted as
  main windows, so Observatory refused to open Broker Editor and showed the misleading "Enable Menues/Enabled" hint.
  When a process still has the native Game → Reset / Exit window, that window is now the only command target; a
  menu-less window is used only when no native menu window exists.
- **Native Dump with the renderer NULL guards.** The renderer patches the native Dump walker in memory with the same
  two NULL guards as the audited J.1 build, but places its stubs in allocated memory and counts NULL hits. This new
  variant, `renderer-broker-null-guard-v1`, is recognized exactly: the walker must equal stock after restoring both
  sites, each site must be `JMP rel32` + `NOP` padding, and each stub must equal, byte for byte, the renderer's stub
  builder output for its address and counter. Stub reads are limited to 64 bytes of committed, executable, private
  memory. The variant is NULL-safe, so a Dump after Results is allowed like with J.1.
- **Clearer Broker Editor errors.** "More than one main window" and "no native Game menu window" are now reported
  separately instead of the shared "Enable Menues/Enabled" hint.

## Compatibility and safety

Unchanged from 0.3.0: Observatory stays read-only; process access is query/read, and the only commands are the two
reviewed tool openers and Broker Editor's original Debug → Dump (local ID 2), sent once.
