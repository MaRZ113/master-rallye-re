# Capability and distribution gates

## Startup sequence

Retail startup anchor `InitializeApplicationAndDevGate` at `005AFB20` reads `Menues/Enabled` from the typed parameter broker. The tool-owner construction routine `ConstructEmbeddedToolOwners` at `005AF5C0` runs before this check. A true value enables the development/menu-window path and reaches the separate Debug-window presentation branch. The owner has runtime-confirmed the `Menues` → Debug-window relationship; exact build/capture metadata remains unavailable.

## Interface checks

The startup path calls two virtual methods through an application interface: slot `+0x28` is used on the Debug-window path; slot `+0x2C` is used by the menu/window setup path. The recovered implementations are one-instruction truth returns in every build:

| Build | interface/vtable address | slot `+0x28` implementation | slot `+0x2C` implementation |
|---|---:|---:|---:|
| 8.4.1 | `005CF3E8` | `00403D40` | `00403D50` |
| 9.3.1 | `006463EC` | `00404030` | `00404040` |
| 9.10.0 | `0067946C` | `004041D0` | `004041E0` |
| retail | `0068F4AC` | `00404750` | `00404760` |

The methods return true; they do not inspect a version, role, license, or distribution flag in their bodies. This removes a proposed “capability denies retail editors” explanation at these particular checks. It does not prove that every indirect path in the program lacks some other condition.

## What the gate does and does not establish

- `Menues/Enabled` is a consumed startup config value; the owner confirms it controls the Debug-window outcome.
- The shipped value changed true→false between 9.3.1 and 9.10.0.
- Hidden editor command cases and editor owners remain in retail.
- The main menu remains only Reset/Exit even in early builds with `Menues=true`.
- `DebugWindow/Enabled` is not the observed gate; its consumer remains unresolved.
- No in-binary original sender for the hidden editor opener commands was found.

The vtable/class factory's naming and origin remain neutral: the data establishes these callable true-return methods and their use, not a semantic class name such as `DeveloperBuild`.
