# Editor lifecycle objects — conservative retail structure

This is a partial, offset-based layout. It names only members supported by reads, writes, or argument flow. It is not a complete C++ class reconstruction.

## Application object used by the snapshot/restore helpers

Retail `005AF5C0` constructs an application object allocated as `0x4c` bytes. `005AF970` and `005AF9F0` receive its base pointer in `ECX`/`param_1`. Pristine 9.3.1 uses the same flag offsets with a `0x48` allocation; this is a build-specific size difference, not evidence that the final four bytes have different meaning.

```text
ApplicationLifecycleObject_Partial
  +0x00..+0x0f  unknown / base-class and vtable state
  +0x10         BrokerEditorOwner*       confirmed by snapshot/restore calls
  +0x14         unknown pointer/field     used by application/window object paths
  +0x18         unknown pointer/field
  +0x1c..+0x23  unknown
  +0x24         MarkerEditorOwner*        confirmed by snapshot/restore calls
  +0x28         EggEditorOwner*           confirmed by snapshot/restore calls
  +0x2c         ParticleEditorOwner*      confirmed by snapshot/restore calls
  +0x30..+0x37  unknown
  +0x38         shared tool/window context* passed to all four editor openers
  +0x3c         unknown resource/context pointer; released in shutdown path
  +0x40..+0x43  unknown
  +0x44         uint8 marker_was_open
  +0x45         uint8 particle_was_open
  +0x46         uint8 broker_was_open
  +0x47         uint8 egg_was_open
  +0x48..+0x4b  present in retail allocation; meaning unknown
```

Offsets `+0x44..+0x47` are individually cleared and compared with zero. The snapshot writes `1` only after the corresponding predicate returns true and the close/reset call returns. The restore helper tests them independently and clears all four after the open attempts. Do not treat these bytes as persistent configuration or as the `Editing/EditorsOpen` count.

## Editor owner/window relationship

Each owner has an HWND-bearing window wrapper. Its open predicate returns whether the stored HWND is nonzero. The lifecycle helpers retain pointers to the owner objects while closing and reopening their UI/view resources; the owners are not removed from a global “open editors” list by the four byte flags.

| Tool | Application member | Open predicate | Close/reset | Open |
|---|---:|---:|---:|---:|
| Marker | `+0x24` | `0065B860` | `0065B820` | `0065B870` |
| Particle | `+0x2c` | `006557B0` | `00655700` | `006557C0` |
| Broker | `+0x10` | `0065E980` | `0065E960` | `0065E990` |
| Egg | `+0x28` | `00657FC0` | `00657F80` | `00657FD0` |

The predicates establish whether the corresponding window is open, not whether its model data is initialized or dirty. Marker and Egg cleanup paths update `Editing/EditorsOpen`; Particle and Broker do not call those integer-counter helpers. The open byte state therefore covers more tools than the broker value does.

## `Editing/EditorsOpen` storage

Retail access uses the typed broker manager and the literal key `Editing/EditorsOpen`. `0066C180` initializes a missing integer to `1` or increments the existing value. `0066C380` decrements and clamps at zero. Both routines also copy editor camera/view state into or out of owner-side storage. The direct owner initialization/cleanup pairs are Marker `0065ACD0` / `0065AEA0` and Egg `006573B0` / `00657630`.

**Confidence:** HIGH that the value is an integer count of active Marker/Egg editing-view contexts; MEDIUM that these are the only possible callers in all execution paths because virtual/destructor behavior can add indirect edges. It is not a count of every tool HWND.

## Build differences

The four independent byte meanings and order are established in pristine 9.3.1, 9.10.0, and retail. 9.3.1's restore allocation is `0x48`; 9.10.0 and retail allocate `0x4c`. No equivalent 8.4.1 app layout has been verified, and the similar numeric offsets seen in one 8.4.1 per-object update routine are not reused as editor flags.
