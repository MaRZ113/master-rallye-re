# R-DEV1.1 findings — hidden command reachability

Status: static reconstruction complete for the executable's native menu trees, main command dispatch, embedded editor open paths, and open-only write-safety. No hidden command was sent to a running game by the research agent.

## Answer to the phase question

Across 8.4.1, 9.3.1, 9.10.0, and retail, the executable contains editor command handlers and the owners/windows needed to open the tools. The in-binary UI evidence does **not** show a fuller developer main menu in the early builds. Every recovered main-menu builder creates only `&Game → &Reset... / E&xit`. The main window's `WM_COMMAND` procedure forwards messages to a much larger dispatcher, but the mapped tool IDs are not registered by the main menu, dialogs, accelerators, or other recovered senders.

The shipped early `Menues=true` setting enabled the native development/debug window path; the owner also runtime-confirmed that gate. It did not, in static menu construction, add editor items. Each editor has its own dynamically constructed local menu, but those menus are attached only after the corresponding editor window is opened. That explains how a developer used an already-open editor, but not how the editor was first opened.

Therefore the best-supported conclusion is: **the supplied executables prove embedded tools and their command IDs, but do not prove an original in-game sender for opening them.** The missing sender may have been external to the shipped executable, supplied by a development harness/build environment, or otherwise absent from the analyzed code. Those are hypotheses, not findings. No tool is assigned reachability class B or C without a recovered sender. No handler is class E because its case is still reachable from the main window procedure.

## Command path and tool lifecycle

```text
startup parses DataGame config
  ├─ Menues/Enabled → capability-checked native development/debug-window path
  └─ construct embedded tool owners before that gate

main HWND WM_COMMAND → main dispatcher
  ├─ Game subdispatcher
  ├─ Scene subdispatcher
  └─ hidden tool IDs → opener / command object
       └─ create editor HWND → attach that editor's own local menu
```

The main dispatcher is called by the main window's `WM_COMMAND` handler in each build. The analysis found no other direct code reference that invokes it. The seven recovered `SetMenu` roots are the main window plus Particle, Egg, Marker, Broker, Flow, and the generic parameter/tree editor. Resource and API audits found no static `RT_MENU` or accelerator sender that bridges the hidden main IDs into that path.

Direct decompilation plus reads of referenced string data resolved the local menus' exact captions and state conditions across all four programs. This also corrects two inferred local-menu details from the earlier narrow map: Egg `Hatch Egg(s)` (`0x10`) is enabled while `UnHatch Egg(s)` (`0x11`) is disabled; generic tree editor local ID `0x03` is `Cu&t` (not New). Retail Edit Method captions resolve to `en3d`/`en2d`; the same bytes were checked in each earlier program.

Tool owners are constructed at application initialization before the `Menues` gate. Their existence is not evidence that their command can be reached by a normal user. Openers keep/check a window handle and activate an existing instance instead of creating duplicates. The generic editor uses an owner-held collection with a visible maximum of ten editor instances.

## Cross-build result

The native main-menu tree is identical in scope in all four builds. Five tool command IDs shift by one from 8.4.1 to 9.3.1, then remain stable through retail:

| Tool | 8.4.1 | 9.3.1 | 9.10.0 | retail |
|---|---:|---:|---:|---:|
| Broker Editor | `0x26` | `0x27` | `0x27` | `0x27` |
| Egg Editor | `0x2D` | `0x2E` | `0x2E` | `0x2E` |
| Flow Builder | `0x2F` | `0x30` | `0x30` | `0x30` |
| Marker Editor | `0x3A` | `0x3B` | `0x3B` | `0x3B` |
| Particle Editor | `0x49` | `0x4A` | `0x4A` | `0x4A` |

Game and Scene open/save families are likewise mapped in each build. BuildData's retail `0x58` case constructs a command object and immediately invokes its virtual execute slot; no equivalent earlier handler has yet been matched. This is “no matching handler recovered,” not proof that earlier binaries had no related functionality.

