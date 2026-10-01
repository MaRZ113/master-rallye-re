# Embedded toolchain graph

1. Loose DataGame XML is preferred; Data.sma is the fallback.
2. The XML parser updates the typed broker. XmlFilename entries queue more DataGame XML, including Dev and Editors.
3. Startup reads Menues/Enabled and requests the ordinary menu and, on a second capability path, the Debug window.
4. WM_COMMAND dispatch reaches a large command switch. The mapped retail menu registers only Reset and Exit.
5. BuildData scans a directory recursively for DataGx paths and delegates to normal GXM/GXI/bank loaders. Model/texture loaders may read or overwrite DX/DXT caches.
6. Flow Builder reads .sf selection state, builds flow outputs, and has an FL-to-SFL sibling converter.
7. Broker/Game/Scene edits remain in memory until explicit XML Save. Serialization filters values, queues writes and uses CREATE_ALWAYS.

This graph distinguishes supported call/data edges from unknown user reachability and indirect write behavior. Machine-readable edges are in toolchain-graph.json.
