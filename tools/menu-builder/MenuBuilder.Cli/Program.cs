using System.Globalization;
using System.Text.Json;
using MenuBuilder.Core;

// mrmenu — command line and machine API of the Master Rallye Menu Builder.
// Every command prints one JSON document to stdout (except --help); exit code 0 = ok, 1 = validation failed,
// 2 = usage/IO error, 3 = installation failed or rolled back (the previously installed layout is kept).
static class Program
{
    static readonly JsonSerializerOptions Out = new() { WriteIndented = true, PropertyNamingPolicy = JsonNamingPolicy.CamelCase, DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull };

    static int Main(string[] argv)
    {
        CultureInfo.DefaultThreadCurrentCulture = CultureInfo.InvariantCulture;
        CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
        if (argv.Length == 0 || argv[0] is "-h" or "--help" or "help") { Console.WriteLine(Help); return 0; }
        var cmd = argv[0];
        var a = Args.Parse(argv.Skip(1));
        try
        {
            return cmd switch
            {
                "screens" => Screens(a),
                "inspect" => Inspect(a),
                "render" => Render(a),
                "compare" => Compare(a),
                "validate" => Validate(a),
                "compile" => Compile(a),
                "install" => Install(a),
                "activate" => Activate(a),
                "uninstall" => Uninstall(a),
                "status" => Status(a),
                "new-project" => NewProject(a),
                "add-screen" => AddScreen(a),
                "export-screen" => ExportScreen(a),
                "import-screen" => ImportScreen(a),
                "texts" => Texts(a),
                "fix-margins" => FixMargins(a),
                "live" => Live(a),
                "deps" => Deps(a),
                "actions" => Emit(new { ok = true, actions = ActionCatalog.All }),
                "api" => Api(),
                _ => Fail($"unknown command '{cmd}'"),
            };
        }
        catch (Exception ex) { return Fail(ex.Message); }
    }

    const string Help = """
        mrmenu <command> [options]      Master Rallye Menu Builder CLI (JSON output)

          screens       --game DIR                                     retail screens and their sources
          inspect       --game DIR --screen S [--project P] [--aspect A] elements, bounds, hitboxes, navigation
          render        --game DIR --screen S --out F.png [--project P] [--aspect 16:9|WxH] [--mode stock|centered|margins]
                        [--size WxH] [--focus ID] [--hitboxes] [--nav] [--safe] [--original]
          compare       --game DIR --project P --screen S --out F.png [--aspect A] [--mode M]   original | modified side by side
          validate      --game DIR --project P                         findings (exit 1 on errors)
          compile       --game DIR --project P --out DIR               publish the layout under DIR/MenuBuilder/Layouts (dry run, not activated)
          install       --game DIR --project P [--target EXEDIR] [--no-activate] [--replace-foreign]
                                                                       transactional publish to <game|target>/MenuBuilder/Layouts/<name>;
                                                                       errors block it; outcome Installed|Updated|ValidationFailed|
                                                                       RollbackCompleted|InstallationFailed
          activate      --game DIR (--layout NAME | --classic)         switch layout / back to the Classic frontend
          uninstall     --game DIR --layout NAME                       remove an installed layout
          status        --game DIR                                     installed layouts, active selection, runtime log tail
          new-project   --game DIR --out P --name N [--screens A,B]    project with retail screens prepared for editing
          add-screen    --game DIR --project P --screen S [--custom --base GraphicsMain --title T]
          export-screen --project P --screen S --out F.mrscreen.json
          import-screen --project P --in F.mrscreen.json [--rename N]
          texts         --game DIR [--group G] [--language L]          native localized text table
          fix-margins   --game DIR --project P --screen S              quick fix for renderer PreserveMargins matches
          live          --game DIR                                     latest runtime live dumps (in-game eggs/focus/hitboxes)
          deps          --game DIR --project P --screen S [--element E] native dependency class of elements
          actions                                                      typed action/value catalog
          api                                                          machine-readable description of this API
        """;

    static int Fail(string message)
    {
        Console.WriteLine(JsonSerializer.Serialize(new { ok = false, error = message }, Out));
        return 2;
    }

    static int Emit(object o, int code = 0) { Console.WriteLine(JsonSerializer.Serialize(o, Out)); return code; }

