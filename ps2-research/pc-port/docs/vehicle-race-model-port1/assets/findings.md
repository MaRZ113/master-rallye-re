# X-Trail CAR source conversion

Original `\TNG\DATAPSM\VEHICLES\XTRAIL\CAR.PSM` was independently decoded through the established strict vehicle grammar. SHA-256: `af57572e92ce47d810666779fb60c8c178f1979feb203416131a3acc81449326`. It is not COMPLETE: 3,292 source vertices versus 6,606; 31 source mesh records including named/indexed visibility branches.

`convert_car.py` produces only the 20 unconditional roots, 1,980 non-ADC, nondegenerate source triangles. The ignored local `XTRAIL-CAR.ps2model` uses the existing PS2MDL02 layout, 495,343 bytes, 24 original GXI textures. SHA-256: `a15ee827bc93e7a7fe242d8ba2440afe1991cd06e8aeee15ce78b836e372ccac`. No raw assets are committed. Original attributes remain unchanged; the accepted frontend runtime primary-V correction belongs in the consumer, not in original data. Source mode 0 root18 uses the original verified default.gxi rather than a guessed texture.

The excluded 11 mesh records include `blight` off/on/glow and side/front screen branches. They cannot all be rendered together. Retain original PC branch behavior until a current live branch identity join exists. Root19 is unconditional windscreen material20; dynamic screen subsets remain separate. Root8 contains helmet-textured geometry. This must be accounted for against PC driver geometry; do not leave duplicate PC and private PS2 driver surfaces.

## Wheels

Original `XTRAIL/WHEEL.PSM`: SHA `d53360eab52761fdadf1a4d5a2c87196be7674fbbb603c41cd4726a4b303773c`; 300 vertices, three meshes, 252 source triangles. Separate wheel local coordinates, no named branches or matrices. The proved post-tree tag102 cylinder auxiliary stores approximately 0.4 and 0.2, and is not a visual transform. Root0 mercwheel643/rubber, root1 merctread/rubber, root2 jumpwheel64/chrome. Carshiny preserves authored rubber secondary for the first two; the original reflection material resolver replaces non-rubber secondary for the last.

Do not attach WHEEL vertices to chassis WORLD. Runtime steering, suspension and rolling transforms belong to each original native wheel instance. This converter intentionally does not admit wheel replacement; retaining native PC wheels is the safe initial chassis pilot.

## Reproduce

Run from repository root:

```powershell
python ps2-research/pc-port/docs/vehicle-race-model-port1/assets/convert_car.py
python -m unittest discover -s ps2-research/pc-port/docs/vehicle-race-model-port1/assets -p test_car.py -v
```

Five focused source-contract tests pass, including conversion replay from original inputs. These are source/asset checks, not runtime transform or visual-parity proof.
