# Saves, profiles and clean removal

The accepted J.1/J.2 launcher uses its external bundle/resource-root directory
as the process working directory. Runtime-generated PlayerState, Options and
progress files under that root are user data, not immutable mod resources.
Preserve them when disabling or removing a future runtime package. No J.3-A
command installs, deletes, migrates or rewrites saves.

A save may contain a roster entry for an addon physical ID. Before a future
runtime launcher loads such a profile, the enabled collection must include the
same compatible physical-ID mapping. Until save-compatibility checking is
implemented, the safe policy is to keep the exact addon collection enabled for
that save and make a backup before changing it. Do not manually delete
PlayerState or campaign state to resolve a mismatch.

Clean removal in the future is between game launches: disable the external
loader/package and preserve the external save/profile directory. The original
MRallye.exe and stock Data.sma are never replaced by J.3-A.
