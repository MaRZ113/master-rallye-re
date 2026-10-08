# Reproducible offline diagnostics

`tools/reflection_runtime.py` provides four bounded modes:

1. `inspect`: canonical named Tata/Kia CAR.PSM -> visual mesh/material/strip
   metadata and source metrics; not collision data or captured visibility.
2. `resources`: nine selected canonical GXIs -> existing-decoder properties and
   original range/hash provenance; no speculative format conversion.
3. `coordinates`: explicit normal, two object and two view matrices, interpolation
   weight and base UV -> original normal mapping in host float32 operation order.
4. `contract`: compact executable-derived texture/pass/GS/VIF lifecycle contract.

```powershell
python ps2-research/tools/reflection_runtime.py inspect --input 'D:/Game/Master Rallye PS2' --model TATA --output ps2-research/data/refl1/tata.json
python ps2-research/tools/reflection_runtime.py inspect --input 'D:/Game/Master Rallye PS2' --model KIASPORTAGE --output ps2-research/data/refl1/kia.json
python ps2-research/tools/reflection_runtime.py resources --input 'D:/Game/Master Rallye PS2' --output ps2-research/data/refl1/resources.json
python ps2-research/tools/reflection_runtime.py coordinates --inputs-json ps2-research/refl1/synthetic-coordinate-input.json --output ps2-research/data/refl1/synthetic-coordinate.json
python ps2-research/tools/reflection_runtime.py contract --output ps2-research/data/refl1/contract.json
```

Source modes verify all four canonical hashes/sizes before PackFS reading.
Unknown/missing inputs fail closed. Decoder defaults remain strict for WATER1;
the vehicle explicitly supplies tag7/8 readers and terminal101. Diagnostics
cannot escape ignored data/refl1, overwrite a multiply linked file or redirect
through a resolved symlink outside that root.

Full source coordinates/mesh dumps are excluded from Git and the handoff archive.
Committed vehicle-evidence contains only counts, bounds, IDs, offsets, hashes and
selected compact associations. The small synthetic matrix example is not copied
from original vehicle geometry or a frame.

Independent paths are original PSM material/tag/strip bytes, canonical ELF role
instructions and VU pairs, shared texture-loader/consumer fields, freshly checked
embedded MPG hashes, and separately constructed synthetic mathematical cases.
Tests do not construct expected proprietary data using the same parser. Passing
the evaluator establishes these formulas/inputs, not captured runtime parity.

Precision: source hashes/offsets/words are exact bytes; GS bit fields are
EXACT_ELF_OPERATION semantics; matrix/normal/color evaluation is
FLOAT32_RECONSTRUCTION; geometry bounds/count diagnostic calculations use
MATHEMATICALLY_EQUIVALENT host arithmetic with declared tolerances. Live FCSR,
VU ACC details, converted VRAM pixels and complete GS inheritance are UNKNOWN.

No trusted PCSX2/debugger session was running during the bounded process check.
Runtime validation is NOT_PERFORMED. A future read-only capture should:

1. Record canonical ELF/disc hash, emulator version/configuration, course,
   selected Tata model/camera and frame identity.
2. Break at32f988 and33257c/3325c8. Record42dd34/38, handles49b380/388 and
   resolved descriptors; capture target contents before and after each sprite pass.
3. Identify runtime root.3 carshiny mesh by its source/material association;
   capture mode3, mesh+dc/+e4 and actual TEX0/ALPHA/TEST/ZBUF/FRAME/CLAMP/TEXA.
4. Dump live VU code around2cf/30e/408 and data319.w/608..619, plus the actual
   object/view packet inputs. Compare them with the original embedded program.
5. Correlate that mesh/draw with a frame, then rotate camera and vehicle separately.
   Capture a second target generation to distinguish changing image from changing UV.
6. Repeat one glass mesh and split-screen gate if practical; do not modify the ELF.

Only this source->updated target->selected consumer->visible frame chain could
upgrade independent runtime evidence. A synthetic normal preview cannot.
