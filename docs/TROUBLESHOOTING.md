# Troubleshooting

## The game starts but opponents look unchanged

Check that `MRallyeRandomizer.ini` is beside `MRallye.exe`, has
`ConfigVersion = 2`, and the desired mode is set to a non-Stock policy. Policy
edits are used for the next newly generated roster, not the current event.

## The game reports an unsupported executable

This release supports one exact retail executable build. Do not bypass the
check or rename a patched executable to make it appear compatible. Restore the
original game executable and verify its SHA256 before trying again.

## The mod does not load

Confirm that the package files are in the game folder and that no other mod
owns `dinput8.dll`. Enable `Logging.Enabled = 1`, restart, then review
`MRallyeRandomizer.log`. Do not replace the graphical `d3d8.dll`.

## Seven AI crashes with some T1/T2 player cars

Seven-AI Quick Races have shown instability in some T1/T2-player setups. The
exact cause is unknown. Use the default five-opponent ceiling or lower it if
you encounter a crash, and report the log and configuration used. Do not
interpret this as proof that a particular vehicle pool is the cause.

## Configuration is ignored

The INI is strict ASCII and must be no larger than 4096 bytes. Remove unknown
settings, duplicate keys or sections, and comments placed after values. Keep
comments on their own lines. Invalid changes are not partially applied.
