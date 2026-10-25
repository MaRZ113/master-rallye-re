# Physics-family generation

An addon family uses its own Broker namespace, for example:

```text
Vehicles/MyRallyCar
```

When both `--retail-data-sma` and `--retail-data-root` are supplied,
`project-validate` and `project-build`:

1. Verify the Data.sma size and SHA256 pinned by the selected capability
   profile.
2. Read `DataGame/vehicles.xml` and `DataGame/Modifications.xml` from that
   archive.
3. Require the unpacked files at the corresponding paths to match those
   members byte-for-byte.
4. Find the donor's serialized `<Value Name="Vehicles/<donor>/..."/>` rows and
   append exact value clones under `Vehicles/<runtime_family>/...`.
5. Validate the XML, duplicate paths, clone count and donor attributes.
6. Record the generated XML paths, source hashes and output hashes in the
   offline build manifest and resource inventory.

The generated physics values are **inherited donor values**. J.3-A does not
author new suspension, engine or gearing parameters. This avoids creating
unqualified physics behavior. The original Data.sma is never modified or
copied into the build. The output is not an installable runtime package until
the native integration compiler and resource-root composer accept the same
addon collection.

If the target profile does not pin the archive, the DataGame members differ,
the donor family is absent, the target family already exists, or the stock XML
serialization differs from the audited one-line self-closing Value form, the
build fails closed.
