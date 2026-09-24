# Class-2 frontend capacity

`RAW_GHIDRA_SUPPORTED` from R5V-B, reconfirmed against current local research: screen constructor `0x480A20` stores class capacities 7/7/**11** at object `+0x20/+0x24/+0x28`; `0x481F50` uses the active class capacity for next/previous bounds. Class-2 local 11 converts to absolute ID25 in `0x481E20`.

The update function `0x481950` iterates 12 button positions, but retail frontend XML references `Button0XPos` through `Button10XPos`. This suggests arithmetic/config handling for a twelfth position, **not** a proven allocated twelfth button widget. No complete audit of button storage, focus/navigation, stats display, preview lookup and localization for local 11 was established. Stats at `0x4819B0` index record25 and ID25 has a localization selector, but only after valid initialization; the frontend preview may use another bound.

Therefore a hypothetical 11→12 change is necessary to navigate to local 11, but structural safety as a one-value patch remains **unproven**. ID25 unlock flag 15 may also prevent selection. No capacity value was changed.