    sealed class Args
    {
        public Dictionary<string, string> Values = new(StringComparer.OrdinalIgnoreCase);
        public HashSet<string> Flags = new(StringComparer.OrdinalIgnoreCase);
        public static Args Parse(IEnumerable<string> argv)
        {
            var a = new Args(); var list = argv.ToList();
            for (int i = 0; i < list.Count; i++)
            {
                if (!list[i].StartsWith("--")) continue;
                var k = list[i][2..];
                if (i + 1 < list.Count && !list[i + 1].StartsWith("--")) a.Values[k] = list[++i]; else a.Flags.Add(k);
            }
            return a;
        }
        public string Req(string k) => Values.TryGetValue(k, out var v) ? v : throw new ArgumentException($"--{k} is required");
        public string? Opt(string k) => Values.TryGetValue(k, out var v) ? v : null;
        public bool Has(string k) => Flags.Contains(k) || Values.ContainsKey(k);
    }

    static Workspace Ws(Args a) => new(a.Req("game"), a.Opt("exe") ?? (a.Opt("target") is { } t ? Path.Combine(t, "MRallye.exe") : null));
    static MenuProject? Project(Args a) => a.Opt("project") is { } p ? MenuProject.Load(p) : null;

    static ScreenDef ScreenOf(Workspace ws, MenuProject? project, string name, bool original = false)
    {
        if (!original && project?.Screen(name) is { } s) return s;
        var retail = ws.RetailScreens().FirstOrDefault(r => r.name.Equals(name, StringComparison.OrdinalIgnoreCase));
        if (retail.name == null) throw new ArgumentException($"screen {name} is neither in the project nor a retail screen");
        return ws.NewRetailScreen(retail.name);
    }

    static InterfaceMode Mode(string? m) => m?.ToLowerInvariant() switch
    {
        null or "stock" or "0" => InterfaceMode.Stock,
        "centered" or "centered4x3" or "1" => InterfaceMode.Centered4x3,
        "margins" or "preservemargins" or "2" => InterfaceMode.PreserveMargins,
        _ => throw new ArgumentException($"bad mode {m}"),
    };

    static (int w, int h, string aspect) Size(Args a)
    {
        var aspect = a.Opt("aspect") ?? "4:3";
        var ratio = Aspect.Parse(aspect).Ratio;
        if (a.Opt("size") is { } s)
        {
            var p = s.ToLowerInvariant().Split('x');
            return (int.Parse(p[0]), int.Parse(p[1]), aspect);
        }
        int h = 720;
        return ((int)Math.Round(h * ratio), h, aspect);
    }

    static string NearestVariant(MenuProject? project, double ratio) =>
        Aspect.Nearest(project?.Settings.Aspects is { Count: > 0 } l ? l : new List<string> { "4:3" }, ratio);

    static int Screens(Args a)
    {
        using var ws = Ws(a);
        return Emit(new
        {
            ok = true, exe = ws.Exe?.Sha256, retail = ws.Exe?.IsRetail, exeError = ws.ExeError,
            screens = ws.RetailScreens().Select(s => new { s.id, s.name, s.source, focusables = ws.Compiler.Base(s.name).Focusables.Count() }),
        });
    }

    static object Describe(Workspace ws, Egg e)
    {
        var f = e.Focusable;
        var run = ws.Layout.Text(e);
        return new
        {
            name = e.Name, kind = e.Kind.ToString(), x = e.X, y = e.Y, scaleX = e.ScaleX, scaleY = e.ScaleY,
            model = e.Model, bank = e.BankIndex, drawPriority = e.DrawPriority, visible = e.Visible,
            ais = e.AiNames.ToArray(),
            bounds = R(ws.Layout.Bounds(e)),
            hitbox = f != null ? R(ws.Layout.Hitbox(e)) : null,
            buttonId = e.ButtonId,
            nav = f != null && f.Has("Up Path") ? new { up = f.GetInt("Up Path"), down = f.GetInt("Down Path"), left = f.GetInt("Left Path"), right = f.GetInt("Right Path") } : null,
            enabled = f?.Get("Enabled") is { } en ? en == "True" : (bool?)null,
            text = run?.Text, font = run?.FontName,
        };
    }
    static double[] R(UiRect r) => new[] { Math.Round(r.X0, 2), Math.Round(r.Y0, 2), Math.Round(r.X1, 2), Math.Round(r.Y1, 2) };

