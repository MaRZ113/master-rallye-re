# R5V-I.0 human runtime plan — slot proof only

## Prelaunch

Use a disposable retail profile and the ignored staged package:

* Runtime root and working directory:
  `D:\Game\Master Rallye\master-rallye-re-vehicles\.research-output\vehicles\multislot\i0\runtime-package`
* Executable: `MRallye.exe` in that root; SHA256
  `50ff267d2758c1ff894d91bcdafd7dba4a2fa278d678a075e7767120727abbea`.
* Effective scene:
  `DataScene/FrontendScreens/VehicleSelect.xml`; SHA256
  `0b8c61efd2959a5b3b5dcef0d3810c2b445e021c465816627e87b9e3da2b4490`.
* The package includes the exact H.2 Data.sma/resource set and has no
  PlayerState or save state. Launch it with this runtime root as the working
  directory and use a fresh isolated profile.

From the repository root, run this before launch:

```powershell
python tools\vehicle_multislot_runtime_package.py verify
if ($LASTEXITCODE -ne 0) { throw 'R5V-I.0 package verification failed' }
```

The verifier checks the exact retail source, H.2 parent, I.0 EXE and inverse,
G.1-derived Vehicle Select XML, complete staged resource inventory and
package file set. Do not launch if it fails.

## Human check

1. Open Vehicle Select and navigate normally to T2. Do not bypass a locked
   class or edit PlayerState. If T2 is not legitimately available on the
   isolated profile, stop and use a profile that reached T2 through normal
   progression.
2. Inspect appended `T2_Car8`. It is intentionally labeled `SLOT PROOF` /
   `NAVARA DONOR`, uses stock Navara frame 23 and diagnostic stats 7/6/6/5.
   It is not the new T2 car. Check that the T2CupCar1 lock rule and normal
   button behavior remain coherent.
3. If naturally unlocked, select the slot and enter one short offline T2
   Quick Race. Capture `i0-id27-race`; after materialization, verify
   `Race/NumCars` is unchanged, `Race/Car0/CarID=27`,
   `Race/Car0/CarClass=1`, and Mercedes remains distinct at ID26. Verify
   `CarType`/`WheelType` reflect the Navara donor and the cyan color canary
   corresponds to physical ID27. Human observation is needed for the model,
   wheels, independent motion, collision, damage and progress.
4. Return normally and verify stock ID7/Navara, ID25/Trooper and ID26/Mercedes
   still select and display correctly. Stop at any wrong mapping, crash,
   collision/physics anomaly, lock bypass or roster corruption.
5. Do not interpret this donor test as a real independent T2 vehicle pass.
   R5V-I remains open until an independent T2 cooked family and its own
   physics/collision data are qualified.

Observatory Broker paths are supporting identity evidence, not actor proof by
themselves. The selected race actor, controls, movement and collisions need
human observation. Preserve capture/raw hashes outside Git; do not commit the
runtime package or proprietary files.
