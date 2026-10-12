# R-CAM1-A3i short runtime handoff

Runtime confirmation is pending. Keep the pristine retail executable unchanged. Use the current renderer build and a normal offline France1 race. The existing Freecam and Trace features must be enabled; the input path forwards all key messages to the game.

```ini
[FreeCamera]
Enabled=1
CameraBookmarksEnabled=1
CameraBookmarkDefaultSlot=1

[FreeCameraKeys]
SaveCameraBookmark=J
LoadCameraBookmark=K
NextCameraBookmarkSlot=L

[Trace]
Enabled=1
FrameSummaries=1
```

1. Start France1, activate Freecam with the configured toggle, then pause normally. Fly to a recognizable road/tree/vehicle view and adjust orientation, Roll and FOV.
2. Press `J` for slot 1. Move and rotate away; press `K`. The first loaded image should return to the exact saved pose, Roll and lens without a residual movement step.
3. Press `L`, save a second viewpoint with `J`, then cycle back and forth with `L` and load both slots.
4. Exit and restart the game. Enter the same France1 race, activate Freecam and load slots 1 and 2. Both must still exist and restore.
5. Confirm pause/unpause, movement, mouse look, speed, Roll, FOV, Clean View, Alt+Tab/refocus, Race Restart, return to frontend, and normal native controls remain intact. Repeat a Save/Load only after Freecam is active on the certified race.

After a successful load, press F10 once. The capture should contain `free_camera.camera_bookmarks` with `last_action="load"`, `last_result="loaded_exact_pose"`, the selected slot, a non-null `last_pose`, valid certificate, and unchanged scope/restore behavior. If there is a native binding conflict, change only the three bookmark key values and repeat; the wrapper does not consume those keys.

Please return the session JSONL, one F10 capture after a successful load, and a screenshot only if visual pose accuracy is unclear. Report same-session save/load, three-slot cycling, cross-restart persistence, pose/FOV/Roll match, native key conflicts, Clean View, pause, focus loss, race restart and frontend behavior. Static/native tests do not substitute for this human runtime check.
