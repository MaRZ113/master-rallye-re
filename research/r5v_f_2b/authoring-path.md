# R5V-F.2b authoring path and Junction incident

The selected Copy of Mercedes GXM files embed the authoring root D:/projects/MRallyeTNG/DataGx/Vehicles/Mercedes. The isolated Junction at D:\projects\MRallyeTNG\DataGx\Vehicles\Mercedes targets research-output/r5v_f_2b/authoring-root/Mercedes. Its ownership marker currently records phase R5V-F.2b and state created.

## Incident and repair

The original Setup helper created the correct Junction, but the ownership marker remained creating after a verifier failure. The verifier used Resolve-Path on the link path; this returns the traversed target content location in a way that did not match the expected target string used by the script. The first verifier therefore reported a false target mismatch after successful Junction creation.

Recovery independently checked LinkType=Junction and the actual Get-Item.Target against the exact isolated authoring directory, then advanced marker state from creating to created. No target files were moved or deleted. This failure and recovery are retained as pipeline evidence.

The source Check, Setup and Remove helpers now read the reparse-point target from Get-Item.Target and normalize both slash styles. Setup safely recovers an exact marked creating state. Remove requires the completed marker and exact target, calls Directory.Delete with recursive=false on only the link node, then rechecks the target files. Regression tests guard these behaviors.

The fixed source scripts have been copied into the generated research-output scripts directory and checked against the current Junction. It remains installed for Cook B. Removal is deferred until after A/B comparison.
