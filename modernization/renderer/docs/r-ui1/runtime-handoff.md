# R-UI1 closeout

`CONFIRMED_BY_RUNTIME`: the human reported both Race Select and Vehicle Select correct with R-UI1-FINAL, including neighbor order and scrolling, with no missing/overlapping thumbnails. Tested retail scenarios are accepted; all frontend screens/builds are not claimed covered.

The accepted card-row correction is automatic whenever PreserveMargins is enabled on the exact supported retail build. Use only:

```ini
[Widescreen]
InterfaceMode=2
```

Old `CarouselAlignment` keys are ignored, including zero and malformed values. No replacement toggle exists. Stock and Centered4x3 remain unchanged. Predicate, scene freshness, source-space geometry, bounded diagnostics, sticky unrelated anchors and native WORLD restore safeguards are preserved.

See [final row policy](final-row-policy.md) for exact signature/evidence and [validation](validation.md) for closeout checks. Continue with R-CAM1-A3; no further broad UI investigation is required. A specific future collision remains subject to the existing exact draw/context diagnostics.
