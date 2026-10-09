# Vehicle-to-prop contact and bounded response

**173d98 ->16e498 ->installed2e3270** connects registered bodies to actual pair tests. The dispatcher separates vehicle and prop families and active/paused collections. A successful relevant active-vehicle/paused-prop pair clears the prop pause flag and rest counter+1c4. This is executable contact-wake proof, not an observed car striking a selected object.

Selected contact response chain:

```text
173df0 grouped contacts
 ->25c980 ->25cd78 ->25ca30 ->25d988 ->25da08
 ->23e6d8/23e7b0 [accumulate velocity changes]
 ->23e968 [commit body state]
```

Contact layout includes point+00..08, normal+0c..14 and body pointers+4c/+50. Given the original solver's selected scalar lambda, **25da08** computes the following bounded response:

```text
J = lambda * normal
rA = contact - positionA; rB = contact - positionB
vAnew = (PA + J) * inverseMassA
vBnew = (PB - J) * inverseMassB
omegaAnew = worldInverseInertiaA * (LA + rA cross J)
omegaBnew = worldInverseInertiaB * (LB - rB cross J)
```

Accumulation helpers subtract old v/omega. **23e968** commits position corrections, velocity, **P=m*v**, and omega via **267940**, which reconstructs L. This reaches actual state writes; it is stronger than a candidate function list. **25dd60** separately computes two-body kinetic energy .5*(P dot v+L dot omega). A ratio >1.01 in25ca78 enters a corrective branch; that branch and general impulse selection remain incomplete.

**UNKNOWN LINK: contact/material/constraints -> selected impulse magnitude.** Surface helper values in body+1bc/+1c0/+1cc are not named restitution or friction without evidence. No offline collision simulator substitutes a textbook formula for that missing link. Other solver branches and detailed vehicle dynamics are outside RIGID1.
