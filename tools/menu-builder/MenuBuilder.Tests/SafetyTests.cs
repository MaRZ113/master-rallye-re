using System.Diagnostics;
using MenuBuilder.Core;

/// <summary>MENU-STUDIO1 regression tests: installer safety, strict compilation, editor state, dependencies, snapping.</summary>
static class SafetyTests
{
    static Action<bool, string> Check = (_, _) => { };

    static string Temp(string stem)
    {
        var d = Path.Combine(Path.GetTempPath(), "mb-tests", stem + "-" + Guid.NewGuid().ToString("N")[..6]);
        Directory.CreateDirectory(d);
        return d;
    }

    static Dictionary<string, string> Tree(string dir) => !Directory.Exists(dir) ? new() :
        Directory.GetFiles(dir, "*", SearchOption.AllDirectories)
            .ToDictionary(f => Path.GetRelativePath(dir, f), f => GameData.Sha256(File.ReadAllBytes(f)));

    static bool Same(Dictionary<string, string> a, Dictionary<string, string> b) => a.Count == b.Count && a.All(kv => b.TryGetValue(kv.Key, out var v) && v == kv.Value);

    static bool Junction(string link, string target)
    {
        var p = Process.Start(new ProcessStartInfo("cmd.exe", $"/c mklink /J \"{link}\" \"{target}\"") { CreateNoWindow = true, UseShellExecute = false, RedirectStandardOutput = true });
        p!.WaitForExit();
        return p.ExitCode == 0 && Directory.Exists(link);
    }

    static MenuProject Small(Workspace ws, string name, string? id = null)
    {
        var p = new MenuProject { Name = name, Id = id ?? MenuProject.NewId() };
        var s = ws.NewRetailScreen("MainMenu");
        s.Elements.Add(new ElementDef { Name = "Options", Base = "Options", Patch = new ElementPatch { X = 300 } });
        p.Screens.Add(s);
        return p;
    }

    public static void Run(Workspace ws, MenuProject demo, Action<bool, string> check)
    {
        Check = check;
        Names();
        Installer_(ws, demo);
        Compiler_(ws, demo);
        Editor(ws, demo);
        Deps(ws, demo);
        Snapping();
        Overlay();
    }

    static void Names()
    {
        foreach (var bad in new[] { "", " ", ".", "..", "a/b", "a\\b", "..\\x", "C:\\x", "C:x", "CON", "nul", "My Menu", "-x", "x.y", new string('a', 49), "ÄÖ", "a\tb" })
            Check(!LayoutName.IsValid(bad), $"layout name rejected: '{bad.Replace("\t", "\\t")}'");
        Check(LayoutName.IsValid("Demo") && LayoutName.IsValid("my-menus_2"), "valid layout names accepted");
        bool threw = false;
        try { Installer.LayoutDir(Temp("ld"), ".."); } catch (InvalidLayoutNameException) { threw = true; }
        Check(threw, "LayoutDir('..') throws instead of addressing the parent folder");
        threw = false;
        try { Installer.LayoutDir(Temp("ld"), ""); } catch (InvalidLayoutNameException) { threw = true; }
        Check(threw, "LayoutDir('') throws instead of addressing the Layouts root");
        Check(LayoutName.Suggest("My Menu!") == "My_Menu" && LayoutName.IsValid(LayoutName.Suggest("..")), "name suggestion is valid");
    }

