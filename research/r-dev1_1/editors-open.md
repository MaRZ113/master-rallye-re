> **R-DEV1.2 correction:** the statement below that no producer was found for retail `+0x44..+0x47` is superseded. `005AF970` snapshots/closes open editors and writes those flags; `005AF9F0` restores and clears them. The counter owner set is now mapped to Marker and Egg. See `research/r-dev1_2/editor-lifecycle.md` and `editor-state-structure.md`.

# Editor open paths and `Editing/EditorsOpen`

## Startup-created owners

Retail `ConstructEmbeddedToolOwners` at `005AF5C0` constructs the editor/tool objects before the startup menu gate. The owner object includes Flow Builder, a large generic tree/editor object, Broker Editor, Debug log sink, Egg Editor, Particle Editor, and Marker Editor. The allocations below describe observed allocation sizes, not complete class layouts.

| Tool / object | Observed allocation | Retail construction/open anchors |
|---|---:|---|
| Flow Builder | `0x2C` | constructor `00662B20`; opener `00662D90` |
| Generic tree/editor | `0x848` | constructor `00660B30`; global `0x3F`, indexed family `0x40–0x49` |
| Broker Editor | `0x20` | constructor `0065E650`; opener `0065E990` |
| Debug log sink | `0x34` | `0064E4C0`; startup window path `0064E5C0` |
| Egg Editor | `0x8C` | constructor `0065AAD0`; opener `00657FD0` |
| Particle Editor | `0xCC` | constructor `00656CD0`; opener `006557C0` |
| Marker Editor | `0x68` | constructor `00654F50`; opener `0065B870` |

Other builds show corresponding constructors/openers in the cross-build function/command maps. The allocation sizes are constructor observations, not member offsets or complete class layouts. Construction is application-lifetime ownership; it is not a registration into a user-visible editor list.

## Window handle and duplicate behavior

Each named opener checks a stored HWND. If one exists, it activates/focuses the existing window and returns. Otherwise it creates the application window, initializes child controls, sets title/menu, populates UI, and shows the window. This is direct evidence of per-tool duplicate prevention. It does not reveal how the first opener command is produced.

A retail helper `005AF9F0` consumes four pending open bytes at application offsets `+0x44..+0x47` for Marker, Particle, Broker, and Egg. It calls corresponding owner members, then clears the bytes. The callback path is present, but no producer/setter of those flags was recovered. Treat it as a latent internal open path, not a reachable sender.

## `Editing/EditorsOpen`

The key is backed by an integer-like broker value. Retail helpers `0066C180` and `0066C380` increment/decrement it; decrement clamps at zero. Equivalent helper pairs exist at:

| Build | increment | decrement |
|---|---:|---:|
| 8.4.1 | `00550A90` | `00550C90` |
| 9.3.1 | `00626CA0` | `00626EA0` |
| 9.10.0 | `00658880` | `00658A80` |
| retail | `0066C180` | `0066C380` |

The helpers also save/restore shared editor camera/view state. Camera constructors access the same key and associated state. This supports an **editor-open counter plus editor-view bookkeeping** interpretation. The exact set of window types that increment/decrement it and all failure/teardown cases were not fully enumerated. No consumer was found that uses it to enable the hidden main commands.

The counter therefore does not solve original command reachability. It is separate from the HWND-based duplicate-open checks.

## Generic tree/editor

Global ID `0x3F` opens/creates the generic parameter editor. IDs `0x40–0x49` address indexed instances/operations through the owner's collection. `005B0720` enforces ten editor instances and reports “Maximum Number of Open Editors Reached.” Retail WndProc `00660D80` initializes the `Edit Parameters` dialog and handles its local OK/Cancel. The editor's local menu supports Commit/Cancel and Save. Its live broker semantics make it unsuitable for an open-only runtime test until further static tracing.
