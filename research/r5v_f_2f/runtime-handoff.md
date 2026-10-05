# R5V-F.2f runtime handoff

## Candidate

- Clean retail source: exact hash-pinned `MRallye_orig.exe`
- Source SHA-256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
- F.2f executable: `research-output\r5v_f_2f\candidate-verified\MRallye_id26_mercedes_f2f_frontend.exe`
- Candidate SHA-256: `1fbb3489208de9bc0af3802902a8611ea9a149c245031d1563960bd91b430c14`
- Size: `3,121,214` bytes

Use a disposable offline copy of the existing F.2e runtime package. Keep its `Data.sma` and Mercedes DX/DXT payload unchanged; place the F.2f executable there as `MRallye.exe`. Do not overwrite the F.2e candidate or use the pristine installed game directory.

## P0 — frontend identity

1. Launch the isolated F.2f copy.
2. Enter Vehicle Select. Verify T1=8, T2=7, T3=12.
3. Select T1 local7 / physical ID26. Verify manufacturer `MERCEDES`, model `ML-320`, Mercedes preview and textures, and stats 4/3/6/5.
4. Enter the Quick Race main screen. Verify the combined identity is `MERCEDES ML-320` and no `GALOCAL UNKNOWN` appears.
5. Enter Race Options. Verify the separate visible manufacturer and model lines are `MERCEDES` and `ML-320`. If capturing Observatory, save label `f2f-race-options` and preserve its paired dump outside Git.
6. Return to Quick Race, enter Race Options again, and verify the two strings remain correct after the second transition.
7. Select stock T1 ID0 and verify its normal identity. Return to ID26 and verify the Mercedes strings again.
8. Verify ID25/Trooper remains separately selectable and normal.

Stop if any P0 identity or stock-regression check fails. This P0 does not require a full stage or Results.

## P1 — short race regression, only after P0 passes

Run one short offline Quick Race. Verify the Mercedes model and textures, normal controls/physics, and one ordinary collision. If Broker is available, confirm `Race/Car0/CarID=26`, `CarClass=0`, `CarType=Mercedes`, `WheelType=Mercedes`, and colour `[1,0,0,1]`. Do not extend this to an unnecessary full-stage/results qualification.

Report P0 and P1 separately. The current owner report for F.2e is a core gameplay pass; it does not transfer runtime acceptance to this new F.2f hash.