    static void Installer_(Workspace ws, MenuProject demo)
    {
        var target = Temp("install");
        var layouts = Installer.LayoutsRoot(target);
        var o = new Installer.Options { TargetRoot = target };
        var p = Small(ws, "SafeA");
        // A neighbour layout that must survive everything below.
        var other = Path.Combine(layouts, "Neighbour");
        Directory.CreateDirectory(other);
        File.WriteAllText(Path.Combine(other, "keep.txt"), "neighbour");

        var r1 = ws.Install(p, o);
        Check(r1.Outcome == Installer.Outcome.Installed && File.Exists(Path.Combine(layouts, "SafeA", "runtime.txt")), $"first install: Installed ({r1.Message})");
        var r2 = ws.Install(p, o);
        Check(r2.Outcome == Installer.Outcome.Updated, "second install: Updated");
        Check(Installer.ReadConfig(target) is { enabled: true, layout: "SafeA" }, "activated in MenuBuilder.ini");
        Check(!Directory.GetDirectories(layouts, ".mb-*").Any(), "no staging/backup folders left after success");
        var live = Tree(Path.Combine(layouts, "SafeA"));

        // Invalid project name: nothing written.
        var bad = Small(ws, "..");
        var rb = ws.Install(bad, o);
        Check(rb.Outcome == Installer.Outcome.ValidationFailed && rb.Findings.Any(f => f.Code == "LAYOUT_NAME"), "name '..' → Validation Failed");
        bad.Name = "";
        Check(ws.Install(bad, o).Outcome == Installer.Outcome.ValidationFailed && Directory.Exists(layouts), "empty name → Validation Failed, Layouts root intact");

        // Collision with another project's layout of the same name.
        var foreign = Small(ws, "SafeA", MenuProject.NewId());
        var rf = ws.Install(foreign, o);
        Check(rf.Outcome == Installer.Outcome.ValidationFailed && Same(live, Tree(Path.Combine(layouts, "SafeA"))), "same name from another project refused; installed layout untouched");
        Check(ws.Install(foreign, new Installer.Options { TargetRoot = target, ReplaceForeign = true }).Outcome == Installer.Outcome.Updated, "explicit replace of a foreign layout");
        ws.Install(p, new Installer.Options { TargetRoot = target, ReplaceForeign = true });
        live = Tree(Path.Combine(layouts, "SafeA"));

        // Fault injection at every publication step.
        foreach (var step in new[] { "staged", "backed-up", "published", "activated" })
        {
            var ini = File.ReadAllBytes(Installer.ConfigPath(target));
            var changed = p.Clone(); changed.Screens[0].Elements[0].Patch.X = 310;
            Installer.FaultInjection = s => { if (s == step) throw new IOException("simulated failure at " + s); };
            Installer.InstallResult rr;
            try { rr = ws.Install(changed, o); } finally { Installer.FaultInjection = null; }
            bool expectRollback = step is "published" or "activated";
            Check(rr.Outcome == (expectRollback ? Installer.Outcome.RollbackCompleted : Installer.Outcome.InstallationFailed),
                $"failure at '{step}' → {(expectRollback ? "Rollback Completed" : "Installation Failed")} (got {rr.Title}: {rr.Message})");
            Check(Same(live, Tree(Path.Combine(layouts, "SafeA"))), $"failure at '{step}': previous layout byte-identical");
            Check(File.ReadAllBytes(Installer.ConfigPath(target)).SequenceEqual(ini), $"failure at '{step}': MenuBuilder.ini unchanged");
            Check(!Directory.GetDirectories(layouts, ".mb-*").Any(), $"failure at '{step}': temporary folders removed");
        }

        // First install that fails after publishing leaves nothing behind.
        var fresh = Small(ws, "SafeNew");
        Installer.FaultInjection = s => { if (s == "activated") throw new IOException("simulated"); };
        try { Check(ws.Install(fresh, o).Outcome == Installer.Outcome.RollbackCompleted && !Directory.Exists(Path.Combine(layouts, "SafeNew")), "failed first install leaves no layout"); }
        finally { Installer.FaultInjection = null; }

        // Interrupted swap (process killed between the two renames): the next install restores and continues.
        Directory.Move(Path.Combine(layouts, "SafeA"), Path.Combine(layouts, ".mb-backup-SafeA-deadbeef"));
        var notes = new List<string>();
        Installer.RecoverInterrupted(layouts, "SafeA", notes);
        Check(Same(live, Tree(Path.Combine(layouts, "SafeA"))) && notes.Any(n => n.Contains("restored")), "interrupted swap: backup restored");

        // Read-only files in the installed layout.
        foreach (var f in Directory.GetFiles(Path.Combine(layouts, "SafeA"), "*", SearchOption.AllDirectories)) File.SetAttributes(f, FileAttributes.ReadOnly);
        var ro = ws.Install(p, o);
        Check(ro.Outcome == Installer.Outcome.Updated && !Directory.GetDirectories(layouts, ".mb-*").Any(), "read-only files: Updated and old copy removed");
        live = Tree(Path.Combine(layouts, "SafeA"));

        // Locked file (opened without delete sharing, like a running process holding it).
        var lockedFile = Directory.GetFiles(Path.Combine(layouts, "SafeA"), "*.xml", SearchOption.AllDirectories).First();
        using (new FileStream(lockedFile, FileMode.Open, FileAccess.Read, FileShare.Read))
        {
            var rl = ws.Install(p, o);
            Check(rl.Outcome == Installer.Outcome.InstallationFailed && rl.Message.Contains("open"), $"locked file → Installation Failed with a clear reason ({rl.Message})");
        }
        Check(Same(live, Tree(Path.Combine(layouts, "SafeA"))), "locked file: installed layout unchanged");

        // Junctions: a "layout" that is a link to a victim folder is never followed or deleted.
        var victim = Temp("victim");
        File.WriteAllText(Path.Combine(victim, "precious.txt"), "do not delete");
        if (Junction(Path.Combine(layouts, "Evil"), victim))
        {
            var evil = Small(ws, "Evil");
            var re = ws.Install(evil, new Installer.Options { TargetRoot = target, ReplaceForeign = true });
            Check(re.Outcome == Installer.Outcome.InstallationFailed && File.Exists(Path.Combine(victim, "precious.txt")), "install over a junction refused; target untouched");
            bool threw = false;
            try { Installer.Uninstall(target, "Evil"); } catch (UnsafePathException) { threw = true; }
            Check(threw && File.Exists(Path.Combine(victim, "precious.txt")), "uninstall of a junction refused; target untouched");
            Check(!Installer.InstalledLayouts(target).Contains("Evil"), "junctions are not listed as layouts");
            // A link inside a tree is unlinked, never followed.
            var tree = Path.Combine(layouts, ".mb-trash-Tree-12345678");
            Directory.CreateDirectory(tree);
            Junction(Path.Combine(tree, "link"), victim);
            SafeFs.DeleteTree(layouts, tree);
            Check(!Directory.Exists(tree) && File.Exists(Path.Combine(victim, "precious.txt")), "recursive delete unlinks a nested junction without touching its target");
            Directory.Delete(Path.Combine(layouts, "Evil"), false);
        }
        else Check(false, "could not create a junction for the test (mklink /J)");

        // A Layouts folder that is itself a junction is refused.
        var target2 = Temp("install2");
        Directory.CreateDirectory(Path.Combine(target2, Installer.Folder));
        if (Junction(Installer.LayoutsRoot(target2), victim))
            Check(ws.Install(Small(ws, "X"), new Installer.Options { TargetRoot = target2 }).Outcome == Installer.Outcome.InstallationFailed &&
                  Directory.GetFileSystemEntries(victim).Length == 1, "Layouts junction refused; nothing written through it");

        bool rootThrew = false, gameThrew = false;
        try { SafeFs.DeleteTree(layouts, layouts); } catch (UnsafePathException) { rootThrew = true; }
        try { SafeFs.DeleteTree(layouts, target); } catch (UnsafePathException) { gameThrew = true; }
        Check(rootThrew && gameThrew, "DeleteTree never deletes the Layouts root or the game folder");

        Check(Installer.Uninstall(target, "SafeA") && !Directory.Exists(Path.Combine(layouts, "SafeA")) && Installer.ReadConfig(target).enabled == false,
            "uninstall of the active layout switches to Classic");
        Check(File.ReadAllText(Path.Combine(other, "keep.txt")) == "neighbour" && Installer.InstalledLayouts(target).SequenceEqual(new[] { "Neighbour" }),
            "neighbour layout untouched by every operation");
    }