    static int Inspect(Args a)
    {
        using var ws = Ws(a);
        var project = Project(a);
        var screen = ScreenOf(ws, project, a.Req("screen"), a.Has("original"));
        var doc = a.Opt("aspect") is { } asp && project != null ? ws.SceneVariant(project, screen, asp) : ws.Scene(project ?? new MenuProject(), screen);
        return Emit(new { ok = true, screen = screen.Name, baseScene = screen.Base, screenAi = doc.ScreenAi, elements = doc.Eggs.Select(e => Describe(ws, e)) });
    }

    static SceneRenderer.Canvas Draw(Workspace ws, MenuProject? project, ScreenDef screen, Args a, int w, int h, string aspect, bool original)
    {
        var p = project ?? new MenuProject();
        var variant = original ? "4:3" : NearestVariant(project, Aspect.Parse(aspect).Ratio);
        var doc = original ? ws.Compiler.Base(screen.Base) : ws.SceneVariant(p, screen, variant);
        var mode = Mode(a.Opt("mode"));
        if (mode == InterfaceMode.Stock && !original) doc = ws.SceneVariant(p, screen, "4:3");
        return ws.Renderer.Render(doc, new RenderOptions
        {
            Width = w, Height = h, Mode = mode, ShowHitboxes = a.Has("hitboxes"), ShowNavigation = a.Has("nav"), ShowSafeArea = a.Has("safe"),
            FocusedId = a.Opt("focus") is { } f ? int.Parse(f) : null,
        });
    }

    static int Render(Args a)
    {
        using var ws = Ws(a);
        var project = Project(a);
        var screen = ScreenOf(ws, project, a.Req("screen"), a.Has("original"));
        var (w, h, aspect) = Size(a);
        var c = Draw(ws, project, screen, a, w, h, aspect, a.Has("original"));
        var outPath = a.Req("out");
        Png.Save(outPath, c.Px, c.W, c.H);
        return Emit(new { ok = true, @out = Path.GetFullPath(outPath), width = w, height = h, mode = Mode(a.Opt("mode")).ToString(), missing = ws.Assets.Missing.Distinct() });
    }

    static int Compare(Args a)
    {
        using var ws = Ws(a);
        var project = Project(a) ?? throw new ArgumentException("--project is required");
        var screen = ScreenOf(ws, project, a.Req("screen"));
        var (w, h, aspect) = Size(a);
        var left = Draw(ws, project, ws.NewRetailScreen(screen.IsCustom ? screen.Base : screen.Base), a, w, h, aspect, true);
        var right = Draw(ws, project, screen, a, w, h, aspect, false);
        var px = new uint[(w * 2 + 8) * h];
        Array.Fill(px, 0xFF202020);
        for (int y = 0; y < h; y++)
        {
            Array.Copy(left.Px, y * w, px, y * (w * 2 + 8), w);
            Array.Copy(right.Px, y * w, px, y * (w * 2 + 8) + w + 8, w);
        }
        Png.Save(a.Req("out"), px, w * 2 + 8, h);
        return Emit(new { ok = true, @out = Path.GetFullPath(a.Req("out")) });
    }

    static object Report(List<Finding> f) => f.Select(x => new
    {
        severity = x.Severity.ToString(), screen = x.Screen, element = x.Element, elementType = x.ElementType, code = x.Code,
        message = x.Message, operation = x.Operation, fix = x.Fix, aspect = x.Aspect,
    });

    static int Outcome(Installer.InstallResult res) => Emit(new
    {
        ok = res.Ok, outcome = res.Outcome.ToString(), title = res.Title, message = res.Message, directory = res.Directory,
        files = res.Files, keptBackup = res.KeptBackup,
        errors = res.Findings.Count(f => f.Severity == Severity.Error), warnings = res.Findings.Count(f => f.Severity == Severity.Warning),
        findings = Report(res.Findings),
    }, res.Ok ? 0 : res.Outcome == Installer.Outcome.ValidationFailed ? 1 : 3);

