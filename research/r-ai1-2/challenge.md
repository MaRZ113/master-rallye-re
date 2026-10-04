# Challenge opt-in

Default/sample Challenge=Stock. Type7, 45EA60 frontend event handler and
44FEC0 fixed participant constructor are separate from Quick Race.
Event index0..10 maps to RaceID25..35; registry event stride2C contains the
fixed human/AI IDs at +570/+574. Split-screen has a different branch and is
excluded. Normal one-human constructor establishes two total cars.

45010E always loads the original AI ID before the optional selection callback.
Stock/missing config/module preserves it. Mixed/Diverse can replace only
the selected AI ID register; original CarID setter, registry-derived class,
driver identity, count, ordering and event/course settings still run.
The Stock constructor loads two authored IDs without a duplicate-exclusion
chooser; it supplies no general no-duplicate guarantee. The Stock checker
therefore accepts an authored fixed pair even if IDs coincide. Opt-in selection
explicitly excludes the human ID. This does not alter Stock event data.
With one AI, Diverse means one randomly selected eligible class.

The bounded objective audit includes 4501D0: ranking, race time/bests and
challenge progression are consumed; no exact opponent CarID equality test is
present there. Fixed vehicle matchup is intentional content, and changing it
affects balance. Full completion of an opted-in Challenge remains a human
runtime gate; this is not a claim about every unexercised objective path.