    static void Compiler_(Workspace ws, MenuProject demo)
    {
        var target = Temp("compile");
        var o = new Installer.Options { TargetRoot = target };
        var good = demo.Clone();
        good.Name = "StrictDemo";
        var ok = ws.Install(good, o);
        Check(ok.Ok, $"demo installs (warnings do not block): {ok.Title} {ok.Message}");
        var dir = Path.Combine(Installer.LayoutsRoot(target), "StrictDemo");
        var before = Tree(dir);
        var reopened = MenuProject.Load(Path.Combine(dir, "project.mrmenu.json"));
        Check(reopened.ToJson() == good.ToJson(), "installed project.mrmenu.json reopens identical");

        // One element that cannot be compiled.
        var broken = good.Clone();
        broken.Screen("MainMenu")!.Elements.Add(new ElementDef { Name = "MB_Broken", Template = "MainMenu/NoSuchEgg", Patch = new ElementPatch { X = 10, Y = 10 } });
        var (_, f1) = ws.Build(broken);
        var e1 = f1.FirstOrDefault(f => f.Code == "TEMPLATE_MISSING");
        Check(e1 != null && e1.Severity == Severity.Error && e1.Screen == "MainMenu" && e1.Element == "MB_Broken" && e1.Operation != null && e1.Fix != null,
            "failed element = ERROR with screen, element, operation and fix");
        var rb = ws.Install(broken, o);
        Check(rb.Outcome == Installer.Outcome.ValidationFailed && Same(before, Tree(dir)), "a failed element blocks installation; installed layout untouched");

        var renamed = good.Clone();
        renamed.Screen("MainMenu")!.Elements.Add(new ElementDef { Name = "bad name", Template = "MainMenu/OnePlayer" });
        Check(ws.Build(renamed).findings.Any(f => f.Code == "INVALID_ID" && f.Severity == Severity.Error), "invalid element identifier is an ERROR");

        var gone = good.Clone();
        gone.Screen("MainMenu")!.Elements.Add(new ElementDef { Name = "NotThere", Base = "NotThere", Patch = new ElementPatch { X = 1 } });
        Check(ws.Build(gone).findings.Any(f => f.Code == "BASE_EGG_MISSING" && f.Severity == Severity.Error), "edit of a missing retail egg is an ERROR");

        var required = good.Clone();
        required.Screen("VehicleConfig")!.Element("VC_Paint")!.Action!.Optional = false;
        var (_, f2) = ws.Build(required);
        Check(f2.Any(f => f.Code == "ACTION_REQUIRED_MISSING" && f.Severity == Severity.Error && f.Element == "VC_Paint"), "required action without handler is an ERROR");
        Check(ws.Install(required, o).Outcome == Installer.Outcome.ValidationFailed && Same(before, Tree(dir)), "missing required callback blocks installation");

        var badId = good.Clone();
        badId.Screen("VehicleConfig")!.Element("VC_Paint")!.Action!.Extension = "0x401000";
        Check(ws.Build(badId).findings.Any(f => f.Code == "ACTION_ID" && f.Severity == Severity.Error), "an address-like action ID is rejected");

        var (lay, f3) = ws.Build(good);
        Check(f3.Any(f => f.Code == "ACTION_NOT_IMPLEMENTED" && f.Severity == Severity.Warning) && f3.All(f => f.Severity != Severity.Error), "optional planned actions are warnings only");
        var vc = lay.Screens.First(s => s.Name == "VehicleConfig");
        Check(vc.Values.Any(v => v.Source == "vehicle.model_source" && v.Key == "MenuBuilder/MB_VehicleConfig/VC_ModelValue" && v.Format == "MODEL: {value}"), "value binding compiled to a runtime Broker name");
        var table = Installer.RuntimeTable(lay, ws.Data, ws.Exe);
        Check(table.Contains("value\tMB_VehicleConfig\tVC_BuildValue\tMenuBuilder/MB_VehicleConfig/VC_BuildValue\tvehicle.build\tNOT AVAILABLE\tBUILD: {value}\n"), "runtime table carries value bindings");
        Check(table.Contains("ext=vehicle.paint\targs=1\toptional=1"), "runtime table marks optional actions");
        var legacy = good.Clone();
        legacy.Screen("VehicleConfig")!.Element("VC_Model")!.Action!.Extension = "extra_options.model_source";
        Check(Installer.RuntimeTable(ws.Build(legacy).layout, ws.Data, ws.Exe).Contains("ext=vehicle.model_source"), "legacy action name maps to its catalog ID");
        Check(lay.Screens.All(s => s.Name != "Unused") && ws.Build(new MenuProject { Name = "U", Screens = { ws.NewRetailScreen("Credits") } }).layout.Screens.Count == 0,
            "unchanged retail screens are not served");
    }

