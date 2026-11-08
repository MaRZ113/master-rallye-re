# Compatibility

The mod supports the exact 32-bit retail executable with SHA256:

`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`

Other executables are rejected, even if their version text or file size looks
similar. Keep the original `MRallye.exe` unchanged.

The mod uses a local `dinput8.dll` proxy and forwards DirectInput to Windows.
It is designed to coexist with the game's existing graphical `d3d8.dll`; it
does not include, replace, or require a replacement for `d3d8.dll`.

Another modification that installs its own `dinput8.dll` may conflict. Check
its compatibility before installing, and do not overwrite it without keeping
a backup. Compatibility with other executable hooks or input proxies is not
guaranteed.

Randomizer policies are available for Quick Race, Rallye Cup, Master Rallye,
Invitation, and Challenge. Opponent-count extension applies to Quick Race only.
It is independent from vehicle add-on SDK/runtime support.
