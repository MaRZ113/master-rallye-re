# Bounded regression correction

StartingHEADf999343e20be23f199551dc4486be25e442fc5d8. User confirms wheel adoption and native steering, reports duplicate drivers and stretched tread; screenshots MRallye_DNgGaJ3Goj.png/MRallye_OyZcsgik1p.png. Session30252 confirms fourwheelowners with successful native draw/restoration; same CAR/WHEEL classifiers retained.

## Drivers

Excluding standalone PS2helmet root8 was insufficient: root0underdash contains two static bodies(101+151faces) and two facecomponents(48+48); root7chair contains two head/visor inserts(24+24). Those396faces overlap the preserved animated nativePCdrivers. Exact source-topology components are independently inventoried in ../driver-fix/components.json and pinned driver-masks.json. Semantic identification uses source topology/UV and diagnostic projection plus overlap with native character parts; mask membership is fixed for the exact asset, never a runtime bounding-box deletion rule. Bodies/faces/inserts are retained in original asset and filtered only from private race submission vectors. Root0keeps221faces:floor/dashboard/steering/underbody/arches; root7keeps6seatfaces. Helmetroot8 remains excluded. Native driver geometry, animation, texture/state and physics untouched. FullprivateCAR1436faces excludes both staticcharacters396 and standalonehelmet148 from1980unconditionalsourcefaces. This corrects the earlier coverage wording: rendering all unconditional nonhelmetfaces was not a valid native-driver-compatible composition.

Implementation: role1runtime filtered source-ordinal masks in FrontendModel; draw_race uses actual filtered vector count. Role0COMPLETE untouched; native owner, upload, suppression and material bindings unchanged. Asset hashes unchanged. C++ checks filteredroot0=221/root7=6; masktests ensure exact disjoint coverage396drop/227keep and retain steeringcomponent18/seats6.

## Tread

OriginalWHEELsource1merctread U spans[-2.159478187561035,2.830815315246582], V[.000499457, .999500513]. The shared material transaction forcedCLAMP and stretched boundary texels over the repeating strip. Source UV convention and numeric domain support Urepeat; no arbitraryUVscale or generatedtexture is introduced. Optional primaryUargument defaultsCLAMP for every prior caller; only wheel source1requestsWRAP. Existing capturedADDRESSU state and dirty-before-set rollback restore it exactly; tests assert WRAPonlyU,CLAMPV,originalTSS afterscope. All other wheel materials, authoredrubber, chrome, framebuffer sources, normals and alpha unchanged.

Both Win32Release builds24/24baseline and34/34PS2CTest plus133Pythonregressions passed; exports/generator verification passed. No originalrenderer/SDK/gameasset edit, automaticdeployment or push. Corrected visual A/B pending; no PS2pixelparityclaim.
