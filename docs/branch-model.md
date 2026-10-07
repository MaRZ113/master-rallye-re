# Branch model

`master` is the canonical public branch, active development branch, and integration branch. New executable, Broker, AI/UI, runtime, vehicle, course, Blender, renderer, and tooling work is integrated into `master`.

Historical branches remain available for provenance and archival review. Their presence does not make them active development destinations or establish that they are safe to delete. Reactivate one only when explicitly requested.

| Branch | Current role |
| --- | --- |
| `master` | Canonical public and active development branch |
| `research/general-re` | Consolidation line promoted into `master`; retained temporarily as a reference |
| `research/vehicles` | Historical research branch; archival audit pending |
| `research/r5t-course-archaeology` | Historical research branch; archival audit pending |
| `research/r-demo-pipeline` | Historical research branch; archival audit pending |
| `research/blender-sdk` | Historical research branch; archival audit pending |

The repository contains both released supporting code and ongoing research. Presence on `master` does not mean that every capability is released, production-ready, or runtime-confirmed. GitHub Releases remain the packaging boundary for public tools and builds.
