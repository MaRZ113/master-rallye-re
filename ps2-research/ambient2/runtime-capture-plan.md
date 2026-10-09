# Targeted read-only PCSX2 validation — NOT_PERFORMED

No controlled PCSX2 debugger/frame capture was performed in AMBIENT2. Existing course screenshots and offline traces are not promoted to runtime proof. This plan is a future validation procedure, not a completed experiment or a new phase begun here.

Use canonical SLES_509.06 hash`b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2`, the validated TNG hashes, and record emulator version, settings/disc identity, course, save-state provenance and frame/update counters. Prefer FRANCE1's local FlightList/MillList positive case first. Use read-only breakpoints/memory/packet reads; do not patch ELF/assets to force birds.

1. Break at`1af1c0`/`1af330`; identify concrete0xb0 manager, vtable473c10 and owning entity. Sample+a0/a4 list names,+a8/ac pointers, record vectors and+34 effective capacity. Capture both lists' counts, ordered80-byte record positions and global registry identity; verify against the exact FRANCE1 source hash.
2. Record pointer/count from`201350` and first/current entry+c0/c4/c8. This settles distance-observer identity and the last-entry direction observer used by pending activation. Sample source update cadence and pause, rather than assuming30Hz.
3. Capture RNG state at4262a8 before`1afa20` and before FlyBird`1b0a40`. Record clock+1c, selected nearest/base/index, count, free/pending/flying vectors and actual global call ordering. Track one stable entity pointer/Burdy ID through pending conversion.
4. Across consecutive`1b0e68` invocations sample its AI+0c origin,+18 direction,+28 speed,+2c travel; record entity+50 carrier translation. Compare float32 model with captured original inputs. Check whether the conditional rise draw occurred. Capture`1b0508` copy into entity+4c.
5. Read bank identifier and command key, slot1 counter/current key and en2d matrix. Capture camera renderer+220 input and before/after`330530` basis; verify Y-lock separately from flight velocity. Two or more key transitions settle update frequency, not just static frame shape.
6. Break/trace`337a98`/`3376c0` for that entity. Identify PSB frame, primary handle/atlas region, four CPU vertices,64-byte cache records and CALL packet. Capture texture descriptor and actual TEX0/TEX1/CLAMP/ALPHA/TEST/ZBUF/FRAME/TEXA/PRIM words after all inherited-state changes.
7. Record selected MSCAL0xf/selector0 and live VU micro-RAM, match uploaded program hashes and final GIF/XGKICK output. Correlate the same packet/entity with a rendered frame and counted visible sprite. A changing wing image alone does not establish a captured motion-to-draw chain.

Second bounded control: load TURKEY3 and sample registry+a8/ac. Its XML has no local MillList. Observe whether pointers are NULL or another owner/retained resource supplies MillList; record transitions across course unload/load. Also sample Brown property load if testing the writer bug and actual effective bank. Do not turn this into general emulator automation or a weather/animal-engine reverse.

Only then can selected observations become CONFIRMED_BY_RUNTIME. Full population, rendering cadence and visual parity remain UNKNOWN until their own captures. Actual live VU residency is an independent acceptance item, not implied by matching embedded microcode.