The meaningful 9.3.1 → 9.10.0 transition is in shipped config, not a newly discovered menu removal: `Menues/Enabled` and `DebugWindow/Enabled` change from true/true to false/false, while the hidden dispatchers and local tool menus remain. The owner-isolated observation establishes `Menues/Enabled` as the Debug-window gate. The native main menu was already limited to Reset/Exit in 8.4.1 and 9.3.1.

## Safety decision

- **Flow Builder: SAFE_OPEN_CANDIDATE, open-only.** Its opener creates the window, populates controls, attaches its local menu, and shows it. No file read or write was found on that open-only path. Its separate Clear, Speed Matrix, FL→SFL, and Build actions must not be invoked during an inspection-only test.
- **Broker Editor: DO_NOT_RUNTIME_TEST.** Opening ensures two broker registry entries through generic registry calls. One helper appends a node and increments a registry count when a key is absent. The keys' semantics and effects are not fully resolved, so an open is not proven read-only with respect to shared broker structure.
- **Egg, Marker, Particle, and generic tree editor: UNKNOWN / DO_NOT_TEST.** No disk writer was found on the mapped opener paths, but live broker, model/list, and editor-state side effects are not sufficiently bounded.
- **BuildData and Game/Scene Save: unsafe for this phase.** BuildData recursively loads resources and its ordinary loaders can replace cache files. XML save handlers reach `CREATE_ALWAYS` writers. They remain excluded from all proposed runtime tests.

An external trigger helper is included only for the single Flow Builder open command. It accepts no arbitrary command ID, requires the exact retail EXE SHA256, finds a visible top-level window with a native menu belonging to that process, and requires both an explicit flag and a typed phrase before sending `WM_COMMAND 0x30`. It has not been run against the game.

## Corrective pass status

`corrections.md` records the owner-provided flag-isolation result, the shipped XML values, the `006FE040` BuildData reset correction, the portable case-insensitive config lookup/test correction, and the early EXE provenance correction. The corrective pass is separately committed before this phase's research.

## Identity and provenance

The current 8.4.1 and 9.3.1 corpus files are now canonical pristine sources with verified hashes listed in `research/corpus/executable-provenance.md`. Earlier detailed demo analysis used research-modified copies. The prior early-demo Ghidra projects were built from research-modified copies. Their static exports are reused as reference evidence with the provenance correction and narrow contamination recorded in `research/corpus/executable-provenance.md`. The `.rsrc` byte ranges match the current pristine files, and the PE UI inventory was checked against those resource sections. The old program inputs are patched copies; see the provenance record. 9.10.0, retail, and retail `Data.sma` match their recorded identities.

## Evidence boundaries

- **CONFIRMED_BY_EXE:** function bodies, call paths, menu-builder code, dispatch cases, PE resource tables, and selected assembly/xref results.
- **CONFIRMED_BY_CORPUS:** shipped XML values and corpus file identities.
- **CONFIRMED_BY_RUNTIME:** owner-isolated `Menues/Enabled` Debug-window result; executable/build and captures remain unspecified.
- **STRONG_HYPOTHESIS:** no in-game original tool opener route in the analyzed executable; external development UI/harness may have supplied one.
- **UNKNOWN:** original sender mechanism, exact capability-object factory semantics, editor teardown semantics, and Broker Editor registry-key meaning.

## Analysis record

- Branch: `research/r-dev1-1-command-reachability`, based on completed R-DEV1 commit `5cea4d7a...` through corrective commit `bb5527c`.
- Ghidra: 12.0.4; selective PyGhidra decompilation of copied existing projects and raw PE resource inspection. No full decompile dump is committed.
- Earlier R5T checkout: read-only reference; no edits, staging, checkout, stash, reset, or commit.
- Runtime: none by the research agent; runtime observations in the report are explicitly attributed to the owner.
- The canonical 8.4.1 and 9.3.1 pristine EXEs are independently hash-verified and can be used for future runtime/static work. Earlier detailed analysis used research-modified copies; see `research/corpus/executable-provenance.md`.
