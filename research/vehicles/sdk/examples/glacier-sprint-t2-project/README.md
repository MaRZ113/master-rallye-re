# Glacier Sprint T2 — metadata-only project example

This example demonstrates an independent T2 addon identity and policy set.
It does not include the Navara donor DX/DXT assets. It is not a historical
Master Rallye vehicle, and its synthetic ID27/T2/local7 plan is not a runtime
qualification for the GlacierSprint identity.

To author locally, copy compatible donor resources you are entitled to use to
`assets/source/Navara/` or point `source_vehicle_dir` in
`vehicle-project.json` at your own donor folder. Run `mrtool addon
project-validate` and `project-build` as described in the SDK J.3 Quick Start.
No SDK source edits are needed to change the family, display name, stats,
marker color, unlock/audio profile, AI membership or Results label.

The current production launcher still requires its explicit Mercedes +
R5VQualifier reference collection; do not launch an offline Glacier Sprint
build through that reference bundle.
