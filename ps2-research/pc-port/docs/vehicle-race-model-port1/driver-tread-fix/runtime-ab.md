# X-Trail driver duplication / tread address correction

Close game and manually replace only d3d8.dll. Keep current CAR/WHEEL/COMPLETE assets and INI, including RacePS2ModelParts=1/RacePS2WheelMode=1, single-participant X-Trail race. No asset regeneration or new config is needed.

Expected: one native driver and one native copilot, with original animation. No extra fixed faces, bodies or visors. Seats, dashboard and steering wheel remain. From outside and inside inspect driver heads/torso while turning, accelerating/braking and changing camera. Static racePS2 draw count falls by396triangles: chassisbatch1330→934 withparts1; fullprivateCAR1832→1436. Native PCdrivers are intentionally retained; fewerprivatefaces here means duplicated static characters were removed, not geometry lost accidentally. COMPLETE menu model remains unchanged.

Tread: originalUrange[-2.159478,2.830815] repeats across circumference; now only wheel source1 uses D3DTADDRESS_WRAP for primaryU, while primaryV remainsCLAMP and rim/body policies remain unchanged. Original UV, image bytes, source alpha and rubber secondary unchanged. Inspect close tread seam at rest, steering, rolling forward/reverse; look for stretching or edge discontinuities. Test windowReset/MSAA4x and race restart. Save two F10/screenshots (interior + tirecloseup).

Diagnostics remain bounded. ps2_race_model_replacement should report934 batchfaces underparts1; part/suppression events unchanged. Wheel gates and source signatures unchanged; exact state restoration/native HRESULT tests passed. Corrected appearance is PENDING_USER_RUNTIME; previous wheel steering/movement was confirmed by user.