    static void Editor(Workspace ws, MenuProject demo)
    {
        var dir = Temp("editor");
        var path = Path.Combine(dir, "demo.mrmenu.json");
        demo.Clone().Save(path);
        var s = new EditorSession(ws, MenuProject.Load(path), path);
        Check(!s.Dirty && !s.CanUndo, "opened project is clean");
        s.SelectScreen("MainMenu");
        s.Move(new[] { "Multiplayer" }, 5, 0, 0);
        Check(s.Dirty && s.CanUndo, "edit → dirty");
        s.Undo();
        Check(!s.Dirty && s.CanRedo, "undo back to the saved state → clean");
        s.Redo();
        Check(s.Dirty, "redo → dirty again");

        // All frontend screens can be opened without making the project dirty.
        var undoCount = s.CanUndo;
        int opened = 0, failed = 0;
        foreach (var (_, name, _) in ws.RetailScreens())
        {
            try { s.OpenScreen(name); var v = s.Variant(); ws.Renderer.Render(v, new RenderOptions { Width = 320, Height = 240 }); opened++; }
            catch (Exception ex) { failed++; Console.WriteLine($"  open {name}: {ex.Message}"); }
        }
        Check(failed == 0 && opened >= 45, $"every frontend screen opens and renders ({opened} screens)");
        Check(s.Dirty && ws.Build(s.Project).layout.Screens.Count == demo.Screens.Count, "opening screens adds no served screens");
        s.SelectScreen("MainMenu");

        // Changing the game folder keeps project, path, dirty flag and history.
        var dirty = s.Dirty;
        using (var ws2 = new Workspace(ws.Data.Root))
        {
            var report = s.Rebind(ws2);
            Check(s.Path == path && s.Dirty == dirty && s.CanUndo && report.All(f => f.Severity != Severity.Error), "rebind to a game folder keeps path, dirty state and undo history");
            s.Undo();
            Check(s.Project.Screen("MainMenu") != null, "undo works after the rebind");
            s.Redo();
            s.Rebind(ws);
        }
        var fake = Temp("fakegame");
        File.WriteAllBytes(Path.Combine(fake, "MRallye.exe"), new byte[] { 0x4D, 0x5A });
        using (var ws3 = new Workspace(fake))
        {
            var report = s.Rebind(ws3);
            Check(report.Any(f => f.Code == "BASE_MISSING") && s.Dirty == dirty && s.CanUndo, "wrong resource folder: missing resources reported, edits kept");
            s.Rebind(ws);
        }

        // Save / save as / reopen.
        var path2 = Path.Combine(dir, "copy.mrmenu.json");
        s.Save(path2);
        Check(!s.Dirty && s.Path == path2 && s.Project.Id != null, "save as → clean, new path, project ID assigned");
        var again = new EditorSession(ws, MenuProject.Load(path2), path2);
        Check(again.Project.ToJson() == s.Project.ToJson() && !again.Dirty, "saved project reopens identical");

        // A failing edit leaves nothing behind.
        var json = s.Project.ToJson();
        try { s.Edit("boom", () => { s.Project.Screens.Clear(); throw new InvalidOperationException("x"); }); } catch (InvalidOperationException) { }
        Check(s.Project.ToJson() == json && !s.Dirty, "failed edit is rolled back and not recorded");

        // Two projects in two sessions stay independent.
        var other = new EditorSession(ws, Small(ws, "Other"), null, saved: false);
        other.SelectScreen("MainMenu");
        other.Move(new[] { "Quit" }, 3, 0, 0);
        Check(other.Dirty && !s.Dirty && s.Project.Screen("MainMenu")!.Element("Quit")?.Patch.X == null, "sessions do not share state");
        Check(new EditorSession(ws, new MenuProject { Name = "N" }, null, saved: false).Dirty, "a new unsaved project is dirty");
    }

