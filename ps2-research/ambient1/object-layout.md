# Object layout

Owner size **0x130**, owner ID +4, vtable +8. Fields are four-byte words unless
specified. Evidence is `CONFIRMED_BY_EXE`; names describe access behavior, not
recovered source symbols. `ctor/config/prep/init/tick/eval/forward/bank/publish/
advance/trigger/dtor` below mean respectively `1a7b08/1a7dc8/1a8330/1a7ef8/
1a80e8/1a9498/1a9e08/1a9fd0/1aa308/1aa3b8/1aa438/1cef20`.

| Offset | Size/type | Meaning | Writer | Reader |
|---|---:|---|---|---|
| +00 | 4/int | Base sentinel -1 | ctor | Base owner infrastructure; not used in recovered path math |
| +04 | 4/ID | Interned owner ID | ctor | Registry lookup |
| +08 | 4/pointer | `473b10` vtable | ctor/dtor | Registry, loader, dispatcher |
| +0c | 4/ID | MarkerList name | ctor/config | prep |
| +10..+18, +24 | 4 each | Zeroed internal controls; consumer semantics UNKNOWN | ctor | No normal XML consumer established |
| +1c | 4/bool | Constant chord-time mode | ctor/config | prep |
| +20 | 4/bool | Dormant acceleration-constrained preprocessing branch; default 0, no XML writer | ctor | prep |
| +28 | 4/bool | Closed controls and advance wrap | ctor/config | prep/advance |
| +2c | 4/bool | Trigger enabled | ctor/config | init/tick |
| +30 | 4/bool | Rest on open endpoint | ctor/config | advance |
| +34, +3c | 4 each | UNKNOWN, no contractual meaning assigned | UNKNOWN | UNKNOWN |
| +38 | 4/float | Authored speed setting | ctor/config | prep/bank |
| +40/+44 | 4/float each | On/off radii | ctor/config | trigger squares them |
| +48/+4c | 4/float each | Internal accel/decel bounds, default +3/+3; absolute values after config | ctor/config | dormant prep branch |
| +50 | 4/float | Banking multiplier | ctor/config | init/bank |
| +54 | 4/int | Rest counter | ctor/advance | advance |
| +58 | 4/int | Rest invocation count after config | ctor/config | advance |
| +5c | 4/ID | Observer class `Car0` | ctor | tick Broker lookup |
| +60 | 4/bool | Active flag | ctor/init/trigger | tick |
| +64 | 4/float | `0x3d088889`, nominal 1/30 increment | ctor | advance |
| +68/+6c | 4/float each | Path time / total duration | init/advance, prep | eval/advance |
| +70/+74/+78 | 12/vector descriptor | Owned XYZ controls: begin/end/capacity, 12-byte elements | ctor/prep | eval/dtor |
| +7c/+80/+84 | 12/vector descriptor | Owned cumulative knot times, 4-byte elements | ctor/prep | eval/dtor |
| +88/+8c | 4/int, 4/float | Basis-valid flag, cached **local** coordinate | ctor/eval | eval compares against global coordinate |
| +90..+9c | 16/float[4] | Cached cubic weights | eval | eval |
| +a0 | 4/float | Closing-span time | ctor/prep | prep/eval |
| +a4/+a8 | 4/int each | Cached knot index / lookup initialized flag | eval, ctor for +a8 | eval |
| +ac | 4/bool | Evaluator closed mode copied from +28 | ctor/prep | eval |
| +b0..+b8 | 12/Vec3 | Published position | init/tick | forward/bank/publish |
| +bc..+c4 | 12/Vec3 | Previous published forward | init/tick | forward/bank/publish |
| +c8..+d0 | 12/Vec3 | Published up | init/tick | publish |
| +d4..+dc | 12/Vec3 | Published right | init/tick | publish |
| +e0..+e8 | 12/Vec3 | Current evaluated position scratch | tick | bank/tick copy |
| +ec..+f4, +f8..+100, +104..+10c | 12 each | New forward/up/right scratch | tick | tick copy |
| +110/+114/+118 | 12/vector descriptor | Owned bank history float ring | ctor/init/bank | bank/dtor |
| +11c | 4/float | Running bank average | init/bank | bank |
| +120/+124 | 4/int, 4/float | Sample count / float divisor | ctor/config, init | init/tick/bank |
| +128 | 4/int | Bank enabled when ==1 | init, **after first pose calculation** | bank |
| +12c | 4/int | Ring index, `(index+1)%samples` | ctor/tick | bank |

Constructor does **not** write +128, +124, the initial pose scratch, or the
forward cache. A valid initial displacement initializes forward; first init
calls bank before assigning +128. The allocator's zero-fill/heap-reuse contract
is not proved. No actual garbage value or fault is claimed. Diagnostic init
explicitly assumes pre-init +128=0; another first-frame state needs a capture.

Separate runtime objects: entity `0x7c`, en3d carrier `0x80` at entity +50,
marker-manager shared vector of 80-byte records, Broker wrapper with payload
pointer +8. Owner copies the relevant route XYZ into its own vector. There is
no model-family field, global elapsed time, live velocity variable or curve
arc-length sample table in this recovered layout.