    static int Validate(Args a)
    {
        using var ws = Ws(a);
        var project = Project(a) ?? throw new ArgumentException("--project is required");
        var (layout, findings) = ws.Build(project);
        int errors = findings.Count(f => f.Severity == Severity.Error);
        return Emit(new
        {
            ok = errors == 0, errors, warnings = findings.Count(f => f.Severity == Severity.Warning),
            screens = layout.Screens.Select(s => new
            {
                s.Name, s.SceneName, s.NativeId, s.IsCustom, s.BaseSource,
                buttons = s.Buttons.Select(b => new { b.Id, b.Egg, kind = b.Kind.ToString(), status = b.Status.ToString(), action = b.Action.ToString(), local = R(b.Local) }),
            }),
            findings = Report(findings),
        }, errors == 0 ? 0 : 1);
    }

    static int Compile(Args a)
    {
        using var ws = Ws(a);
        var project = Project(a) ?? throw new ArgumentException("--project is required");
        var outDir = Path.GetFullPath(a.Req("out"));
        Directory.CreateDirectory(outDir);
        return Outcome(ws.Install(project, new Installer.Options { Activate = false, TargetRoot = outDir }));
    }

    static int Install(Args a)
    {
        using var ws = Ws(a);
        var project = Project(a) ?? throw new ArgumentException("--project is required");
        if (a.Has("force")) throw new ArgumentException("--force was removed: validation errors always block installation (use --replace-foreign only to replace another project's layout of the same name)");
        return Outcome(ws.Install(project, new Installer.Options { Activate = !a.Has("no-activate"), TargetRoot = a.Opt("target"), ReplaceForeign = a.Has("replace-foreign") }));
    }

    static int Activate(Args a)
    {
        var root = a.Req("game");
        if (a.Has("classic")) Installer.SetActive(root, null);
        else
        {
            var name = a.Req("layout");
            if (!Directory.Exists(Installer.LayoutDir(root, name))) throw new ArgumentException($"layout {name} is not installed");
            Installer.SetActive(root, name);
        }
        var c = Installer.ReadConfig(root);
        return Emit(new { ok = true, enabled = c.enabled, layout = c.layout });
    }

    static int Uninstall(Args a) => Emit(new { ok = Installer.Uninstall(a.Req("game"), a.Req("layout")) });

    static int Deps(Args a)
    {
        using var ws = Ws(a);
        var project = Project(a) ?? new MenuProject();
        var screen = ScreenOf(ws, project, a.Req("screen"));
        if (project.Screen(screen.Name) == null) project.Screens.Add(screen);
        var analyzer = new DependencyAnalyzer(ws);
        var names = a.Opt("element") is { } e ? new List<string> { e } : ws.Compiler.BuildScene(project, screen).Eggs.Select(x => x.Name).ToList();
        return Emit(new
        {
            ok = true, screen = screen.Name,
            elements = names.Select(n => analyzer.Analyze(project, screen, n)).Select(r => new
            {
                element = r.Element, @class = DependencyReport.Label(r.Class), blocksDelete = r.BlocksDelete, blocksRename = r.BlocksRename, canHide = r.CanHide,
                dependencies = r.Dependencies.Select(d => new { d.Kind, d.Detail }),
            }),
        });
    }

    static int Status(Args a)
    {
        var root = a.Req("game");
        var c = Installer.ReadConfig(root);
        var log = Path.Combine(root, Installer.Folder, "MenuBuilder.log");
        return Emit(new
        {
            ok = true, enabled = c.enabled, layout = c.layout, installed = Installer.InstalledLayouts(root),
            runtime = File.Exists(Path.Combine(root, "dinput8.dll")) ? "dinput8.dll present" : "dinput8.dll missing",
            logTail = File.Exists(log) ? File.ReadAllLines(log).TakeLast(40) : null,
        });
    }

    static int NewProject(Args a)
    {
        using var ws = Ws(a);
        var p = new MenuProject { Name = LayoutName.Validate(a.Req("name")), Id = MenuProject.NewId() };
        foreach (var s in (a.Opt("screens") ?? "MainMenu").Split(',', StringSplitOptions.RemoveEmptyEntries)) p.Screens.Add(ws.NewRetailScreen(s.Trim()));
        p.Save(a.Req("out"));
        return Emit(new { ok = true, project = Path.GetFullPath(a.Req("out")), screens = p.Screens.Select(s => s.Name) });
    }

