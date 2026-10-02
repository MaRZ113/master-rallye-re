# General-RE worktree consolidation record

Checked 2026-10-02 from `master-rallye-re-general` on
`research/general-re`. This phase reused the existing persistent checkout and
created no branch or worktree. `research/general-re` is at accepted commit
`2d5c2125fe7759d7f0db79489ee0f8f2b06f9db2`; its first parent is the pristine
demo provenance correction `f90259f3450d8e1f01915e1310e1fab1a1a511fe`, and
the accepted R-EXE1, R-DEV1, R-DEV1.1, R-DEV1.2, and corpus provenance files
are present in its history/tree.

## Current linked worktrees

| Worktree | Branch / HEAD | Reachable from general-RE HEAD? | Recommendation |
|---|---|---:|---|
| `master-rallye-re` | `research/r5t-course-archaeology` / `74aa02f3ffdfe086a118dda61e1d18e53b6151f2` | No | Keep. This is the active course archaeology checkout; do not alter it. |
| `master-rallye-re-e0.1` | `research/r5v-f-2b-native-mercedes-cook-proof` / `726b65d4b2874e9fefac30483817818cd148f2d8` | No | Keep. Its work is outside this general-RE phase. |
| `master-rallye-re-general` | `research/general-re` / `2d5c2125fe7759d7f0db79489ee0f8f2b06f9db2` | Yes (self) | Persistent general-RE home. |
| `master-rallye-re-r-dev1` | `research/r-dev1-embedded-tools` / `5cea4d7a37a43eefcf3f9127289f623c61c80511` | Yes | Commit is consolidated; consider cleanup only after a separate local/ignored-file check. |
| `master-rallye-re-r-dev1-1` | `research/r-dev1-1-command-reachability` / `f90259f3450d8e1f01915e1310e1fab1a1a511fe` | Yes | Commit is consolidated; consider cleanup only after a separate local/ignored-file check. |
| `master-rallye-re-r-dev1-2` | `research/r-dev1-2-editor-lifecycle` / `2d5c2125fe7759d7f0db79489ee0f8f2b06f9db2` | Yes (same accepted tip) | Commit is consolidated; consider cleanup only after a separate local/ignored-file check. |
| `master-rallye-re-r-exe1` | `research/r-exe1-whole-program` / `27583d3629081a69382609c17171cca59d310113` | Yes | Commit is consolidated; consider cleanup only after a separate local/ignored-file check. |
| `master-rallye-re-rdemo` | `research/r-demo-pipeline` / `0fb0a6ff6d89f2fbca5f6600578a2614b9b8f91a` | No | Keep until its separate pipeline/release history is intentionally reviewed. |

Reachability was checked with `git merge-base --is-ancestor`. This table does
not assert that any linked checkout is free of uncommitted or ignored local
data. No old worktree was deleted or modified, and the active course worktree
was not inspected beyond the read-only linked-worktree listing.
