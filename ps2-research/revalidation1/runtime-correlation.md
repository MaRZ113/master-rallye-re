# Runtime correlation evidence

## Artifacts available

The checkout contains `ps2-research/pc-port/runtime-ab.md`, which documents
the earlier user-provided runtime result. It does not contain the source
F10 logs, screenshots, raw D3D8 state trace, or capture metadata for the
France1 runs. The `ps2-research/data/treeblend1/revalidation1-cases.json`
file is local ignored analysis output, not runtime data and not part of the
handoff.

The separate `D:\Game\Master Rallye\!backup\handoff` folder contains older
handoff files, not raw PILOT1.3 captures. Those files were not used as if they
were France1 four-mode evidence.

## Carried user observations

The user reported:

- 5,364 successful `ps2_port_draw_identity` events with `override_applied=true`;
- the target call `DrawIndexedPrimitive(4,11940,28,22944,48)` in F10 frame 7608;
- the same call in Stock frame 4311 without override;
- temporary alpha-test, alpha-blend and depth-write changes followed by restore;
- target ordinal 46 of 704 in the enabled frame, with many later depth-writing draws;
- visible foreground bush loss under mode 1; partial visibility near/through
  neighboring foliage.

The new four-mode observations supplied with the request are:

| Mode | User-observed result |
|---:|---|
| 0 | Bush visible under Stock |
| 1 | Bush nearly invisible |
| 2 | White rectangular foliage cards; depth write preserved |
| 3 | Bush nearly invisible; only depth write overridden |

All observations above are graded `USER_RUNTIME_OBSERVATION`. Their
underlying artifacts were not available for independent replay or frame/state
correlation. No `CONFIRMED_BY_RUNTIME` claim is made by this audit.

## Correlation boundary

The source geometry match and original executable contracts make the target a
strong intended candidate. The missing raw trace prevents this audit from
independently proving that the logged draw used the expected current resource
generation and exact course owner. The prior implementation report's
classifier tests remain code-level evidence; they do not substitute for raw
runtime capture review.
