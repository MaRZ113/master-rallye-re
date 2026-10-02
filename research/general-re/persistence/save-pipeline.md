# Serializer, queue, backup and writer

## Ownership chain

```text
005229B0(logical-file, mode)
  → 0052D700 job callback
  → 0052EFB0 Game root → 005FE460 Broker filter → 005FE580 typed Value
  → 005FDCA0 / 004E1D60 XML text sink
  → 005FC9C0 / 005FDC10 copy serialized bytes into owned queued job
  → 0054A340 pump → 0054A4B0 write queue
```

The caller releases its temporary XML/tree/text after the job owns a byte copy.
This is deferred IO, not an XML serializer calling WriteFile directly for each
entry. `005417D0` supplies the backend root; writer joins that root with the job
relative path and normalizes slash direction. Target is a loose file, not a
Data.sma replacement or archive update.

## Confirmed existing-file backup

Writer `0054A4B0`:

1. Probe candidate with `0064D070`.
2. If it exists, append literal **`#`** (`006E9054`) to the original path.
3. `0064D050` sets the backup file's attributes to FILE_ATTRIBUTE_NORMAL;
   it does not delete it.
4. `0064D030(backup, original)` calls **CopyFileA(original, backup, FALSE)**.
   FALSE permits replacing the previous backup. Copy failure takes the error
   callback and returns before the writer's truncating open.
5. `0064D530(original, 1, 0)` calls CreateFileA with GENERIC_READ|GENERIC_WRITE,
   read/write sharing, **CREATE_ALWAYS**, FILE_ATTRIBUTE_NORMAL.
6. `0064D830` calls WriteFile and checks the requested byte count.
7. Success `005FCB30` or failure `005FCA90` invokes the job's virtual callback;
   wrapper destruction closes the handle.

For `DataGame/PlayerState.xml`, backup is `DataGame/PlayerState.xml#`.
It is one generation, not an append-only history. No temporary file plus atomic
rename was found on this chain. After CREATE_ALWAYS, write failure may leave
truncated/partial output. No automatic backup restoration was recovered.

## Important fallback boundary

The existence probe uses the resource read layer, which can see archive members.
The backup is **CopyFileA of the loose physical path**. If the only “existing”
candidate is in Data.sma, copy can fail before new output is opened. This is a
`STRONG_HYPOTHESIS` for archive-only save targets, based on probe/copy mismatch;
it requires a disposable runtime test before broad Game saving. Ordinary options/
PlayerState loose-file round trips are the lower-risk first experiment.

Read-only handling/error UI varies by caller. The direct write job logs an IO
error through its vtable. Recovery, durability after crash and safe overwrite of
every registered group have not been runtime-confirmed.
