# Branch model

The repository keeps six long-lived branches:

| Branch | Responsibility | Intended local worktree |
| --- | --- | --- |
| `master` | Release and full integration | `D:\Game\Master Rallye\master-rallye-re` |
| `research/general-re` | EXE and runtime research, Broker, AI/UI, Observatory, renderer and loader work | `D:\Game\Master Rallye\master-rallye-re-general` |
| `research/r5t-course-archaeology` | Course formats, Courses and future GRID8 research | `D:\Game\Master Rallye\master-rallye-re-courses` |
| `research/vehicles` | Addon vehicle slots, registry, Mercedes and demo-car work | `D:\Game\Master Rallye\master-rallye-re-vehicles` |
| `research/r-demo-pipeline` | Demo/source/cooker pipeline | `D:\Game\Master Rallye\master-rallye-re-rdemo-master` |
| `research/blender-sdk` | Blender tooling, vehicle materials and multi-revision support | `D:\Game\Master Rallye\master-rallye-re-blend` |

Short-lived experiment branches are allowed. After closeout, merge their
history into one of these six canonical branches, then delete the experiment
branch. Preserve archive tags for independent milestones where they are needed
for rollback.

This branch model does not mean that the separate research results form a
single runtime-tested product. Each capability keeps its existing evidence and
validation boundary.
