# Locked selection and commit gate

## Stock ID3 control

Retail `VehicleSelect.xml` defines stock T1 local3 / physical ID3 as `T1_Car4`.
Its AI list contains:

* AI 0 `gaFrontendDisablerAI`, driven by `T1CupCar1 OR UnlockCars OR UnlockAll`.
* AI 2 `gaFrontendXYButtonAI`, with the slot's `Enabled` field.
* AI 3 `gaFrontendButtonUnlockerAI`, with the same three paths and
  `Control AI ID=2`.

Ghidra analysis of pristine retail maps the unlocker constructor/configuration
to `FUN_0044BEC0`; its availability callback is `FUN_0044C060` (vtable slot 5
at `0x006901F4`). The callback evaluates the configured OR gates and writes
the controlled button's `Enabled` field. `FUN_0045D0B0` publishes the current
XY button state as `UI/Enabled`; the generic positive-action handler
`FUN_0045D930` checks that state and returns the stock `Frontend/ButtonDisabled`
result instead of taking the disabled positive action.

This is the native Vehicle Select commit blocker. The relevant participant
fields are not used as a substitute for this control path.

## ID26 divergence

The previous `T1_Car8` extension was based on an always-unlocked widget. It did
not carry `gaFrontendDisablerAI` or `gaFrontendButtonUnlockerAI`; its XY control
therefore remained enabled and its image did not switch to locked art. This is
the earliest proven semantic difference from stock `T1_Car4`.

The locked capture's `FrontEnd/Network/selectedCar=26` is produced by the
highlight/cursor publication path (identified as `FUN_004AD840`). It can be
published before a commit. The coexisting `Race/Car0/CarID=26` value is likewise
not, by itself, proof of a currently instantiated or accepted vehicle. The
owner's interaction report establishes that the old UI could continue to Setup
and race; the corrected candidate still needs an ID3-vs-ID26 human check.

## Correction

The new `T1_Car8` overlay clones the locked-capable stock `T1_Car4` controls and
retains their three Broker paths and OR booleans. It binds AI 3 to XY AI 2,
which disables the ID26 button when ID3 would be locked. No race-launch guard
is added. Runtime acceptance requires both locked slots to reject the same
normal commit action and both to prevent Vehicle Setup/race entry.

## Test boundary

Synthetic tests inspect the actual stock-shaped XML control binding and the
candidate manifest. They do not execute the game's native event handler. The
human runtime oracle is:

1. on a fresh profile, highlight locked ID3 and try the normal accept action;
2. repeat with locked ID26;
3. confirm neither commits or enters Vehicle Setup;
4. repeat on a naturally unlocked profile and confirm ID26 is accepted.
