# VEHICLE-LIGHT1 runtime check

Replace `d3d8.dll` (assets from fix8.2 unchanged). In `PS2Port.ini` add `VehicleLighting=1`
(default when absent). Compare the same car/course/camera with `VehicleLighting=0`.
Good candidates: the blue BFGoodrich car and UFO from the earlier PS2/PC screenshot pairs.
Expected with 1: darker, normal-shaded paint (roof brighter than sides), decals readable,
environment visible as an additive highlight rather than a uniform blue sheen.
Glass is not changed in this step.
