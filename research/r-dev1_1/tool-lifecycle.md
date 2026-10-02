# Embedded tool lifecycle

## Shared lifecycle pattern

1. Application initialization allocates tool-owner objects before the startup Menues gate.
2. The main `WM_COMMAND` switch calls an opener or constructs a one-shot command object.
3. A normal window opener checks its stored HWND, activates it if already open, otherwise creates the window and controls, attaches its dynamic local menu, populates data, and calls `ShowWindow`.
4. The local WndProc dispatches local menu IDs; those IDs are a separate namespace from global opener IDs.
5. Closing routes through the tool's local close command / application-window wrapper. A complete destructor and all shared ownership releases were not reconstructed here.

## Owner map (retail)

| Object | Constructor / allocation | Opener | Window/event role | Lifecycle evidence limit |
|---|---|---|---|---|
| Flow Builder | `00662B20`, `0x2C` | `00662D90` from global `0x30` | WndProc `00662E00`, local menu `00662FB0` | Open-only chain mapped; tool actions have output effects. |
| Generic tree/editor | `00660B30`, `0x848` | `005B0720` and `0x40–0x49` family | WndProc `00660D80`, local menu `006644C0` | Up to 10 instances; internal collection details partial. |
| Broker Editor | `0065E650`, `0x20` | `0065E990` from `0x27` | WndProc `0065EA90`, dispatch `0065EC40`, edit `0065F170`, menu `0065EEB0` | Shared broker registry and open side effects not fully resolved. |
| Egg Editor | `0065AAD0`, `0x8C` | `00657FD0` from `0x2E` | local menu `00657750` | Live object/list/model population; safety unresolved. |
| Particle Editor | `00656CD0`, `0xCC` | `006557C0` from `0x4A` | WndProc `006559E0`, local menu `00655370` | Live particle population and broker/config helpers; safety unresolved. |
| Marker Editor | `00654F50`, `0x68` | `0065B870` from `0x3B` | local menu `0065AF40` | Live marker/list state; safety unresolved. |
| BuildData command | constructed at `005B2960` | global `0x58` case | vtable `00692F88`; execute slot `+4` at `005B2F80` | Synchronous resource walker; cache writes possible. Not an editor HWND. |

The pending-open helper at `005AF9F0` can invoke Marker, Particle, Broker, and Egg openers from queued flags, but no setter for those flags has been found. It is the only additional internal route surfaced in this pass and is not classified as a user-facing route.

## Command enablement and registration

The tool objects are created independent of the global command switch. Their local menus are built when their windows are opened; no global menu item enables/disables the parent commands. No data-driven editor command list or registered toolbar/accelerator route was found in the examined binaries/resources. Exact editor teardown ownership, queued-flag source, and any outside development harness remain unresolved.
