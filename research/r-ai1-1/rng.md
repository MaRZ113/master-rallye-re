# Native RNG boundaries

**CONFIRMED_BY_EXE**. `0x4D1E90` returns the game singleton (pointer
`0x6F8B90`), lazily initialized with state12345. `0x4D1DF0` is thiscall
(low,high), RET8. It advances the positive state using Schrage constants
44488,48271,3399 and modulus2147483647. Then it scales the low24 bits by
(high-low) and float `0x6916C0 = 2^-24`.

CRT helper `0x5C4053` temporarily loads x87 control word `0x173F` with mask
FFFF via `0x5CA145`; `0x5CBFC8` executes FRNDINT with round-down. It restores
the prior control word. Conversion by __ftol, addition of low, and explicit
high->low wrap produce low-inclusive/high-exclusive results for the positive
stock state/range. MIXED passes0,3 and therefore yields native classes0,1,2.
Float rounding and low24-bit mapping are retained, not statistically certified.

The existing pool helpers request0,65535 as a seed for `srand` (`0x5C37AB`).
CRT rand `0x5C37B8` uses TLS state+0x14, recurrence
`state = state * 214013 + 2531011` modulo2^32, result `(state >>16)&32767`.
Vehicle shuffle `0x450580` and driver shuffle `0x458A80` use it. Native shuffle
at index i>=1 chooses `rand % i`, **not % (i+1)**: first swap is forced and
permutation/modulo biases exist. No replacement Fisher-Yates or uniform-class
claim is introduced.

Class input now adds **three game range draws** per qualifying setup, plus
native vehicle reseeds when a class change requires a new remaining pool.
Both shuffle routines, driver-pool construction, driver choice and consumption
are preserved exactly. The new seed consumption changes the shared stream:
same DriverIDs, CRT seed values or bit-identical stock outcomes in MIXED are
**not** promised. Drivers remain valid/distinct0..9 and are not class-filtered.
STOCK uses unchanged pristine bytes and RNG sequence. This is semantic slot
independence, not a statistical proof of independent random variables.

The native emulator scripts class range outputs across all27 combinations and
uses synthetic seed stimuli at the game-range boundary. Actual CRT srand/rand,
both native shuffles and driver helper execute as x86. Floating helper numeric
execution and real-time/global RNG state are not emulated; source analysis
establishes their contract and the human samples establish runtime variation.
