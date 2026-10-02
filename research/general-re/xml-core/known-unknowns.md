# XML unknowns

- Full native lexical/error grammar and encoding acceptance. Ordered typed
  attributes were recovered, but this is not a comprehensive XML parser rewrite.
- Full factory registration set and every class's failure/side-effect behavior.
- Exact numeric formatting and semantic round-trip fidelity for Matrix, vectors,
  StringList and every object class; diagnostic Dump is not a native writer.
- Whether any shipped atypical attribute layouts intentionally bypass the common
  parser family through specialized loaders.
- Behavior after missing/corrupt dependencies, including queued jobs left for a
  later frame. Successful startup ordering is established; all failure interleavings
  are not.

No independent XML writer or save editor is supplied. Metadata inspection does
not validate a candidate against the game's parser.