    static int AddScreen(Args a)
    {
        using var ws = Ws(a);
        var path = a.Req("project");
        var p = MenuProject.Load(path);
        var name = a.Req("screen");
        if (p.Screen(name) != null) throw new ArgumentException($"screen {name} already in project");
        if (a.Has("custom") && !Ids.IsScreenName(name)) throw new ArgumentException($"'{name}' is not a valid custom screen name (letters and digits, first a letter)");
        p.Screens.Add(a.Has("custom") ? ws.NewCustomScreen(name, a.Opt("title"), a.Opt("base") ?? Compiler.HostScreen) : ws.NewRetailScreen(name));
        p.Save(path);
        return Emit(new { ok = true, screens = p.Screens.Select(s => new { s.Name, s.Kind, s.Base }) });
    }

    static int ExportScreen(Args a)
    {
        var p = MenuProject.Load(a.Req("project"));
        File.WriteAllText(a.Req("out"), Workspace.ExportScreen(p, a.Req("screen")));
        return Emit(new { ok = true, @out = Path.GetFullPath(a.Req("out")) });
    }

    static int ImportScreen(Args a)
    {
        var path = a.Req("project");
        var p = MenuProject.Load(path);
        var s = Workspace.ImportScreen(p, File.ReadAllText(a.Req("in")), a.Opt("rename"));
        p.Save(path);
        return Emit(new { ok = true, screen = s.Name });
    }

    /// <summary>Applies the PreserveMargins quick fix to every flagged egg of a screen (adds the screen if needed).</summary>
    static int FixMargins(Args a)
    {
        using var ws = Ws(a);
        var path = a.Req("project");
        var p = MenuProject.Load(path);
        var name = a.Req("screen");
        if (p.Screen(name) == null) p.Screens.Add(ws.NewRetailScreen(name));
        var session = new EditorSession(ws, p, path);
        session.SelectScreen(name);
        var flagged = session.Scene().Eggs.Where(e => e.Visible && WidescreenModel.MarginDirection(e.X, e.Y, e.Kind == ElementKind.XYButton) != 0).Select(e => e.Name).ToList();
        var done = flagged.Select(n => session.FixMargin(n)).ToList();
        session.Save();
        return Emit(new { ok = true, screen = name, fixes = done });
    }

    static int Texts(Args a)
    {
        using var ws = Ws(a);
        int lang = int.Parse(a.Opt("language") ?? "0");
        var g = a.Opt("group") is { } gs ? int.Parse(gs) : (int?)null;
        var rows = ws.Exe?.AllTexts(lang).Where(t => g == null || t.group == g).OrderBy(t => t.group).ThenBy(t => t.index)
            .Select(t => new { t.group, t.index, t.text });
        return Emit(new { ok = true, fonts = ws.Exe?.Fonts, texts = rows });
    }

    static int Live(Args a)
    {
        var dir = Path.Combine(a.Req("game"), Installer.Folder, "live");
        if (!Directory.Exists(dir)) return Emit(new { ok = false, error = "no live dumps yet (enable LiveDump and open a screen in game)" }, 1);
        var files = Directory.GetFiles(dir, "*.txt").OrderByDescending(File.GetLastWriteTimeUtc);
        return Emit(new { ok = true, dumps = files.Select(f => new { file = f, time = File.GetLastWriteTime(f), lines = File.ReadAllLines(f) }) });
    }

    static int Api() => Emit(new
    {
        ok = true, format = MenuProject.FormatName, version = MenuProject.CurrentVersion,
        actions = ActionBinding.Types,
        actionCatalog = ActionCatalog.All.Select(x => new { x.Id, x.Title, owner = x.Owner.ToString(), x.IsAction, x.HasValue, x.Description, x.ValueExample, x.Args, x.LegacyId }),
        installOutcomes = Enum.GetNames<Installer.Outcome>(),
        exitCodes = new { ok = 0, validationFailed = 1, usageOrIo = 2, installationFailedOrRolledBack = 3 },
        interfaceModes = Enum.GetNames<InterfaceMode>(), aspects = Aspect.Standard.Select(x => x.Key),
        elementPatch = ElementPatch.Fields.Select(p => new { name = JsonNamingPolicy.CamelCase.ConvertName(p.Name), type = (Nullable.GetUnderlyingType(p.PropertyType) ?? p.PropertyType).Name }),
        commands = new[] { "screens", "inspect", "render", "compare", "validate", "compile", "install", "activate", "uninstall", "status", "new-project", "add-screen", "export-screen", "import-screen", "texts", "fix-margins", "live", "deps", "actions", "api" },
    });
}