    static void Deps(Workspace ws, MenuProject demo)
    {
        var s = new EditorSession(ws, demo.Clone(), null);
        s.SelectScreen("MainMenu");
        var quit = s.Dependencies("Quit");
        Check(quit.Class is ElementClass.NativeRequired or ElementClass.UnknownDependency && quit.BlocksDelete, $"retail Quit: {quit.Summary}");
        var screenEgg = s.Scene().ScreenEgg!.Name;
        Check(s.Dependencies(screenEgg).Class == ElementClass.NativeRequired && !s.Dependencies(screenEgg).CanHide, "screen controller is Native Required");
        Check(s.Dependencies("MB_Credits").Class == ElementClass.UserCreated, "new element is User Created");
        var json = s.Project.ToJson();
        bool blocked = false;
        try { s.Delete(new[] { "Quit" }); } catch (DependencyException) { blocked = true; }
        Check(blocked && s.Project.ToJson() == json, "deleting a native element is blocked and changes nothing");
        blocked = false;
        try { s.Rename("Quit", "QuitX"); } catch (DependencyException) { blocked = true; }
        Check(blocked, "renaming a native element is blocked");
        bool invalid = false;
        try { s.Rename("MB_Credits", "bad name"); } catch (ArgumentException) { invalid = true; }
        Check(invalid, "invalid new name rejected");

        // Hide keeps the egg, removes focus/hitbox and reroutes navigation.
        int progressId = s.Scene().Find("Progress")!.ButtonId!.Value;
        s.Hide(new[] { "Progress" });
        var (lay, f) = ws.Build(s.Project);
        var mm = lay.Screens.First(x => x.Name == "MainMenu");
        var pb = mm.Buttons.First(b => b.Egg == "Progress");
        Check(pb.Hidden && pb.Blocked && pb.Hit.Count == 0, "hidden button: no hitbox in any aspect");
        Check(!f.Any(x => x.Code == "NAV_TO_HIDDEN") && mm.Buttons.Where(b => !b.Hidden).All(b => b.Up != progressId && b.Down != progressId), "navigation rerouted around the hidden button");
        var table = Installer.RuntimeTable(lay, ws.Data, ws.Exe);
        Check(table.Contains($"button\tMainMenu\t{progressId}\tProgress\t0\t"), "runtime table blocks the hidden button");
        Check(s.Scene().Find("Progress") != null, "hidden egg stays in the scene (native links kept)");

        // A path that still points at a hidden element is an error.
        var p2 = s.Project.Clone();
        p2.Screen("MainMenu")!.Element("OnePlayer")!.Patch.Down = progressId;
        Check(ws.Build(p2).findings.Any(x => x.Code == "NAV_TO_HIDDEN" && x.Severity == Severity.Error), "focus path into a hidden element is an ERROR");

        // Deleting a user element reroutes its neighbours.
        int creditsId = s.Scene().Find("MB_Credits")!.ButtonId!.Value;
        s.Delete(new[] { "MB_Credits" });
        Check(s.Scene().Focusables.All(e => new[] { "Up Path", "Down Path", "Left Path", "Right Path" }.All(p => e.Focusable!.GetInt(p) != creditsId)),
            "deleting a user element leaves no navigation reference to it");
        Check(!ws.Build(s.Project).findings.Any(x => x.Severity == Severity.Error && x.Code.StartsWith("NAV")), "focus graph valid after delete");

        // Disable.
        s.SetEnabled(new[] { "Options" }, false);
        var ob = ws.Build(s.Project).layout.Screens.First(x => x.Name == "MainMenu").Buttons.First(b => b.Egg == "Options");
        Check(ob.Blocked && !ob.Hidden && ob.Hit.Count > 0, "disabled button keeps its place but is blocked");
    }

