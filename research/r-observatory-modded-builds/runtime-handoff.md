# Mercedes exact-profile human handoff

**READY FOR HUMAN RUNTIME**; observational compatibility only. Keep the supplied
EXE bytes unchanged and preserve original installation/profile. Use an isolated
copy with the already-working Mercedes assets; this task does not build/import
assets. Run the supplied exact image as MRallye_merc.exe or a byte-identical
MRallye.exe copy. No DLL, feature shim or old hardening manifest on top.

Verify installed executable hash is
1fb0a1f1ba02cd05fa25f0c94558cf1b281fd12affcdc37bb3c1ca538e6c65af,
size3121214. Use this branch's adapter and the unchanged audited Observatory.
Normal developer Dump menus must be available.

1. **CONTROL:** fully fresh process, ordinary first Quick Race/Race, one human
   stock ID0/T1, three AI, Ghost off. After actors materialize, capture
   `merc-profile-stock-race`. Observe ordinary stock actor/game behavior.
2. Close process. **MERCEDES:** fresh process, normally select Mercedes ML-320
   in T1 using an eligible profile (fresh-profile availability is not promised).
   Same ordinary first four-car race. Capture `merc-id26-race` after actors
   materialize. Expected human Car0 ID26/Class0/CarType Mercedes/WheelType Mercedes.
   Observe intended model/wheels, independent movement/physics and normal AI.
3. Preserve JSON/raw pairs and observations locally. Checker remains state-only.

**No post-Results native Dump. No Restart before either capture.** Mercedes
still has the stock NULL StringList Dump crash and legacy repeated-loading
Attract false trigger. Capture during active race only, before completing it.

Capture command (substitute installed exact EXE and audited directory):

```powershell
python tools/r_ai1_observe.py --observatory '<audited-directory>' --candidate '<installed-exe>' -- capture merc-profile-stock-race
python tools/r_ai1_observe.py --observatory '<audited-directory>' --candidate '<installed-exe>' -- capture merc-id26-race
```

Use one command in each respective fresh process. Captures go to this checkout's
ignored .research-output/r-observatory-modded-builds/observatory area.

```powershell
python tools/research_build_profiles.py check-vehicle '<installed-exe>' '<control.json>' --slot 0 --expected-id 0 --observatory '<audited-directory>'
python tools/research_build_profiles.py check-vehicle '<installed-exe>' '<merc.json>' --slot 0 --expected-id 26 --observatory '<audited-directory>'
```

Automatic status: BROKER_STATE_MATCH_ONLY. Human visible actor confirmation and
successful live capture under the exact profile are the next closeout gate.
No integration, new vehicle,9+ or mod packaging test is part of this handoff.
