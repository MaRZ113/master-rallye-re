# Flow Builder

Retail command 0x30 in 005B0990 opens the native window at 00662D90, whose title is Flow Builder. The opener prevents duplicate windows. Main menu 005B1320 does not register ID 0x30.

00662FB0 builds the local Flow Builder menu:

- New/Open/Save/Save As are present but disabled.
- Close ID 7, Clear ID 8 and Speed Matrix ID 9 are enabled.
- Convert FL to SFL ID 10 is enabled.
- Build IDs 0/1/2 select Simple Game, Race Game and Rally Game.

WndProc 00662E00 routes these IDs to 006637C0 (build), close, 006636B0 (clear/load SpeedFunction) or 006635B0 (converter). UI labels include Flow File Name, DefaultFlow, Delta and an eleven-column Speed Matrix; they do not define every column's meaning.

Build routine 006637C0 calls mode-dependent generator helpers. 00678FF0 composes Landscape for Simple, RaceLine + Landscape for Race, and Bridges + RaceLine + Landscape for Rally. Other branches reference OutofBounds, BadArea and GoodArea; gameplay meaning is not assigned here.

The build path uses the entered basename and path service, and its writers are create-always. Treat build modes as write-capable until output names and scope are controlled in a copy.