    static void Snapping()
    {
        var moving = new UiRect(100, 100, 200, 150);
        var others = new[] { new UiRect(300, 300, 400, 340) };
        var screen = new UiRect(0, 0, 640, 480);
        var r = Snapper.Move(moving, 197, 3, others, screen, 6);
        Check(r.SnappedX && Math.Abs(r.Dx - 200) < 1e-9 && r.Guides.Any(g => g.Vertical && Math.Abs(g.Pos - 300) < 1e-9), "left edge snaps to a neighbour's left edge");
        var c = Snapper.Move(moving, 168, 0, others, screen, 6);
        Check(c.SnappedX && Math.Abs(c.Dx - 170) < 1e-9, "centre snaps to the screen centre (320)");
        var none = Snapper.Move(moving, 20, 20, others, screen, 6);
        Check(!none.SnappedX && !none.SnappedY && none.Dx == 20, "no snap outside the threshold");
        var (ddx, _, g) = Snapper.Edges(moving, new[] { 297.0 }, Array.Empty<double>(), others, screen, 6);
        Check(Math.Abs(ddx - 3) < 1e-9 && g.Count > 0, "resized edge snaps");
    }

    static void Overlay()
    {
        var root = Temp("overlay");
        File.WriteAllBytes(Path.Combine(root, "MRallye.exe"), new byte[] { 0x4D, 0x5A });
        var rel = "DataScene/FrontendScreens/VehicleSelect.xml";
        var loose = Path.Combine(root, "DataScene", "FrontendScreens");
        Directory.CreateDirectory(loose);
        File.WriteAllText(Path.Combine(loose, "VehicleSelect.xml"), "loose");
        using (var d = new GameData(root)) Check(d.Source(rel) == "loose" && System.Text.Encoding.ASCII.GetString(d.Read(rel)!) == "loose", "loose page wins over Data.sma");
        var ov = Path.Combine(root, "MRMods", "Vehicles", "active", "resources", "DataScene", "FrontendScreens");
        Directory.CreateDirectory(ov);
        File.WriteAllText(Path.Combine(ov, "VehicleSelect.xml"), "roster");
        using (var d = new GameData(root)) Check(d.Source(rel) == "overlay" && System.Text.Encoding.ASCII.GetString(d.Read(rel)!) == "roster", "Vehicle Manager roster page wins (as the loader serves it)");
    }
}
