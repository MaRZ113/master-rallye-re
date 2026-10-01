# GXM model-build pipeline exposed by logs

Retail loader 0053C3F0 reports cache/source decisions. When a valid cached model is available and caching is enabled it can load that result; otherwise it reads GXM, builds a runtime DX model, then may serialize a cache. The “out of date, missing or invalid format” message indicates format validation; timestamp-only freshness is not proven.

The build function 0054D6E0 logs and calls conditional stages:

1. special nodes including _limits, _raceline and _startpoint; moSortPlane insertion;
2. vertex welding;
3. convex hull when needed;
4. BSP when needed;
5. cylinder helpers when present;
6. 2D geometry parsing;
7. object-node handling;
8. land database construction;
9. draw-plane handling and optimization.

Retail callees include 00616F80/00616830, 006166C0, 006215A0, 00622450, 00623940, 00615600, 0054EA70, 006054D0 and 0060C9E0. “Not necessary” messages confirm stages are conditional.

Corresponding loader/builder entry points and stage-message families appear in all four builds. This maps the developer log to a real model pipeline; it does not define course physics, tag semantics, or final material/render behavior.
