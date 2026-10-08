# Marker-list contract

`MarkerList Name -> 1e28f8 -> owner+0c -> 1fde60 -> 1fdba8 -> record vector`.
`1fdba8` bounds-checks an interned ID against the manager's pointer table.
Interner `1d4040 -> 1d4280 -> 1d4758 -> 3fa760` preserves literal bytes;
there is no case folding or PackFS path normalization in marker names.
`barge` and `bargelist` are distinct route identities despite sharing a model.

`1ff6a0` walks XML List children through their next links. `1ff7a8` reads
Marker Type, Pos and Dir, and appends an **80-byte** record. It does not read
the Marker No attribute or sort by its number. Source document order is
therefore the runtime control order. The diagnostic retains raw No values
as provenance, including nonsorted synthetic numbers.

| Runtime record offset | Interpretation | Spline consumer |
|---|---|---|
| +00/+04 | Marker type/name metadata | Not read by this path prep |
| +10..+3f | Basis built by shared loader from Marker Dir | Not read by this path prep |
| +40/+44/+48 | Position X/Y/Z | Copied by `1a8330` |
| +4c | Homogeneous 1 | Not used for cubic XYZ |

Marker Dir participates in constructing the shared marker record, but it is
**not** the tangent source for `gaEntitySpline`. Neither type nor marker flags
select ambient curve geometry. XYZ are copied into an owned 12-byte-element
vector at owner +70; cumulative times go to a distinct float vector at +7c.
Runtime record count uses the EE modular inverse for stride 80, not the
misleading generic MIPS decompiler's plain `bytes >> 4` expression.

Open evaluation clamps indices to [0,N-1], so first/last controls repeat.
Closed evaluation wraps four control indices modulo N; it does not append
an extra first-marker record in the ordinary constant/equal-time modes.

Missing list pointer returns failure before use. Validly reached short-list
checks reject fewer than four controls; init schedules entity removal.
An empty vector can reach a last-time read before that count check, and
degenerate/nonfinite inputs can divide by zero. No safe runtime behavior is
claimed for those malformed cases. The diagnostic rejects them explicitly.
Shared XML loading requires Type, Pos and Dir; parse failure and later empty
list behavior remain distinct.

Six routes independently verified from named PackFS payloads: ITALY3/barge 11,
TURKEYW/bargelist 10, FRANCE1/boatlist1 6, FRANCEM/zeppelin 4,
SPAINS2/boat1 7 and SPAINS2/boat5 5. The 24-record applicability pass reuses
CDELTA1's selection and checks payload hashes, route counts and model binding;
it does not redo course pairing or reinterpret minimap Marker No policy.
