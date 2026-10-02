# R5V-F.2b cache-only portability

**NOT RUN.** No runtime-generated DX cache package exists.

After the complete, car, and wheel outputs pass offline validation and the
Cook A/B gate is closed, create a fresh runtime tree with only:

```text
DataGx/Vehicles/Mercedes/complete.dx
DataGx/Vehicles/Mercedes/car.dx
DataGx/Vehicles/Mercedes/wheel.dx
DataGx/Vehicles/Mercedes/*.dxt
```

Do not place GXM/GXI files in that runtime. Remove the phase Junction using
the marked fail-closed helper, then prove that the complete preview and a short
offline race load all three DX caches without `Reading GXM`, missing-source
errors, or access to `D:\projects\MRallyeTNG`.

The `cache-only/` directory is prepared but empty. Until both preview and race
loads pass without authoring files or the Junction, the cooked package is not
portable and final Mercedes P0 remains blocked.
