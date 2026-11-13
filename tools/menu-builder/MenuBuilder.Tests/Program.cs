using MenuBuilder.Core;

// Self-contained test runner (no NuGet packages): dotnet run --project MenuBuilder.Tests -- <game dir> [demo project]
// Uses the user's own installation read-only; nothing is written outside a temp folder.
static class Program
{
    static int _pass, _fail;
    static void Check(bool ok, string what)
    {
        if (ok) _pass++; else _fail++;
        Console.WriteLine($"{(ok ? "PASS" : "FAIL")} {what}");
    }

    static int Main(string[] args)
    {
        var game = args.Length > 0 ? args[0] : throw new ArgumentException("usage: MenuBuilder.Tests <game dir> [demo.mrmenu.json]");
        var demoPath = args.Length > 1 ? args[1] : Path.Combine(AppContext.BaseDirectory, "../../../../../../examples/menu-builder/demo.mrmenu.json");
        using var ws = new Workspace(game);

        // --- formats -----------------------------------------------------------------------------------
        int banks = 0, bad = 0;
        foreach (var f in ws.Data.ArchiveFiles("DataGx/").Where(p => p.EndsWith(".dxb", StringComparison.OrdinalIgnoreCase)))
        {
            banks++;
            try { DxbBank.Parse(ws.Data.ReadArchive(f)!); } catch { bad++; }
        }
        Check(banks == 113 && bad == 0, $"DXB tag-125 parser reads all retail banks exactly ({banks - bad}/{banks})");
        var lb = ws.Assets.Bank(@"frontend\buttons\longbutton")!;
        Check(lb.Images.Count == 4 && lb.Images[0].Width == 406 && lb.Images[0].Height == 53, "longbutton: 4 state images, 406x53");
        var tex = ws.Assets.Texture(@"frontend\buttons\longbutton", "longbutton_000_000")!;
        Check(tex.Width == 256 && tex.Height == 64, "DXT 256x64 BGRA");
        var font = ws.Assets.Bank("fonts/Arial/Arial_16")!;
        Check(font.Glyph('A') != null && font.Glyph(' ') != null, "Arial_16 glyph map via {code,image} pairs");

        // --- EXE tables -----------------------------------------------------------------------------------
        Check(ws.Exe?.IsRetail == true, "retail MRallye.exe recognised");
        Check(ws.Exe!.Screens.Count == 54 && ws.Exe.Screens[1] == "MainMenu" && ws.Exe.Screens[51] == "GraphicsMain" && ws.Exe.Screens[27] == "QuickRace", "screen table 0x6F5BD8 (54 names)");
        Check(ws.Exe.Fonts[2] == "fonts/Arial/Arial_16" && ws.Exe.Fonts[3] == "fonts/Arial/Arial_24", "font IDs 0x6CD2F8");
        Check(ws.Exe.Text(1, 1) == "ONE PLAYER" && ws.Exe.Text(12, 0) == "OPTIONS", "gaLocal English text table");

        // --- lossless scene round trip -------------------------------------------------------------------
        int same = 0, total = 0;
        foreach (var (_, name, _) in ws.RetailScreens())
        {
            var raw = ws.Data.ReadArchive(Compiler.ScenePath(name));
            if (raw == null) continue;
            total++;
            var out_ = SceneDocument.Load(name, raw).Serialize();
            if (out_.AsSpan().SequenceEqual(raw)) same++;
            else if (total - same <= 2) Console.WriteLine($"  differs: {name} {raw.Length} vs {out_.Length}");
        }
        Check(same == total, $"unmodified retail scenes serialize byte-identical ({same}/{total})");

        // --- compiler on the demo project ----------------------------------------------------------------
        var demo = MenuProject.Load(demoPath);
        var (layout, findings) = ws.Build(demo);
        Check(findings.Count(f => f.Severity == Severity.Error) == 0, "demo project validates without errors");
        var mm = layout.Screens.First(s => s.Name == "MainMenu");
        var credits = mm.Buttons.First(b => b.Egg == "MB_Credits");
        Check(credits.Id == 10 && credits.Status == BindingStatus.Runtime && credits.Action.Screen == "Credits", "new MainMenu button: ID 10, runtime action navigate Credits");
        Check(mm.Buttons.First(b => b.Egg == "Quit").Status == BindingStatus.NativeRetail, "retail Quit keeps its native command");
        var doc = mm.Variants["4:3"];
        Check(doc.Find("SureChooser")!.Ai("gaFrontendPopupAI")!.GetInt("Up Path") == 10, "popup paths follow the edited owner button (Quit up → 10)");
        var options = doc.Find("Options")!;
        Check(options.X == 300 && Math.Abs(options.ScaleX - 0.9f) < 1e-4, "moved/resized retail Options");
        var hit = ws.Layout.Hitbox(options);
        Check(Math.Abs(hit.Width - 406 * 0.9) < 0.01 && Math.Abs(hit.X0 - 300) < 0.01, $"hitbox follows the scaled sprite {hit}");
        var custom = layout.Screens.First(s => s.Name == "ModMenu");
        Check(custom.IsCustom && custom.NativeId == 64 && custom.SceneName == "MB_ModMenu" && custom.Variants["4:3"].ScreenAi == Compiler.HostAi, "custom screen 64 hosted by GraphicsMain AI");
        Check(custom.Hnt != null && System.Text.Encoding.ASCII.GetString(custom.Hnt).Contains("FSTexture\t[frontend\\buttons\\longbutton_000_000]"), "custom screen texture manifest");
        var vc = layout.Screens.First(s => s.Name == "VehicleConfig");
        Check(vc.Buttons.First(b => b.Egg == "VC_Setup").Action.Type == ActionBinding.Forward, "VEHICLE SETUP = native.forward (Quick Race command 5)");
        Check(vc.Buttons.First(b => b.Egg == "VC_Paint").Status == BindingStatus.Extension && vc.Buttons.First(b => b.Egg == "VC_Paint").Action.Extension == "vehicle.paint",
              "PAINT bound to the planned typed action vehicle.paint (served disabled, not faked)");
        Check(vc.Buttons.First(b => b.Egg == "VC_Model").Action.Extension == "vehicle.model_source", "MODEL SOURCE bound to the Extra Options action");

        // --- runtime table ---------------------------------------------------------------------------------
        var table = Installer.RuntimeTable(layout, ws.Data, ws.Exe);
        Check(table.StartsWith($"MRMENU\t{Installer.RuntimeFormat}\n") && table.EndsWith("end\n"), "runtime table header/footer");
        Check(table.Contains("button\tMainMenu\t10\tMB_Credits\t1\t") && table.Contains("navigate.screen\tscreen=44"), "navigate target resolved to native screen 44");
        Check(table.Contains("button\tMB_ModMenu\t1\tMB_VehicleConfig\t1\t") && table.Contains("screen=65"), "custom target resolved to 65");
        Check(table.Contains("native.forward\tcommand=5\tscreen=27"), "forward resolved to QuickRace 27");

        // --- aspect variants ----------------------------------------------------------------------------------
        var p2 = demo.Clone();
        p2.Screen("MainMenu")!.Element("MB_Credits")!.Patch.Anchor = "right";
        var (l2, _) = ws.Build(p2);
        var v169 = l2.Screens.First(s => s.Name == "MainMenu").Variants["16:9"].Find("MB_Credits")!;
        Check(Math.Abs(v169.X - (252 + 106.67)) < 0.02, $"right anchor shifts by half the extra width at 16:9 ({v169.X})");
        Check(l2.Screens.First(s => s.Name == "MainMenu").Variants["4:3"].Find("MB_Credits")!.X == 252, "4:3 variant unchanged");

        // --- editor session ---------------------------------------------------------------------------------
        var session = new EditorSession(ws, demo.Clone(), null);
        session.SelectScreen("MainMenu");
        var before = session.Project.ToJson();
        session.Move(new[] { "Multiplayer" }, 10, -5, 0);
        Check(session.Scene().Find("Multiplayer")!.X == 280 && session.Scene().Find("Multiplayer")!.Y == 282, "move edits the delta");
        session.Undo();
        Check(session.Project.ToJson() == before, "undo restores the project exactly");
        session.Redo();
        Check(session.Scene().Find("Multiplayer")!.X == 280, "redo");
        var added = session.Add("MainMenu/OnePlayer", "MB_New", 100, 100, text: "NEW");
        var addedEgg = session.Scene().Find(added)!;
        Check(addedEgg.ButtonId == 11, $"new button gets the next free ID >= 10 ({addedEgg.ButtonId})");
        var (l3, f3) = ws.Build(session.Project);
        Check(f3.Any(f => f.Code is "UNBOUND" or "NO_ACTION"), "new button without a handler is reported");
        session.Aspect = "16:9"; session.EditAspectOverride = true;
        session.Move(new[] { "Quit" }, 50, 0, 0);
        Check(session.Project.Screen("MainMenu")!.Aspects["16:9"]["Quit"].X == 284 && session.Scene().Find("Quit")!.X == 234, "aspect-only edit leaves the base layout");
        var dup = session.Duplicate(new[] { "Options" }, 0, -40);
        Check(dup.Count == 1 && session.Scene().Find(dup[0])!.ScaleX == 0.9f, "duplicate keeps the effective patch");
        session.Delete(new[] { "Progress" }, force: true);
        Check(session.Scene().Find("Progress") == null && ws.Compiler.Base("MainMenu").Find("Progress") != null, "delete is a delta; retail base untouched");
        var json = session.Copy(new[] { "OnePlayer" });
        session.Paste(json, 0, 0);
        Check(session.Selection.Count == 1 && session.Scene().Find(session.Selection[0]) != null, "copy/paste of a retail egg");

        // --- widescreen rules ---------------------------------------------------------------------------
        var vs = ws.Compiler.Base("VehicleSelect");
        Check(WidescreenModel.MarginDirection(vs.Find("ModeRightArrow")!.X, vs.Find("ModeRightArrow")!.Y, false) == 1 &&
              WidescreenModel.MarginDirection(vs.Find("ModeLeftArrow")!.X, vs.Find("ModeLeftArrow")!.Y, false) == 0, "PreserveMargins moves only the right arrow of the Mode row");
        Check(Math.Abs(WidescreenModel.Half(16.0 / 9) - 106.6667) < 1e-3 && WidescreenModel.Half(4.0 / 3) == 0, "half extra width");

        // --- screen exchange ---------------------------------------------------------------------------
        var exported = Workspace.ExportScreen(demo, "VehicleConfig");
        var p4 = new MenuProject();
        var imported = Workspace.ImportScreen(p4, exported, "VC2");
        Check(imported.Name == "VC2" && p4.Components.ContainsKey("LongButton") && p4.Styles.ContainsKey("MenuButton"), "screen export/import carries components and styles");

        // --- MENU-STUDIO1 regression suites
        SafetyTests.Run(ws, demo, Check);

        Console.WriteLine($"RESULT pass={_pass} fail={_fail}");
        return _fail == 0 ? 0 : 1;
    }
}
