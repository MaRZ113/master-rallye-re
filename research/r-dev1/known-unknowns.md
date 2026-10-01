# Known unknowns

1. Does DebugWindow/Enabled independently gate anything?
2. Which capability-vtable implementation is selected per build/distribution?
3. What exact start path does BuildData receive from the path service?
4. Who frees command objects stored by 006018E0, and when is its pointer array cleared?
5. Is there another legitimate retail UI sender for editor IDs not in 005B1320?
6. What are complete layouts/semantics for Egg, Particle, Marker, Flow and the 0x848 tree object?
7. Are DataEditors help files in an archive or separate developer package?
8. What are the exact .sf columns and per-cell FL-to-SFL semantics?
9. Which Flow Builder output suffix is written by each mode and where is the base path?
10. Do image-bank descendants write output/cache files, and with what overwrite mode?
11. Does 006FE040 reset anywhere outside the BuildData wrapper?
12. What overwrite flags does the common save dialog use?
13. What happens when Dev.xml or Editors.xml is missing/malformed?
14. What consumes Scene/StartScene outside the visible corpus values?
15. What UI and values do Camera0 switch flags control?
