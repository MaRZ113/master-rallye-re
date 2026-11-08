# Live configuration changes

Randomizer policy values and `Duplicates` are read when the game creates its
next opponent roster. You can edit these values while the game is running.
The current race or saved event keeps its existing roster; start a new Quick
Race, Cup, Master Rallye competition, Invitation event, or Challenge preview
to use the new policy.

Challenge Preview keeps its prepared opponent while the preview remains on
screen. Back out and create a new preview to pick up a policy edit. The preview
and race remain synchronized.

`MaxOpponents`, `Addons.Include`, and `Logging.Enabled` are startup settings.
Restart the game after changing them. `MaxOpponents` sets the Quick Race menu
ceiling; it does not force that many opponents into a race.

The runtime reads a complete bounded configuration snapshot. A malformed or
partially written edit is rejected as a whole, and the last valid running
configuration remains active.
