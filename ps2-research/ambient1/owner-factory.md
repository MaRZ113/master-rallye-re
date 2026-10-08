# Owner, factory and lifecycle

All addresses refer to ELF SHA256
`b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2`.
Roles below are `CONFIRMED_BY_EXE`; selected XML-to-owner binding is
`CONFIRMED_BY_BOTH`. Generic Ghidra argument guesses are replaced with audited
EE integer/FPU register arguments in `elf-functions.json`.

| Step | Executable evidence | Result |
|---|---|---|
| Name registration | Name at `475658`; `1cdd54 -> 1d4040`; destination `48e1d0` | Interned `gaEntitySpline` ID; this is a callsite inside static initialization, not a constructor entry |
| Prototype construction | Factory `15b190`, audited `15d374..15d384` | Allocate `0x130`; `15d37c -> 1a7b08`; append prototype |
| Constructor | `1a7b08` | ID from `48e1d0` into +4; vtable `473b10` into +8 |
| Registry resolution | `1fc500`, called by `1fc4c0` | Compare requested ID with prototype +4; virtual +14 clone |
| Clone | `1cefc0` | Allocate `0x130`, call constructor; no path/state copy from prototype |
| Egg hatch | `292a48` | Allocate entity `0x7c`; model carrier at entity +50; resolve up to four AI slots |
| Config | Loader invokes virtual +24 -> `1a7dc8` | `a0=owner`, `a1=entity`, `a2=owner XML node` |
| Attach/init | `21e620` -> virtual +34 -> `1a7ef8` | Store owner at entity +4+4*slot, prepare route, publish initial matrix |
| Tick dispatch | `21f088`, virtual +2c -> `1a80e8` | Walk priority queues 6..0 and owner slots 0..3; frozen/removed entities can be skipped |
| Pose publication | `1a80e8 -> 1aa308` | All sixteen world-matrix words written before time advance |
| Destruction | entity destructor `21e3c8` -> virtual +c -> `1cef20` | Free sample history, release path containers through `1cee20`, delete owner when flags request it |

Vtable `473b10` has eight-byte adjustment/function pairs: destructor +c,
clone +14, schema +1c (`1a7c50`), config +24, update +2c, init +34.
The corresponding this-adjustments for these entries are zero. Entity/model
pointers are passed to owner methods; they are not persistent owner fields
invented from a misleading decompiler signature.

`1a7ef8` calls setup `1a8330`. A missing named list or a safely reached setup
failure returns zero; init prints "Spline %s failed setup - killing it, check
XML!" and invokes deferred entity removal `21e4f0`. That removal is not trigger
deactivation. Empty/malformed route arithmetic is not guaranteed safe before
the late count check; see [marker contract](marker-list-contract.md).

The neighboring `gaEntitySplineFlyBy` (`473ad0`, ctor `1aa480`, update `1aaa80`)
is a different owner. Its camera logic, allocation size and defaults are not
substituted for ambient behavior. Mid-function query probes were excluded from
the committed function inventory. No complete static initializer entry or
whole-registry size was guessed.
