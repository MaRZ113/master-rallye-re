# Deterministic research scaffolding

Source is pristine retail bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4,
size3121214. Builders verify hash, size, PE layout and each original byte. Inverse
restoration must recover pristine hash; rebuilt output must match exact pin.

Two existing count reads47B88A/47B8DD call fresh cave68E300..68E383. Original
getter always runs; original one-human/ID0/Track10/Race/ghost-off guards are kept,
with effective count5/6/7. One-human chooser CALL47B96E routes to68E400:
396/453/510 bytes for totals6/7/8 respectively. The ordinary split-screen chooser
call47B93D is untouched. Wrapper checks all five original arguments, same guarded
frontend count and Race/NumCars, then native CarID, registry CarClass and DriverID
setters publish the roster. Guard failure restores registers/flags and tail-jumps
to original458090. Target return cleans exactly20 argument bytes.

Fresh ranges compose only hardened Loading464F69 and native Dump60201E/602153
guards at68E2A0/68E2C0. No old randomizer, DLL loader or Challenge preview stub.
Ranges are non-overlapping; end68E5FE is below68F000/IAT. VirtualSize declares
only the required text padding; file size/sections remain unchanged. Physical
participant allocation, update loops, Results/HUD/XML and registry are untouched.

Roster prefixes: Car0 ID0/human Driver30; AI IDs1,7,14,2,8,15,17 with Drivers0..6.
Class is read from each stock registry record, not separately invented. Native
preparation derives family/wheels/physics from each ID. This scaffold intentionally
bypasses stock class-filtered RNG under the exact proof guard; it is not the final
randomizer or UI integration.

Reproduce: `python tools/r_ai2_1_capacity.py build <pristine-MRallye.exe>
--expected-cars N --output .research-output/r-ai2-1/<six|seven|eight>/MRallye.exe`.
Builder refuses candidate overwrite. Verify with `verify <candidate> --expected-cars N`.
Restore the isolated installation using its preserved original. Do not distribute
research executables. Safe [manifest summary](patch-manifest.json) includes
source/output hashes, offsets, lengths and range hashes; proprietary payloads stay ignored.
