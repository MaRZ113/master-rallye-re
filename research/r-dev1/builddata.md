# BuildData command

Retail ID 0x58 in 005B0990 constructs the object at 005B2960, whose vtable 00692F88 has destructor at +0 and execute method 005B2F80 at +4. 006018E0 registers it in a growing pointer list and immediately invokes +4. This confirms the preliminary dispatch path.

005B2F80 gets a start path from a path service via vtable slot +0x14, normalizes slash direction, trims a trailing separator, clears all nine counters at 006FE020–006FE040, then invokes 005B2DA0. Retail assembly zeros EBX at 005B2F9E, stores it to 006FE020–006FE040 (including `MOV [006FE040], EBX` at 005B303B), then calls the walker at 005B3041. This disproves the earlier accumulation hypothesis. No folder picker occurs in this wrapper; exact path-service meaning is UNKNOWN.

005B2DA0 recursively enumerates *.*; directories beginning with a dot are skipped. For file entries it checks for a DataGx\\ path segment and tries the supported callbacks. The wrapper reports file/directory/model/texture/image-bank totals. It does not establish a scope limited to one selected DataGx folder.

- .gxm → 005B29C0 → ordinary GXM loader 0054B320 and model build/cache path.
- .gxi → 005B2AD0 → 0054A9B0 then texture conversion/cache 0054ACD0.
- .gxb/.gxp → 005B2C40 → image-bank loader 0054B430 and downstream handlers.

The normal model/texture paths may read a valid cache or write a new DX/DXT cache. Generic cache writers call CreateFileA with CREATE_ALWAYS. BuildData is not proven to force a rebuild. Image-bank descendants' write behavior is UNKNOWN.

Safety classification: RECURSIVE_READ_WITH_CACHE_WRITES, high overwrite risk. Its ID has no item in the mapped retail main menu. Do not test against any authoritative tree. A future test requires a legitimate invocation route, a disposable copy with a tiny DataGx input, no existing cache target, and a complete before/after manifest.
