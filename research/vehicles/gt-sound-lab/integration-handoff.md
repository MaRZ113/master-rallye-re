# Rally Workshop Audio Studio handoff

This is an independent research tool. No Workshop implementation, installed
profile, main developer file or game asset was modified, merged or published.

## Selection contract

1. Configure a read-only local game root/VOL and generate a private catalog.
2. Select a `game` and exact `vehicle_id`; a GT4 ModelCode alias is accepted
   only if unambiguous. GT3 short mesh identifiers remain a separate boundary.
3. Offer the vehicle's source-key-associated `banks`. Show shared Sound IDs,
   missing variants, tuning evidence and confidence beside the selection.
4. Inspect a bank and choose an explicit PCM-valid `entry_id`. Expose original
   record/file offsets, encoded hash, raw fields, loops and semantic evidence.
5. Export/audition with an explicit nominal rate, or an admitted native anchor
   rule. Preserve its sidecar and let the user override the recommendation.
6. Import the selected PCM through Audio Studio's existing source/hash/trim/
   conversion workflow. Preserve source qualification separately from authored
   pitch/gain/resampling and native output format conversion.

Catalog schema is `gt-sound-bank-lab/1`; see mapping.schema.json. GT3 source
fields remain present under their original names as well as common aliases.
Vehicle objects contain `vehicle_id`, `sound_id`, `banks`; GT4 adds model
codes, exact row evidence, tuning options, shared ENGINE rows and a
`default_native_bank_candidate`. Its runtime_confirmed=false is intentional.
GT3 supplies GTAR row offsets/hashes and bank-member RoFS provenance.

Bank inspections contain `sha256`, `entries`, source metadata and explicit
boundaries. `sample_file_offset` is within the decoded bank member, not an
absolute VOL file offset when compression is involved. RoFS member offsets,
stored/decoded hashes and compression metadata supply the outer provenance.
Never add the decoded offset to a compressed VOL member offset and describe
the result as an original encoded sample location.

WAV sidecars contain bank and encoded-span identity, selected entry, WAV hash,
rate provenance and loop metadata. `authentic_effect_identity:null` forbids
silently promoting a recording to an acoustic BOV/whine/etc. A static native
event connection is a separate evidence record and may be displayed as such.

## Policy for automatic suggestions

Source key chains can automatically suggest associated banks. GT4 default
tuning interpretation may suggest a variant with its supplied-CORE evidence
and build limitation. A current game save/loadout, matching-build runtime and
the user's preferred recording remain explicit inputs. Missing/unsupported
records have no acoustic fallback guess. A sample ID shared by vehicles is
never treated as a unique sound fingerprint of the chosen model.

An Audio Studio layer should preserve source provenance while freely allowing
authored gain, pitch and loop controls. Such a profile is an adaptation to
Rally Workshop's mixer; it is not original GT multi-layer SPU2 orchestration.
The explorer does not replace the existing synthetic turbo/whine defaults.

## Unresolved acceptance gates

Matching GT4 build/asset pairing, actual driving controls, special INST loops,
sequence-mode dispatch, hardware voice envelopes and spatial mixing need
separate evidence before claiming original playback fidelity. Source-only
regression tests prove parser behavior; they do not prove sound heard in a race.
