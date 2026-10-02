# Development UI and shipping transition

## What changed

The strongest documented distribution transition is the shipped `DataGame/dev.xml` value:

| Build | `Menues/Enabled` | `DebugWindow/Enabled` | Observation |
|---|---:|---:|---|
| 8.4.1 | true | true | Owner-corpus verified; owner reports Menues gate opens Debug window |
| 9.3.1 | true | true | Owner-corpus verified; owner reports Menues gate opens Debug window |
| 9.10.0 | false | false | Owner-corpus verified |
| retail | false | false | Owner-corpus verified; hash-verified retail data |

The owner's flag-isolation result is that `Menues=true` opens the native Debug window, while changing `DebugWindow/Enabled` produced no observable effect in the tested configuration. The tested build/captures were not provided, so this runtime attribution has no build-specific executable identity.

## What did not change in the recovered menu code

The main-menu builder in every build contains only `Game → Reset… / Exit`. Therefore a fuller in-game native main menu is **not** evidenced in 8.4.1 or 9.3.1 and cannot be described as removed in 9.10.0. The hidden command cases and tool-local menu builders remain in 9.10.0 and retail. The exact 9.3.1 → 9.10.0 change shown here is config-level suppression of the Menues/debug-window startup path, not removal of tool implementations.

The editor command IDs themselves move +1 between 8.4.1 and 9.3.1; handlers stay mapped afterward. The Flow local FL→SFL item first appears by 9.3.1, and the Marker local reverse-order action first appears by 9.10.0. These are tool-internal evolution, not global opener routes.

## Gate path

Startup reads the typed broker key `Menues/Enabled`. When true, it proceeds through the app's development/menu-window path. A second interface call guards Debug-window presentation, but in every recovered vtable the relevant methods return true unconditionally. No distribution-type test was found in those methods. Independently, the embedded tool owners are constructed before the Menues conditional. Thus false config suppresses presentation while leaving handlers/objects compiled into the executable.

`DebugWindow/Enabled` exists as a key/default but has no direct consumer string xref in the four executables; treat it as **ORPHANED_OR_REDUNDANT_KEY / STRONG_HYPOTHESIS**, not proven dead.

## Historical interpretation

The original binary may have relied on a development-only sender outside the shipped program, or a route omitted from these builds. Current evidence does not identify a compiler `#if`, role/capability build discriminator, fuller early menu, or surviving retail sender. The responsible next test is UI observation on verified pristine early binaries; exact hashes and provenance are in `research/corpus/executable-provenance.md`.
