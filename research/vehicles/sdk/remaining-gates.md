# Remaining gates after J.1 static implementation

J.0 remains accepted as an offline manifest/compiler foundation. J.1 now has a
compiled native launcher, exact-build runtime operation plan, isolated
resource bundle, deterministic verifiers, a no-op memory canary, and a human
handoff. No game process has been started by this phase, so the unchanged-EXE
loader is **READY FOR HUMAN RUNTIME**, not runtime-confirmed.

Before calling J.1 complete:

1. Human-confirm `--bootstrap-only` launches the exact retail file and normal
   frontend; record EXE SHA before and after exit.
2. Human-confirm `--canary-only` validates the suspended-process memory path,
   shows `IN_MEMORY_CANARY_VERIFIED`, then reaches normal frontend. This canary
   writes identical bytes and is not a semantic gameplay change.
3. Confirm the integrated process Broker `Resource Root` and prove it resolves
   the external resource root while the executable remains at the original
   retail path.
4. Run the integrated profile and confirm ID26 remains physical CarID26/T1,
   `CarType=Mercedes`, `WheelType=Mercedes`, with Mercedes model and physics.
5. Confirm retail executable hash after integrated game exit; report rendering,
   driving, and gameplay observations separately from Broker state.
6. Qualify any D3D/input/sound wrappers before allowing the integrated path
   with them. Common local proxy names are currently rejected.

The test root may receive native profile files. Only the known
`DataGame/PlayerState.xml`, `DataGame/PlayerState.xml#`, and
`DataGame/options.xml#` paths are permitted as runtime state outside the
resource index; they are preserved and excluded from asset hashes. All other
extra files or changed inventoried resources fail verification.

After J.1 runtime qualification, J.2 may qualify both addon profiles
end-to-end. J.3 may address public packaging. Vehicle Select re-entry and the
magenta marker color remain explicit runtime/release checks. No ID28 or UI
ordering work is part of these gates.
