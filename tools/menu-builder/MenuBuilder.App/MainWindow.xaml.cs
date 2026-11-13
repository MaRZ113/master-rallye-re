using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Text.Json;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Shapes;
using MenuBuilder.Core;
using Microsoft.Win32;
using RenderOptions = MenuBuilder.Core.RenderOptions;

namespace MenuBuilder.App;

public sealed class AppSettings
{
    public static bool Persist = true;
    public string? GameRoot { get; set; }
    public string? LastProject { get; set; }
    public bool SmartGuides { get; set; } = true;
    static string File_ => System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "MRMenuBuilder", "settings.json");
    public static AppSettings Load() { try { return JsonSerializer.Deserialize<AppSettings>(File.ReadAllText(File_)) ?? new(); } catch { return new(); } }
    public void Save() { if (!Persist) return; try { Directory.CreateDirectory(System.IO.Path.GetDirectoryName(File_)!); File.WriteAllText(File_, JsonSerializer.Serialize(this)); } catch { } }
}

public partial class MainWindow : Window
{
    readonly AppSettings _settings = AppSettings.Load();
    Workspace? _ws;
    EditorSession? _s;
    SceneRenderer.Canvas? _canvas;
    SceneDocument? _scene;
    List<Finding> _findings = new();
    CompiledLayout? _compiled;
    bool _refreshing;
    int? _interactFocus;
    Dictionary<int, (string egg, UiRect rect)>? _live;
    string? _liveScene;
    string? _clipboard;

    // ---- drag state (authored UI units, y up) ----------------------------------------------------
    enum DragKind { None, Move, Scale }
    DragKind _drag;
    Point _dragStart;
    double _dragDx, _dragDy;
    UiRect _dragBox;             // selection bounds when the drag started
    int _handle;                 // 0 TL, 1 T, 2 TR, 3 R, 4 BR, 5 B, 6 BL, 7 L
    double _kx = 1, _ky = 1, _ax, _ay;
    List<SnapGuide> _guides = new();
    double _dragDxCommitted;
    const double SnapPixels = 7;

    static readonly (string Label, string Template)[] Builtins =
    {
        ("Long menu button", "MainMenu/OnePlayer"),
        ("Curved button", "QuickRace/VehicleSetup"),
        ("Small curved button", "VehicleSelect/SelectCar"),
        ("Option row (multistate)", "QuickModeSelect/Mode"),
        ("Left arrow", "VehicleSelect/LeftArrow"),
        ("Right arrow", "VehicleSelect/RightArrow"),
        ("Text", "MainMenu/SureText"),
        ("Title text", "MainMenu/MM_TitleText"),
        ("Value text (live game value)", "QuickRace/ModeText"),
        ("Image (logo)", "QuickRace/RaceLogo"),
        ("Image (flag)", "QuickRace/RaceFlag"),
        ("Panel (tile box)", "MainMenu/SureTiles"),
        ("Stat bar (gradient)", "VehicleSelect/SpeedBar"),
    };

    public MainWindow()
    {
        InitializeComponent();
        foreach (var a in Aspect.Standard) AspectBox.Items.Add(a.Key);
        AspectBox.Items.Add("Window size…");
        AspectBox.SelectedIndex = 0;
        foreach (var m in new[] { "Stock (4:3 stretch)", "Centered 4:3", "Preserve margins" }) ModeBox.Items.Add(m);
        ModeBox.SelectedIndex = 0;
        foreach (var c in new[] { "Off", "Original", "Split", "Onion" }) CompareBox.Items.Add(c);
        CompareBox.SelectedIndex = 0;
        foreach (var g in new[] { "0", "1", "5", "10" }) SnapBox.Items.Add(g);
        SnapBox.SelectedIndex = 2;
        SmartBox.IsChecked = _settings.SmartGuides;
        Loaded += (_, _) => Startup();
    }

    // ---- startup / project lifecycle ---------------------------------------------------------------
    readonly Dictionary<string, string> _args = ParseArgs(Environment.GetCommandLineArgs().Skip(1).ToArray());
    static Dictionary<string, string> ParseArgs(string[] a)
    {
        var d = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        for (int i = 0; i < a.Length; i++)
            if (a[i].StartsWith("--")) d[a[i][2..]] = i + 1 < a.Length && !a[i + 1].StartsWith("--") ? a[++i] : "1";
        return d;
    }
    bool Testing => _args.ContainsKey("selftest");

    void Startup()
    {
        if (_args.TryGetValue("game", out var argGame))
        {
            _settings.GameRoot = argGame;
            AppSettings.Persist = false;
            if (!OpenWorkspace(argGame)) { Close(); return; }
            if (_args.TryGetValue("project", out var argProject)) OpenProject(argProject); else NewProject("MyMenus", saved: true);
            if (Testing) Dispatcher.BeginInvoke(new Action(() => SelfTest(_args["selftest"])), System.Windows.Threading.DispatcherPriority.ApplicationIdle);
            return;
        }
        var root = _settings.GameRoot;
        if (root == null || !File.Exists(System.IO.Path.Combine(root, "Data.sma")))
        {
            MessageBox.Show(this, "Select the Master Rallye game folder (the one with MRallye.exe and Data.sma). The editor only reads it; layouts are installed into <game>\\MenuBuilder.", "Menu Builder");
            if (ChooseGameFolder() is not { } picked) { Close(); return; }
            root = picked;
        }
        if (!OpenWorkspace(root!)) { Close(); return; }
        if (_settings.LastProject != null && File.Exists(_settings.LastProject) && OpenProject(_settings.LastProject)) return;
        NewProject("MyMenus", saved: true);
    }

    string? ChooseGameFolder()
    {
        var d = new OpenFolderDialog { Title = "Master Rallye game folder" };
        if (d.ShowDialog(this) != true) return null;
        if (!File.Exists(System.IO.Path.Combine(d.FolderName, "Data.sma")) && !File.Exists(System.IO.Path.Combine(d.FolderName, "MRallye.exe")))
        {
            MessageBox.Show(this, $"{d.FolderName} has neither MRallye.exe nor Data.sma.", "Game folder");
            return null;
        }
        return d.FolderName;
    }

    bool OpenWorkspace(string root)
    {
        try
        {
            var ws = new Workspace(root);
            var old = _ws;
            _ws = ws;
            _settings.GameRoot = root; _settings.Save();
            BuildInsertMenu();
            Status($"Game: {root}  EXE {(_ws.Exe?.IsRetail == true ? "retail (verified)" : _ws.Exe != null ? "NOT retail" : "missing")}");
            if (_s != null)
            {
                // Same project, path, dirty state and undo history; only the resource bindings change.
                var report = _s.Rebind(ws);
                if (report.Count > 0)
                    Dialogs.Choice(this, "Game resources", $"The project refers to {report.Count} resource(s) this installation does not provide. The edits are kept; fix or remove them before installing.",
                        string.Join(Environment.NewLine, report.Select(f => f.ToString())), "OK");
            }
            old?.Dispose();
            return true;
        }
        catch (Exception ex) { MessageBox.Show(this, ex.Message, "Game folder"); return false; }
    }

    void Attach(EditorSession s)
    {
        if (_s != null) _s.Changed -= OnSessionChanged;
        _s = s; _s.Changed += OnSessionChanged;
        _interactFocus = null; _live = null;
        BuildInsertMenu();
        RefreshAll();
    }

    void NewProject(string name, bool saved = false)
    {
        var p = new MenuProject { Name = name, Id = MenuProject.NewId() };
        p.Screens.Add(_ws!.NewRetailScreen("MainMenu"));
        Attach(new EditorSession(_ws, p, null, saved));
    }

    bool OpenProject(string path)
    {
        try
        {
            var p = MenuProject.Load(path);
            Attach(new EditorSession(_ws!, p, path));
            _settings.LastProject = path; _settings.Save();
            var report = _s!.ResourceReport();
            if (report.Count > 0) Status($"Opened {path}: {report.Count} resource problem(s), see Validation");
            return true;
        }
        catch (Exception ex) { MessageBox.Show(this, ex.Message, "Open project"); return false; }
    }

    /// <summary>Asks before an action that would lose unsaved edits. Save / Don't save / Cancel.</summary>
    bool ConfirmLoseChanges(string action)
    {
        if (_s == null || !_s.Dirty) return true;
        int c = Dialogs.Choice(this, "Unsaved changes", $"{_s.Project.Name} has unsaved changes. Save them before you {action}?", null, "Save", "Don't save", "Cancel");
        if (c == 0) return SaveProject(false);
        return c == 1;
    }

    bool SaveProject(bool saveAs)
    {
        if (_s == null) return false;
        var path = _s.Path;
        if (saveAs || path == null)
        {
            var d = new SaveFileDialog { Filter = "Menu Builder project (*.mrmenu.json)|*.mrmenu.json", FileName = _s.Project.Name + ".mrmenu.json" };
            if (d.ShowDialog(this) != true) return false;
            path = d.FileName;
        }
        try
        {
            _s.Save(path);
            _settings.LastProject = path; _settings.Save();
            Status("Saved " + path);
            return true;
        }
        catch (Exception ex) { MessageBox.Show(this, $"The project was NOT saved: {ex.Message}", "Save"); return false; }
    }

    void OnSessionChanged() => RefreshAll();

    void RefreshAll()
    {
        if (_s == null) return;
        _refreshing = true;
        Title = $"Master Rallye Menu Builder — {_s.Project.Name}{(_s.Dirty ? " *" : "")} — {(_s.Path ?? "not saved")}";
        RefreshScreens();
        _refreshing = false;
        RenderView();
        RefreshElements();
        RefreshProps();
        RunValidation();
    }

    /// <summary>Project screens first, then every other frontend screen of the installation (opened on demand).</summary>
    void RefreshScreens()
    {
        ScreenList.Items.Clear();
        var edited = _s!.Project.Screens.Where(sc => !Compiler.IsUnchanged(sc)).ToList();
        ScreenList.Items.Add(new ListBoxItem { Content = "PROJECT", IsEnabled = false, FontWeight = FontWeights.Bold, Foreground = Brushes.Gold });
        foreach (var sc in edited)
            ScreenList.Items.Add(new ListBoxItem { Content = $"{(sc.IsCustom ? "★ " : "✎ ")}{sc.Name}{(sc.IsCustom ? "  (custom)" : "")}", Tag = sc.Name, IsSelected = sc == _s.Screen });
        ScreenList.Items.Add(new ListBoxItem { Content = "ALL FRONTEND SCREENS", IsEnabled = false, FontWeight = FontWeights.Bold, Foreground = Brushes.Gold, Margin = new Thickness(0, 6, 0, 0) });
        foreach (var (id, name, source) in _ws!.RetailScreens().OrderBy(r => r.name))
        {
            if (edited.Any(sc => !sc.IsCustom && sc.Name.Equals(name, StringComparison.OrdinalIgnoreCase))) continue;
            ScreenList.Items.Add(new ListBoxItem
            {
                Content = $"   {name}{(source != "archive" ? "  [" + source + "]" : "")}", Tag = name, Foreground = Brushes.Silver,
                IsSelected = _s.Screen?.Name.Equals(name, StringComparison.OrdinalIgnoreCase) == true, ToolTip = $"native screen #{id}",
            });
        }
        (ScreenList.SelectedItem as ListBoxItem)?.BringIntoView();
    }

    // ---- view ------------------------------------------------------------------------------------
    string AspectKey() => AspectBox.SelectedItem as string is { } a && a != "Window size…" ? a : _customAspect;
    string _customAspect = "16:9";
    InterfaceMode Mode() => (InterfaceMode)Math.Max(0, ModeBox.SelectedIndex);
    double SnapStep() => double.TryParse(SnapBox.SelectedItem as string, out var v) ? v : 0;

    void OnViewChanged(object sender, RoutedEventArgs e)
    {
        if (!IsLoaded || _s == null) return;
        if (sender == AspectBox && AspectBox.SelectedItem as string == "Window size…")
        {
            var r = Dialogs.Prompt(this, "Window size", "Client size of the game window (e.g. 1920x1080, 2560x1080, 1280x1024):", "1920x1080");
            if (r != null) { try { Aspect.Parse(r); _customAspect = r; } catch { MessageBox.Show(this, "Use WIDTHxHEIGHT"); } }
        }
        if (sender == SmartBox) { _settings.SmartGuides = SmartBox.IsChecked == true; _settings.Save(); }
        _s.EditAspectOverride = AspectOverrideBox.IsChecked == true;
        RenderView();
    }

    void OnViewSizeChanged(object sender, SizeChangedEventArgs e) { if (_s != null) RenderView(); }

    /// <summary>Variant the runtime would serve for this view: nearest compiled aspect, 4:3 when the renderer stretches.</summary>
    string VariantKey()
    {
        var ratio = Aspect.Parse(AspectKey()).Ratio;
        if (Mode() == InterfaceMode.Stock) return "4:3";
        return Aspect.Nearest(_s!.Project.Settings.Aspects.Append("4:3").Distinct(), ratio);
    }

    /// <param name="preview">Document to draw instead of the project scene (live drag preview).</param>
    void RenderView(SceneDocument? preview = null)
    {
        if (_s?.Screen == null || _ws == null) return;
        var ratio = Aspect.Parse(AspectKey()).Ratio;
        double availW = Math.Max(200, ViewHost.ActualWidth - 16), availH = Math.Max(150, ViewHost.ActualHeight - 16);
        int h = (int)Math.Min(availH, availW / ratio), w = (int)(h * ratio);
        if (w < 64 || h < 48) return;
        if (preview == null)
        {
            _s.Aspect = VariantKey();
            try { _scene = _s.Variant(); }
            catch (Exception ex) { Status("Build error: " + ex.Message); return; }
        }
        var opt = new RenderOptions
        {
            Width = w, Height = h, Mode = Mode(), ShowHitboxes = HitboxBox.IsChecked == true, ShowNavigation = NavBox.IsChecked == true,
            ShowSafeArea = SafeBox.IsChecked == true, GhostHidden = HiddenBox.IsChecked == true, ShowRuntimeHidden = HiddenBox.IsChecked == true,
            FocusedId = InteractBox.IsChecked == true ? _interactFocus ?? FirstFocus() : SelectedFocusId(),
        };
        var compare = CompareBox.SelectedIndex;
        SceneRenderer.Canvas c;
        if (compare == 1 && preview == null) c = _ws.Renderer.Render(_s.Original(), opt);
        else
        {
            c = _ws.Renderer.Render(preview ?? _scene!, opt);
            if (compare >= 2)
            {
                var o = _ws.Renderer.Render(_s.Original(), new RenderOptions { Width = w, Height = h, Mode = Mode() });
                for (int y = 0; y < h; y++)
                    for (int x = 0; x < w; x++)
                    {
                        int i = y * w + x;
                        if (compare == 2) { if (x < w / 2) c.Px[i] = o.Px[i]; else if (x == w / 2) c.Px[i] = 0xFFFFD000; }
                        else c.Px[i] = Mix(c.Px[i], o.Px[i]);
                    }
            }
        }
        if (GridBox.IsChecked == true) DrawGrid(c);
        _canvas = c;
        var bmp = new WriteableBitmap(w, h, 96, 96, PixelFormats.Bgra32, null);
        bmp.WritePixels(new Int32Rect(0, 0, w, h), c.Px, w * 4, 0);
        View.Source = bmp;
        View.Width = w; View.Height = h; Overlay.Width = w; Overlay.Height = h;
        DrawOverlay();
    }

    static uint Mix(uint a, uint b) => 0xFF000000 | ((((a >> 16) & 255) + ((b >> 16) & 255)) / 2 << 16) | ((((a >> 8) & 255) + ((b >> 8) & 255)) / 2 << 8) | (((a & 255) + (b & 255)) / 2);

    void DrawGrid(SceneRenderer.Canvas c)
    {
        double step = Math.Max(5, SnapStep() >= 5 ? SnapStep() * 2 : 20);
        var (l, _) = c.ToUi(0, 0); var (r, _) = c.ToUi(c.W - 1, 0);
        for (double x = Math.Floor(l / step) * step; x <= r; x += step)
        {
            var p = c.ToPixel(x, 0);
            SceneRenderer.Line(c, p.x, 0, p.x, c.H - 1, x % 100 == 0 ? 0x30FFFFFFu : 0x16FFFFFFu);
        }
        for (double y = 0; y <= 480; y += step)
        {
            var p = c.ToPixel(0, y);
            SceneRenderer.Line(c, 0, p.y, c.W - 1, p.y, y % 100 == 0 ? 0x30FFFFFFu : 0x16FFFFFFu);
        }
    }

    Rect PixelRect(UiRect r)
    {
        var a = _canvas!.ToPixel(r.X0, r.Y0); var b = _canvas.ToPixel(r.X1, r.Y1);
        return new Rect(new Point(Math.Min(a.x, b.x), Math.Min(a.y, b.y)), new Point(Math.Max(a.x, b.x), Math.Max(a.y, b.y)));
    }

    double Shift(Egg e) => WidescreenModel.RendererShift(Mode(), _canvas!.Ratio, e.X, e.Y, e.Kind == ElementKind.XYButton);

    UiRect ShownBounds(Egg e) => _ws!.Layout.Bounds(e).Offset(Shift(e), 0);

    /// <summary>Union of the selected elements' bounds (authored units, as shown).</summary>
    UiRect SelectionBounds(SceneDocument doc)
    {
        UiRect r = default;
        foreach (var n in _s!.Selection) if (doc.Find(n) is { } e) r = r.Union(ShownBounds(e));
        return r;
    }

    static Point HandlePoint(UiRect b, int h) => h switch
    {
        0 => new(b.X0, b.Y1), 1 => new((b.X0 + b.X1) / 2, b.Y1), 2 => new(b.X1, b.Y1), 3 => new(b.X1, (b.Y0 + b.Y1) / 2),
        4 => new(b.X1, b.Y0), 5 => new((b.X0 + b.X1) / 2, b.Y0), 6 => new(b.X0, b.Y0), _ => new(b.X0, (b.Y0 + b.Y1) / 2),
    };
    static readonly Cursor[] HandleCursors = { Cursors.SizeNWSE, Cursors.SizeNS, Cursors.SizeNESW, Cursors.SizeWE, Cursors.SizeNWSE, Cursors.SizeNS, Cursors.SizeNESW, Cursors.SizeWE };

    /// <summary>Box being dragged, as it will be after the drop.</summary>
    UiRect DraggedBox() => _drag switch
    {
        DragKind.Move => _dragBox.Offset(_dragDx, _dragDy),
        DragKind.Scale => new UiRect(Math.Min(_ax + _kx * (_dragBox.X0 - _ax), _ax + _kx * (_dragBox.X1 - _ax)), Math.Min(_ay + _ky * (_dragBox.Y0 - _ay), _ay + _ky * (_dragBox.Y1 - _ay)),
                                     Math.Max(_ax + _kx * (_dragBox.X0 - _ax), _ax + _kx * (_dragBox.X1 - _ax)), Math.Max(_ay + _ky * (_dragBox.Y0 - _ay), _ay + _ky * (_dragBox.Y1 - _ay))),
        _ => _dragBox,
    };

    void DrawOverlay()
    {
        Overlay.Children.Clear();
        if (_canvas == null || _scene == null || _s == null) return;
        if (GuidesBox.IsChecked == true)
        {
            var a = PixelRect(new UiRect(0, 0, 640, 480));
            AddRect(a, Brushes.Transparent, new SolidColorBrush(Color.FromArgb(120, 0, 200, 255)), 1, dash: true);
            var mid = _canvas.ToPixel(320, 240);
            AddLine(mid.x, 0, mid.x, _canvas.H, Color.FromArgb(70, 0, 200, 255));
            AddLine(0, mid.y, _canvas.W, mid.y, Color.FromArgb(70, 0, 200, 255));
        }
        if (_drag != DragKind.None)
        {
            var box = DraggedBox();
            AddRect(PixelRect(box), new SolidColorBrush(Color.FromArgb(25, 255, 208, 0)), Brushes.Gold, 1.5);
            foreach (var g in _guides)
            {
                var p0 = g.Vertical ? _canvas.ToPixel(g.Pos, g.From) : _canvas.ToPixel(g.From, g.Pos);
                var p1 = g.Vertical ? _canvas.ToPixel(g.Pos, g.To) : _canvas.ToPixel(g.To, g.Pos);
                AddLine(p0.x, p0.y, p1.x, p1.y, Color.FromArgb(255, 255, 40, 200), 1.2);
            }
            var label = _drag == DragKind.Move
                ? $"{_dragDx:+0.#;-0.#;0}, {_dragDy:+0.#;-0.#;0}"
                : $"{box.Width:0.#} × {box.Height:0.#}   ({_kx * 100:0}% × {_ky * 100:0}%)";
            var pr = PixelRect(box);
            var t = new TextBlock { Text = label, Foreground = Brushes.Black, Background = Brushes.Gold, Padding = new Thickness(3, 0, 3, 0), FontSize = 11, IsHitTestVisible = false };
            Canvas.SetLeft(t, pr.Right + 6); Canvas.SetTop(t, pr.Bottom + 4);
            Overlay.Children.Add(t);
        }
        else
        {
            foreach (var name in _s.Selection)
            {
                var egg = _scene.Find(name);
                if (egg == null) continue;
                var r = PixelRect(ShownBounds(egg));
                AddRect(r, new SolidColorBrush(Color.FromArgb(30, 255, 208, 0)), Brushes.Gold, 1.5);
                if (_s.Selection.Count == 1 && egg.IsPrimaryFocusable && HitboxBox.IsChecked != true)
                    AddRect(PixelRect(_ws!.Layout.Hitbox(egg).Offset(Shift(egg), 0)), Brushes.Transparent, Brushes.OrangeRed, 1, dash: true);
            }
            if (_s.Selection.Count > 0 && InteractBox.IsChecked != true)
            {
                var b = SelectionBounds(_scene);
                if (!b.IsEmpty)
                    for (int h = 0; h < 8; h++)
                    {
                        var hp = HandlePoint(b, h);
                        var px = _canvas.ToPixel(hp.X, hp.Y);
                        var handle = new Rectangle { Width = 9, Height = 9, Fill = Brushes.Gold, Stroke = Brushes.Black, StrokeThickness = 1, Cursor = HandleCursors[h], Tag = "h" + h };
                        Canvas.SetLeft(handle, px.x - 4.5); Canvas.SetTop(handle, px.y - 4.5);
                        Overlay.Children.Add(handle);
                    }
            }
        }
        if (_live != null && _liveScene != null && string.Equals(_liveScene, CurrentSceneName(), StringComparison.OrdinalIgnoreCase))
            foreach (var (_, (_, rect)) in _live)
                AddRect(PixelRect(rect), Brushes.Transparent, Brushes.Cyan, 1, dash: true);
        var (vl, vr) = WidescreenModel.VisibleRange(Mode(), _canvas.Ratio);
        CursorText.Text = $"variant {VariantKey()}  visible x {vl:0}..{vr:0}";
    }

    void AddRect(Rect r, Brush fill, Brush stroke, double thickness, bool dash = false)
    {
        var shape = new Rectangle { Width = Math.Max(1, r.Width), Height = Math.Max(1, r.Height), Fill = fill, Stroke = stroke, StrokeThickness = thickness, IsHitTestVisible = false };
        if (dash) shape.StrokeDashArray = new DoubleCollection { 4, 3 };
        Canvas.SetLeft(shape, r.Left); Canvas.SetTop(shape, r.Top);
        Overlay.Children.Add(shape);
    }

    void AddLine(double x0, double y0, double x1, double y1, Color c, double thickness = 1) =>
        Overlay.Children.Add(new Line { X1 = x0, Y1 = y0, X2 = x1, Y2 = y1, Stroke = new SolidColorBrush(c), StrokeThickness = thickness, IsHitTestVisible = false });

    string CurrentSceneName() => Compiler.SceneNameOf(_s!.Screen!);

    int? SelectedFocusId() => _s!.Selection.Count == 1 ? _scene?.Find(_s.Selection[0])?.ButtonId : null;
    int? FirstFocus() => _s!.Screen!.DefaultFocus ?? _scene?.Focusables.Select(e => e.ButtonId).FirstOrDefault();

    // ---- canvas interaction ------------------------------------------------------------------------
    Egg? HitEgg(Point p)
    {
        if (_scene == null || _canvas == null) return null;
        var (ux, uy) = _canvas.ToUi(p.X, p.Y);
        var order = _scene.Eggs.Select((e, i) => (e, i)).OrderBy(t => t.e.DrawPriority).ThenByDescending(t => t.i).Select(t => t.e).ToList();
        foreach (var e in order)
        {
            if (e.Kind is ElementKind.Screen or ElementKind.Camera or ElementKind.Effect or ElementKind.Background) continue;
            if ((!e.Visible || LayoutEngine.NativeHidden(_scene, e)) && HiddenBox.IsChecked != true) continue;
            if (ShownBounds(e).Contains(ux, uy)) return e;
        }
        return order.FirstOrDefault(e => e.Kind == ElementKind.Background && ShownBounds(e).Contains(ux, uy));
    }

    /// <summary>Modifier keys of the current pointer gesture (the self-test sets them explicitly).</summary>
    ModifierKeys? _testMods;
    ModifierKeys Mods => _testMods ?? Keyboard.Modifiers;

    void OnCanvasDown(object sender, MouseButtonEventArgs e) => PointerDown(e.GetPosition(Overlay), e.OriginalSource);
    void OnCanvasMove(object sender, MouseEventArgs e) => PointerMove(e.GetPosition(Overlay));
    void OnCanvasUp(object sender, MouseButtonEventArgs e) => PointerUp();

    void PointerDown(Point p, object? source)
    {
        if (_s == null || _canvas == null) return;
        Overlay.Focus();
        if (InteractBox.IsChecked == true)
        {
            var (ux, uy) = _canvas.ToUi(p.X, p.Y);
            var b = _scene!.Focusables.Where(f => _ws!.Layout.Hitbox(_scene.VisualOf(f)).Offset(Shift(_scene.VisualOf(f)), 0).Contains(ux, uy)).LastOrDefault();
            if (b != null) { _interactFocus = b.ButtonId; RenderView(); ReportAction(b); }
            return;
        }
        if (source is Rectangle { Tag: string tag } && tag.StartsWith('h') && _s.Selection.Count > 0)
        {
            _drag = DragKind.Scale; _handle = tag[1] - '0'; _dragStart = p; _dragBox = SelectionBounds(_scene!);
            _kx = _ky = 1; _guides.Clear();
            var (ax, ay) = ScaleAnchor(_dragBox, _handle, Mods.HasFlag(ModifierKeys.Alt));
            _ax = ax; _ay = ay;
            Overlay.CaptureMouse(); DrawOverlay(); return;
        }
        var egg = HitEgg(p);
        if (egg == null) { _s.Selection.Clear(); SyncSelection(); return; }
        if (Mods.HasFlag(ModifierKeys.Control))
        {
            if (!_s.Selection.Remove(egg.Name)) _s.Selection.Add(egg.Name);
        }
        else if (!_s.Selection.Contains(egg.Name)) { _s.Selection.Clear(); _s.Selection.Add(egg.Name); }
        SyncSelection();
        if (!_s.Selection.Contains(egg.Name)) return;
        _drag = DragKind.Move; _dragStart = p; _dragDx = _dragDy = 0; _dragBox = SelectionBounds(_scene!); _guides.Clear();
        Overlay.CaptureMouse();
    }

    static (double x, double y) ScaleAnchor(UiRect b, int handle, bool fromCentre)
    {
        if (fromCentre) return ((b.X0 + b.X1) / 2, (b.Y0 + b.Y1) / 2);
        double ax = handle is 0 or 6 or 7 ? b.X1 : b.X0;   // left handles keep the right edge
        double ay = handle is 0 or 1 or 2 ? b.Y0 : b.Y1;   // top handles keep the bottom edge (y up)
        return (ax, ay);
    }

    /// <summary>Visible, non-selected elements the dragged box snaps to.</summary>
    List<UiRect> SnapTargets() => _scene!.Eggs
        .Where(e => !_s!.Selection.Contains(e.Name) && e.Visible && !LayoutEngine.NativeHidden(_scene, e) &&
                    e.Kind is not (ElementKind.Screen or ElementKind.Camera or ElementKind.Effect or ElementKind.Background))
        .Select(ShownBounds).Where(r => !r.IsEmpty && r.Width < 900).ToList();

    UiRect ScreenArea()
    {
        var (l, r) = WidescreenModel.VisibleRange(Mode(), _canvas!.Ratio);
        return new UiRect(l, 0, r, 480);
    }

    bool Smart() => SmartBox.IsChecked == true && !Mods.HasFlag(ModifierKeys.Alt);

    void PointerMove(Point p)
    {
        if (_canvas == null || _s == null) return;
        var (ux, uy) = _canvas.ToUi(p.X, p.Y);
        if (_drag == DragKind.None)
        {
            var hover = HitEgg(p);
            CursorText.Text = $"ui ({ux:0.0}, {uy:0.0})  {(hover != null ? hover.Name + " [" + hover.Kind + "]" : "")}  variant {VariantKey()}";
            return;
        }
        double kU = _canvas.VirtualWidth / _canvas.W, kV = 480.0 / _canvas.H;
        double threshold = SnapPixels * kU;
        if (_drag == DragKind.Move)
        {
            double dx = (p.X - _dragStart.X) * kU, dy = -(p.Y - _dragStart.Y) * kV;
            if (Mods.HasFlag(ModifierKeys.Shift)) { if (Math.Abs(dx) > Math.Abs(dy)) dy = 0; else dx = 0; } // axis lock
            _guides.Clear();
            bool sx = false, sy = false;
            if (Smart())
            {
                var r = Snapper.Move(_dragBox, dx, dy, SnapTargets(), ScreenArea(), threshold);
                (dx, dy, sx, sy) = (r.Dx, r.Dy, r.SnappedX, r.SnappedY);
                _guides = r.Guides;
            }
            if (!sx) dx = EditorSession.Snap(dx, SnapStep());
            if (!sy) dy = EditorSession.Snap(dy, SnapStep());
            _dragDx = dx; _dragDy = dy;
            RenderView(Preview());
            Status($"move {_dragDx:+0.##;-0.##;0}, {_dragDy:+0.##;-0.##;0}{(_guides.Count > 0 ? "  (snapped)" : "")}   Shift = axis lock, Alt = no snapping");
        }
        else if (_drag == DragKind.Scale)
        {
            bool centre = Mods.HasFlag(ModifierKeys.Alt);
            var (ax, ay) = ScaleAnchor(_dragBox, _handle, centre);
            _ax = ax; _ay = ay;
            bool movesX = _handle is not (1 or 5), movesY = _handle is not (3 or 7);
            // Pointer position → dragged edge position (snapped to neighbours' edges).
            double ex = ux, ey = uy;
            _guides.Clear();
            if (SmartBox.IsChecked == true && !centre)
            {
                var (ddx, ddy, g) = Snapper.Edges(_dragBox, movesX ? new[] { ex } : Array.Empty<double>(), movesY ? new[] { ey } : Array.Empty<double>(), SnapTargets(), ScreenArea(), threshold);
                ex += ddx; ey += ddy; _guides = g;
            }
            double w0 = Math.Max(1, _dragBox.Width), h0 = Math.Max(1, _dragBox.Height);
            double fixedX = _handle is 0 or 6 or 7 ? _dragBox.X1 : _dragBox.X0, fixedY = _handle is 0 or 1 or 2 ? _dragBox.Y0 : _dragBox.Y1;
            double kx = movesX ? Math.Abs(ex - (centre ? ax : fixedX)) * (centre ? 2 : 1) / w0 : 1;
            double ky = movesY ? Math.Abs(ey - (centre ? ay : fixedY)) * (centre ? 2 : 1) / h0 : 1;
            bool uniform = Mods.HasFlag(ModifierKeys.Shift);
            if (uniform) { var k = movesX && movesY ? Math.Max(kx, ky) : movesX ? kx : ky; kx = ky = k; }
            _kx = Math.Clamp(kx, 0.05, 20); _ky = Math.Clamp(ky, 0.05, 20);
            RenderView(Preview());
            Status($"scale {_kx * 100:0}% × {_ky * 100:0}%   Shift = keep proportions, Alt = from centre");
        }
    }

    /// <summary>The current scene with the drag applied to the selected eggs (drawn live while dragging).</summary>
    SceneDocument Preview()
    {
        var doc = _scene!.Clone();
        foreach (var n in _s!.Selection)
        {
            if (doc.Find(n) is not { } egg) continue;
            if (_drag == DragKind.Move) { egg.X = (float)(egg.X + _dragDx); egg.Y = (float)(egg.Y + _dragDy); }
            else if (_drag == DragKind.Scale)
            {
                egg.X = (float)(_ax - _kx * (_ax - egg.X)); egg.Y = (float)(_ay - _ky * (_ay - egg.Y));
                egg.ScaleX = (float)(egg.ScaleX * _kx); egg.ScaleY = (float)(egg.ScaleY * _ky);
            }
        }
        return doc;
    }

    void PointerUp()
    {
        Overlay.ReleaseMouseCapture();
        var kind = _drag;
        _drag = DragKind.None; _guides.Clear();
        try
        {
            _dragDxCommitted = kind == DragKind.Move ? _dragDx : 0;
            if (kind == DragKind.Move && (_dragDx != 0 || _dragDy != 0)) _s!.Move(_s.Selection, _dragDx, _dragDy, 0);
            else if (kind == DragKind.Scale && (Math.Abs(_kx - 1) > 1e-4 || Math.Abs(_ky - 1) > 1e-4)) _s!.ScaleAbout(_s.Selection, _kx, _ky, _ax, _ay);
            else RenderView();
        }
        catch (Exception ex) { MessageBox.Show(this, ex.Message, "Edit"); RenderView(); }
        _kx = _ky = 1; _dragDx = _dragDy = 0;
    }

    void OnCanvasRightUp(object sender, MouseButtonEventArgs e)
    {
        if (InteractBox.IsChecked == true) { Status("Back (-3): " + (_s!.Screen!.Back?.ToString() ?? (_s.Screen.IsCustom ? "← back" : "native"))); return; }
        var menu = new ContextMenu();
        void Item(string text, Action a) { var m = new MenuItem { Header = text }; m.Click += (_, _) => a(); menu.Items.Add(m); }
        Item("Duplicate", () => OnDuplicate(this, new RoutedEventArgs()));
        Item("Rename…", () => OnRename(this, new RoutedEventArgs()));
        Item("Hide", () => OnHide(this, new RoutedEventArgs()));
        Item("Show", () => OnShow(this, new RoutedEventArgs()));
        Item("Disable", () => OnDisable(this, new RoutedEventArgs()));
        Item("Enable", () => OnEnable(this, new RoutedEventArgs()));
        Item("Delete", () => OnDelete(this, new RoutedEventArgs()));
        Item("Dependencies…", () => OnDependencies(this, new RoutedEventArgs()));
        Item("Bring forward", () => _s!.ZOrder(-1));
        Item("Send backward", () => _s!.ZOrder(1));
        Item("Link navigation top→bottom", () => _s!.AutoLinkVertical());
        menu.IsOpen = true;
    }

    void ReportAction(Egg b)
    {
        var def = _s!.Screen!.Element(b.Name) ?? _s.Screen.ForBase(b.Name);
        var cb = _compiled?.Screens.FirstOrDefault(x => x.Name == _s.Screen.Name)?.Buttons.FirstOrDefault(x => x.Egg == b.Name);
        Status($"#{b.ButtonId} {b.Name}: {cb?.Action.ToString() ?? def?.Action?.ToString() ?? "native"} [{cb?.Status.ToString() ?? "?"}]{(cb?.Blocked == true ? " (blocked)" : "")}");
    }

    // ---- lists -----------------------------------------------------------------------------------
    void RefreshElements()
    {
        if (_scene == null) return;
        _refreshing = true;
        ElementList.Items.Clear();
        foreach (var e in _scene.Eggs.Select((e, i) => (e, i)).OrderByDescending(t => t.e.DrawPriority).ThenBy(t => t.i).Select(t => t.e))
        {
            var def = _s!.Screen!.Element(e.Name) ?? _s.Screen.ForBase(e.Name);
            string mark = def == null ? "" : def.IsNew ? " +" : def.Patch.IsEmpty && def.Action == null ? "" : " ✎";
            var text = $"{KindGlyph(e.Kind)} {e.Name}{(e.ButtonId is int id ? $"  #{id}" : "")}{mark}{(def?.Patch.Visible == false ? "  (hidden)" : def?.Patch.Enabled == false ? "  (disabled)" : "")}";
            ElementList.Items.Add(new ListBoxItem { Content = text, Tag = e.Name, IsSelected = _s.Selection.Contains(e.Name), Foreground = e.Visible ? Brushes.Gainsboro : Brushes.Gray });
        }
        _refreshing = false;
    }

    static string KindGlyph(ElementKind k) => k switch
    {
        ElementKind.Button => "▭", ElementKind.Multistate => "◫", ElementKind.Toggle => "◩", ElementKind.Slider => "▬", ElementKind.Arrow => "◂",
        ElementKind.XYButton => "▦", ElementKind.Popup => "▤", ElementKind.Text => "T", ElementKind.Label => "t", ElementKind.Image => "▣",
        ElementKind.Panel => "□", ElementKind.Background => "▒", ElementKind.Screen => "⚙", ElementKind.Effect => "✦", ElementKind.Camera => "◉", _ => "·",
    };

    void SyncSelection()
    {
        RefreshElements();
        RefreshProps();
        RenderView();
    }

    void OnScreenSelected(object sender, SelectionChangedEventArgs e)
    {
        if (_refreshing || _s == null || ScreenList.SelectedItem is not ListBoxItem { Tag: string name }) return;
        _interactFocus = null;
        try
        {
            if (_s.Project.Screen(name) != null) _s.SelectScreen(name);
            else _s.OpenScreen(name);
        }
        catch (Exception ex) { MessageBox.Show(this, ex.Message, "Open screen"); }
    }

    void OnElementSelected(object sender, SelectionChangedEventArgs e)
    {
        if (_refreshing || _s == null) return;
        _s.Selection.Clear();
        foreach (ListBoxItem it in ElementList.SelectedItems) _s.Selection.Add((string)it.Tag);
        RefreshProps(); RenderView();
    }

    // ---- property panel ------------------------------------------------------------------------------
    void Header(string text) => Props.Children.Add(new TextBlock { Text = text, FontWeight = FontWeights.Bold, Margin = new Thickness(0, 10, 0, 2), Foreground = Brushes.Gold });
    void Note(string text, Brush? color = null) => Props.Children.Add(new TextBlock { Text = text, Foreground = color ?? Brushes.Gray, TextWrapping = TextWrapping.Wrap });

    void Row(string label, UIElement editor, string? tip = null)
    {
        var g = new Grid { Margin = new Thickness(0, 1, 0, 1) };
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(120) });
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        var t = new TextBlock { Text = label, VerticalAlignment = VerticalAlignment.Center, ToolTip = tip };
        g.Children.Add(t); Grid.SetColumn(editor, 1); g.Children.Add(editor);
        Props.Children.Add(g);
    }

    void Buttons(params (string text, Action action, string? tip)[] items)
    {
        var p = new WrapPanel { Margin = new Thickness(0, 3, 0, 3) };
        foreach (var (text, action, tip) in items)
        {
            var b = new Button { Content = text, Margin = new Thickness(0, 0, 4, 4), Padding = new Thickness(8, 1, 8, 1), ToolTip = tip };
            b.Click += (_, _) => Try(action);
            p.Children.Add(b);
        }
        Props.Children.Add(p);
    }

    void Field(string label, string? value, Action<string> commit, string? tip = null)
    {
        var box = new TextBox { Text = value ?? "", ToolTip = tip };
        void Do() { if (box.Text != (value ?? "")) Try(() => commit(box.Text.Trim())); }
        box.LostFocus += (_, _) => Do();
        box.KeyDown += (_, e) => { if (e.Key == Key.Enter) { Do(); e.Handled = true; } };
        Row(label, box, tip);
    }

    void Check(string label, bool value, Action<bool> commit, string? tip = null)
    {
        var c = new CheckBox { IsChecked = value, ToolTip = tip };
        c.Click += (_, _) => Try(() => commit(c.IsChecked == true));
        Row(label, c, tip);
    }

    void Combo(string label, IEnumerable<string> items, string? value, Action<string> commit, bool editable = false, string? tip = null)
    {
        var c = new ComboBox { IsEditable = editable, ToolTip = tip };
        foreach (var i in items) c.Items.Add(i);
        if (editable) c.Text = value ?? ""; else c.SelectedItem = value;
        bool ready = false;
        c.SelectionChanged += (_, _) => { if (ready && c.SelectedItem is string s && s != value) Try(() => commit(s)); };
        if (editable) c.LostFocus += (_, _) => { if (c.Text != (value ?? "") && !c.Items.Contains(c.Text)) Try(() => commit(c.Text)); };
        ready = true;
        Row(label, c, tip);
    }

    void Try(Action a)
    {
        try { a(); }
        catch (DependencyException dex) { ResolveDependencies(dex); }
        catch (Exception ex) { MessageBox.Show(this, ex.Message, "Edit"); }
    }

    static float? F(string s) => s.Length == 0 ? null : float.Parse(s, CultureInfo.InvariantCulture);
    static int? I(string s) => s.Length == 0 ? null : int.Parse(s, CultureInfo.InvariantCulture);
    static string Fs(float v) => v.ToString("0.##", CultureInfo.InvariantCulture);

    static string ActionLabel(ActionInfo a) => $"{a.Id} — {a.Title} ({a.Owner switch { ActionOwner.BuiltIn => "built in", ActionOwner.ExtraOptions => "Extra Options", _ => "not implemented yet" }})";
    static string IdOf(string label) => label.Split(' ')[0];

    static Brush ClassBrush(ElementClass c) => c switch
    {
        ElementClass.UserCreated => Brushes.LightGreen, ElementClass.NativeOptional => Brushes.LightSkyBlue,
        ElementClass.NativeRequired => Brushes.OrangeRed, _ => Brushes.Orange,
    };

    void RefreshProps()
    {
        Props.Children.Clear();
        if (_s?.Screen == null || _scene == null) return;
        var sc = _s.Screen;
        if (_s.Selection.Count != 1)
        {
            Header($"SCREEN {sc.Name}");
            Note($"{(sc.IsCustom ? "Custom screen hosted by " + Compiler.HostAi : "Retail screen " + sc.Base)}\nbase {sc.Base}  {_ws!.Data.Source(Compiler.ScenePath(sc.Base))}" +
                 $"{(Compiler.IsUnchanged(sc) ? "\nnot edited: the native page is used as is" : "")}\n{_s.Selection.Count} selected", Brushes.Silver);
            if (_s.Selection.Count > 1)
            {
                Header("MULTIPLE SELECTION");
                Combo("Style", _s.Project.Styles.Keys.Prepend(""), null, v => _s.ApplyStyle(v));
                Combo("Anchor", new[] { "none", "left", "right", "center" }, null, v => _s.Patch(_s.Selection, "Anchor", (p, _) => p.Anchor = v == "none" ? null : v));
                Buttons(("Hide", () => OnHide(this, new RoutedEventArgs()), null), ("Show", () => _s.Show(_s.Selection), null),
                        ("Disable", () => _s.SetEnabled(_s.Selection, false), null), ("Enable", () => _s.SetEnabled(_s.Selection, true), null));
            }
            return;
        }
        var egg = _scene.Find(_s.Selection[0]);
        if (egg == null) return;
        var def = sc.Element(egg.Name) ?? sc.ForBase(egg.Name);
        var name = egg.Name;
        Header($"{egg.Kind.ToString().ToUpperInvariant()}  {name}");
        Note(def?.IsNew == true ? $"new element from {def.Template}" : $"retail egg{(def?.Name != def?.Base && def != null ? " (renamed from " + def.Base + ")" : "")}");
        Note("AIs: " + string.Join(", ", egg.AiNames));
        try
        {
            var dep = _s.Dependencies(name);
            Props.Children.Add(new TextBlock { Text = DependencyReport.Label(dep.Class), Foreground = ClassBrush(dep.Class), FontWeight = FontWeights.SemiBold, Margin = new Thickness(0, 4, 0, 0) });
            foreach (var d in dep.Dependencies) Note("• " + d.Detail);
        }
        catch { }
        if (_s.EditAspectOverride && _s.Aspect != "4:3") Note($"Geometry edits apply to the {_s.Aspect} variant only", Brushes.Orange);

        Header("GEOMETRY");
        Field("X", Fs(egg.X), v => _s.Patch(new[] { name }, "X", (p, _) => p.X = F(v)), "authored units, 640x480, y up");
        Field("Y", Fs(egg.Y), v => _s.Patch(new[] { name }, "Y", (p, _) => p.Y = F(v)));
        Field("Scale X", Fs(egg.ScaleX), v => _s.Patch(new[] { name }, "Scale", (p, _) => p.ScaleX = F(v)), "en2d matrix scale: sprite, label and icon scale together in game");
        Field("Scale Y", Fs(egg.ScaleY), v => _s.Patch(new[] { name }, "Scale", (p, _) => p.ScaleY = F(v)));
        Field("Draw priority", egg.DrawPriority.ToString(), v => _s.Patch(new[] { name }, "Priority", (p, _) => p.DrawPriority = I(v)), "higher = further back (background 6, buttons 3, titles 2)");
        Combo("Anchor (wide)", new[] { "none", "left", "right", "center" }, def?.Patch.Anchor ?? "none", v => _s.Patch(new[] { name }, "Anchor", (p, _) => p.Anchor = v == "none" ? null : v),
              tip: "widescreen variants only: left/right follow that screen edge; 'none' keeps the authored 4:3 position");
        var b = ShownBounds(egg);
        Note($"bounds {b}\nhitbox {(egg.IsPrimaryFocusable ? _ws!.Layout.Hitbox(egg).ToString() : "—")}");
        int dir = WidescreenModel.MarginDirection(egg.X, egg.Y, egg.Kind == ElementKind.XYButton);
        if (dir != 0) Note($"⚠ Widescreen 'preserve margins' shifts this element {(dir > 0 ? "right" : "left")} (reference rule at {egg.X:0},{egg.Y:0}).", Brushes.Orange);

        Header("STATE");
        bool hidden = def?.Patch.Visible == false, disabled = def?.Patch.Enabled == false;
        Note(hidden ? "Hidden: not drawn, not focusable, no hitbox; its command is ignored." : disabled ? "Disabled: drawn (greyed where supported), never activated." : egg.Visible ? "Visible" : "Hidden in the base page (native state)", hidden || disabled ? Brushes.Orange : Brushes.Silver);
        Buttons(hidden ? ("Show", () => _s.Show(new[] { name }), "make the element visible again") : ("Hide", () => _s.Hide(new[] { name }), "keep the egg and its native links; reroute focus around it"),
                disabled ? ("Enable", () => _s.SetEnabled(new[] { name }, true), null) : ("Disable", () => _s.SetEnabled(new[] { name }, false), "keep it visible but never activated"));

        if (egg.UsesEn2d && egg.Model != "Null")
        {
            Header("SPRITE");
            Combo("Model", _ws!.Assets.FrontendModels(), egg.Model, v => _s.Patch(new[] { name }, "Model", (p, _) => p.Model = v), editable: true);
            Field("Image index", egg.BankIndex.ToString(), v => _s.Patch(new[] { name }, "Image", (p, _) => p.BankIndex = I(v)));
        }
        if (egg.TextAi is { } t)
        {
            bool tb = t.Name == "enUITextButtonAI";
            Header(tb ? "LABEL" : "TEXT");
            var run = _ws!.Layout.Text(egg);
            var vdef = def != null ? Compiler.Effective(_s.Project, def) : null;
            if (vdef?.ValueSource == null)
            {
                Field("Text", t.Get("Text String") is { } ts && ts != "Null" ? ts : "", v => _s.Patch(new[] { name }, "Text", (p, _) => p.Text = v), "literal text (clears Text ID / Broker key)");
                Field("Text ID", t.Get("Text ID#"), v => _s.Patch(new[] { name }, "Text ID", (p, _) => { p.TextId = I(v); p.Text = null; }), $"gaLocal group; current: {run?.Text}");
                Field("Text index", t.Get("Text ID Index#"), v => _s.Patch(new[] { name }, "Text index", (p, _) => p.TextIndex = I(v)));
                Field("Broker key", t.Get("Text*") is { } tk && tk != "Null" ? tk : "", v => _s.Patch(new[] { name }, "Text key", (p, _) => p.TextKey = v.Length == 0 ? "Null" : v));
            }
            Combo("Font", (_ws.Exe?.Fonts ?? new Dictionary<int, string>()).Select(kv => $"{kv.Key}: {kv.Value}"),
                $"{(tb ? t.GetInt("Font ID#") : t.GetInt("Font#"))}: {_ws.Layout.FontName((tb ? t.GetInt("Font ID#") : t.GetInt("Font#")) ?? 1)}",
                v => _s.Patch(new[] { name }, "Font", (p, _) => p.Font = int.Parse(v.Split(':')[0])));
            if (tb)
            {
                Field("Icon", t.Get("Icon"), v => _s.Patch(new[] { name }, "Icon", (p, _) => p.Icon = I(v)), "ButtonIcons image + 1; 0 = none");
                Field("Offset X", t.Get("Text OffsetX"), v => _s.Patch(new[] { name }, "Offset", (p, _) => p.TextOffsetX = I(v)));
                Field("Offset Y", t.Get("Text OffsetY"), v => _s.Patch(new[] { name }, "Offset", (p, _) => p.TextOffsetY = I(v)));
            }
            Combo("H justify", new[] { "0 left", "1 centre", "2 right" }, (tb ? t.Get("HJustification") : t.Get("Horizontal Justification")) is { } h ? h + (h == "0" ? " left" : h == "1" ? " centre" : " right") : null,
                v => _s.Patch(new[] { name }, "Justify", (p, _) => p.HJustify = int.Parse(v[..1])));
            Combo("V justify", new[] { "0 top", "1 middle", "2 bottom" }, (tb ? t.Get("VJustification") : t.Get("Vertical Justification")) is { } vj ? vj + (vj == "0" ? " top" : vj == "1" ? " middle" : " bottom") : null,
                v => _s.Patch(new[] { name }, "Justify", (p, _) => p.VJustify = int.Parse(v[..1])));
            if (!tb)
            {
                Header("LIVE VALUE");
                var values = ActionCatalog.Values.Select(ActionLabel).Prepend("(none — static text)").ToList();
                var cur = vdef?.ValueSource is { } vs ? values.FirstOrDefault(x => IdOf(x) == vs) ?? vs : "(none — static text)";
                Combo("Source", values, cur, v => _s.Patch(new[] { name }, "Value", (p, _) =>
                {
                    if (v.StartsWith("(none")) { p.ValueSource = null; p.ValueFormat = null; p.ValueFallback = null; return; }
                    p.ValueSource = IdOf(v); p.ValueFormat ??= "{value}"; p.ValueFallback ??= "N/A";
                }), editable: true, tip: "the runtime writes the current game value into this text; IDs of other modules can be typed");
                if (vdef?.ValueSource != null)
                {
                    Field("Format", vdef.ValueFormat ?? "{value}", v => _s.Patch(new[] { name }, "Value format", (p, _) => p.ValueFormat = v), "{value} is replaced, e.g. MODEL: {value}");
                    Field("Unavailable", vdef.ValueFallback ?? "N/A", v => _s.Patch(new[] { name }, "Value fallback", (p, _) => p.ValueFallback = v), "shown for {value} while the provider is missing");
                    var info = ActionCatalog.Find(vdef.ValueSource);
                    Note(info == null ? "provided by another module (MRMenuRegisterValueV1); until then the fallback is shown" :
                         info.Owner == ActionOwner.Planned ? "no provider yet: the game shows the fallback text" :
                         info.Owner == ActionOwner.ExtraOptions ? "provided by Extra Options (fallback with the standalone runtime)" : "provided by the Menu Builder runtime",
                         info?.Owner == ActionOwner.Planned || info == null ? Brushes.Orange : Brushes.LightGreen);
                }
            }
        }
        {
            // Dynamic visibility (runtime 1.2): shown only while the value ID has an answer for the current state.
            Header("VISIBLE WHEN");
            var vdyn = def != null ? Compiler.Effective(_s.Project, def) : null;
            var choices = ActionCatalog.Values.Select(ActionLabel).Prepend("(always)").ToList();
            var current = vdyn?.VisibleWhen is { } vw ? choices.FirstOrDefault(x => IdOf(x) == vw) ?? vw : "(always)";
            Combo("Value ID", choices, current, v => _s.Patch(new[] { name }, "Visible when", (p, _) => p.VisibleWhen = v.StartsWith("(always") ? null : IdOf(v)),
                editable: true, tip: "the row (button + texts with the same ID) is hidden while this value is unavailable; Up/Down skip it");
        }
        if (egg.Focusable is { } f && egg.IsPrimaryFocusable)
        {
            Header("FOCUS & NAVIGATION");
            Field("Button ID", f.Get("Button ID"), v => _s.Patch(new[] { name }, "Button ID", (p, _) => p.ButtonId = I(v)), "native command / focus ID");
            var ids = _scene.Focusables.Select(x => $"{x.ButtonId}: {x.Name}").Prepend("0: none").ToList();
            string Cur(string path) => ids.FirstOrDefault(x => x.StartsWith((f.GetInt(path) ?? 0) + ":")) ?? "0: none";
            foreach (var (label, path) in new[] { ("Up", "Up Path"), ("Down", "Down Path"), ("Left", "Left Path"), ("Right", "Right Path") })
                if (f.Has(path))
                    Combo(label, ids, Cur(path), v => _s.Patch(new[] { name }, label + " path", (p, _) =>
                    {
                        int id = int.Parse(v.Split(':')[0]);
                        switch (label) { case "Up": p.Up = id; break; case "Down": p.Down = id; break; case "Left": p.Left = id; break; default: p.Right = id; break; }
                    }));
            Header("ACTION");
            var cb = _compiled?.Screens.FirstOrDefault(x => x.Name == sc.Name)?.Buttons.FirstOrDefault(x => x.Egg == name);
            Note($"status: {cb?.Status.ToString() ?? "?"}{(cb?.Blocked == true ? " (blocked)" : "")}", cb?.Status is BindingStatus.Unbound ? Brushes.OrangeRed : Brushes.LightGreen);
            var action = def?.Action;
            Combo("Type", ActionBinding.Types.Prepend("(retail native)"), action?.Type ?? "(retail native)", v =>
                _s.SetAction(name, v == "(retail native)" ? null : new ActionBinding { Type = v, Command = v == ActionBinding.Native ? egg.ButtonId : null }));
            if (action != null)
            {
                var screens = (_ws!.Exe?.Screens ?? new List<string>()).Distinct().Concat(_s.Project.Screens.Where(x => x.IsCustom).Select(x => x.Name)).OrderBy(x => x).ToList();
                ActionBinding Copy() => action.Clone();
                if (action.Type is ActionBinding.Navigate or ActionBinding.Forward)
                    Combo("Screen", screens, action.Screen, v => { var a = Copy(); a.Screen = v; _s.SetAction(name, a); });
                if (action.Type is ActionBinding.Native or ActionBinding.Forward)
                    Field("Command", action.Command?.ToString(), v => { var a = Copy(); a.Command = I(v); _s.SetAction(name, a); });
                if (action.Type is ActionBinding.SetInt or ActionBinding.ToggleBool or ActionBinding.CycleInt)
                    Field("Broker key", action.Key, v => { var a = Copy(); a.Key = v; _s.SetAction(name, a); });
                if (action.Type == ActionBinding.SetInt) Field("Value", action.Value?.ToString(), v => { var a = Copy(); a.Value = I(v); _s.SetAction(name, a); });
                if (action.Type == ActionBinding.CycleInt)
                {
                    Field("Min", action.Min?.ToString(), v => { var a = Copy(); a.Min = I(v); _s.SetAction(name, a); });
                    Field("Max", action.Max?.ToString(), v => { var a = Copy(); a.Max = I(v); _s.SetAction(name, a); });
                    Field("Step", action.Step?.ToString(), v => { var a = Copy(); a.Step = I(v); _s.SetAction(name, a); });
                }
                if (action.Type == ActionBinding.Ext)
                {
                    var labels = ActionCatalog.Actions.Select(ActionLabel).ToList();
                    var info = ActionCatalog.Find(action.Extension);
                    Combo("Game action", labels, info != null ? ActionLabel(info) : action.Extension, v => { var a = Copy(); a.Extension = IdOf(v); _s.SetAction(name, a); },
                          editable: true, tip: "typed action ID; IDs registered by other modules can be typed (lower-case dotted name)");
                    Field("Args", action.Args, v => { var a = Copy(); a.Args = v.Length == 0 ? null : v; _s.SetAction(name, a); }, info?.Args);
                    Check("Required", action.Optional == false, v => { var a = Copy(); a.Optional = v ? false : null; _s.SetAction(name, a); },
                          "required: a missing handler blocks installation; optional: the button is served disabled until a handler exists");
                    Note(info == null ? "Must be registered by another module (MRMenuRegisterActionV1); until then the button is served disabled." :
                         info.Owner == ActionOwner.Planned ? $"{info.Title}: not implemented yet — the game shows this button disabled." :
                         info.Owner == ActionOwner.ExtraOptions ? $"{info.Description} Disabled when Extra Options is not active." : info.Description,
                         info == null || info.Owner == ActionOwner.Planned ? Brushes.Orange : Brushes.Silver);
                }
            }
        }
        Header("STYLE");
        Combo("Style", _s.Project.Styles.Keys.Prepend(""), def?.Style ?? "", v => _s.ApplyStyle(v));
        Field("Note", def?.Note, v => _s.Edit("Note", () => _s.Def(name).Note = v.Length == 0 ? null : v));
    }

    // ---- validation / findings ----------------------------------------------------------------------------
    void RunValidation()
    {
        if (_s == null || _ws == null) return;
        try { (_compiled, _findings) = _ws.Build(_s.Project); }
        catch (Exception ex) { _findings = new() { new Finding(Severity.Error, "*", null, "BUILD", ex.Message) }; }
        FindingsList.Items.Clear();
        foreach (var f in _findings.Where(f => f.Severity != Severity.Info || InfoBox.IsChecked == true).OrderByDescending(f => f.Severity))
            FindingsList.Items.Add(new ListBoxItem
            {
                Content = f.ToString(), Tag = f,
                Foreground = f.Severity == Severity.Error ? Brushes.OrangeRed : f.Severity == Severity.Warning ? Brushes.Gold : Brushes.LightGray,
            });
        int e = _findings.Count(x => x.Severity == Severity.Error), w = _findings.Count(x => x.Severity == Severity.Warning);
        FindingsTitle.Text = $"VALIDATION  {e} errors (block installation), {w} warnings";
        RefreshProps();
    }

    void OnInfoToggled(object sender, RoutedEventArgs e) { if (IsLoaded) RunValidation(); }

    void OnFindingActivated(object sender, MouseButtonEventArgs e)
    {
        if (FindingsList.SelectedItem is not ListBoxItem { Tag: Finding f } || _s == null) return;
        if (_s.Project.Screen(f.Screen) != null && _s.Screen?.Name != f.Screen) _s.SelectScreen(f.Screen);
        if (f.Aspect != null && AspectBox.Items.Contains(f.Aspect)) AspectBox.SelectedItem = f.Aspect;
        if (f.Element != null) { _s.Selection.Clear(); _s.Selection.AddRange(f.Element.Split(',').Where(n => _scene?.Find(n) != null)); SyncSelection(); }
    }

    void OnQuickFix(object sender, RoutedEventArgs e)
    {
        if (FindingsList.SelectedItem is not ListBoxItem { Tag: Finding f } || _s == null || f.Code != "WS_MARGIN_RULE" || f.Element == null) { Status("Select a WS_MARGIN_RULE finding"); return; }
        if (_s.Screen?.Name != f.Screen) _s.SelectScreen(f.Screen);
        Try(() => Status(_s.FixMargin(f.Element)));
    }

    // ---- keyboard ------------------------------------------------------------------------------------------------
    void OnKeyDown(object sender, KeyEventArgs e)
    {
        if (_s == null || e.OriginalSource is TextBox || e.OriginalSource is ComboBox) return;
        bool ctrl = Keyboard.Modifiers.HasFlag(ModifierKeys.Control), shift = Keyboard.Modifiers.HasFlag(ModifierKeys.Shift);
        if (InteractBox.IsChecked == true && !ctrl)
        {
            var cur = _scene?.Focusables.FirstOrDefault(x => x.ButtonId == (_interactFocus ?? FirstFocus()));
            string? path = e.Key switch { Key.Up => "Up Path", Key.Down => "Down Path", Key.Left => "Left Path", Key.Right => "Right Path", _ => null };
            if (path != null && cur?.Focusable?.GetInt(path) is int t && t != 0) { _interactFocus = t; RenderView(); Status($"focus #{t}"); e.Handled = true; return; }
            if (e.Key == Key.Enter && cur != null) { ReportAction(cur); e.Handled = true; return; }
            if (e.Key == Key.Escape) { Status("Back: " + (_s.Screen!.Back?.ToString() ?? (_s.Screen.IsCustom ? "← back" : "native"))); e.Handled = true; return; }
        }
        if (ctrl && e.Key == Key.Z) { _s.Undo(); e.Handled = true; }
        else if (ctrl && e.Key == Key.Y) { _s.Redo(); e.Handled = true; }
        else if (ctrl && shift && e.Key == Key.S) { SaveProject(true); e.Handled = true; }
        else if (ctrl && e.Key == Key.S) { SaveProject(false); e.Handled = true; }
        else if (ctrl && e.Key == Key.C) { OnCopy(this, e); e.Handled = true; }
        else if (ctrl && e.Key == Key.V) { OnPaste(this, e); e.Handled = true; }
        else if (ctrl && e.Key == Key.D) { OnDuplicate(this, e); e.Handled = true; }
        else if (ctrl && e.Key == Key.H) { OnHide(this, e); e.Handled = true; }
        else if (ctrl && e.Key == Key.OemCloseBrackets) { _s.ZOrder(-1); e.Handled = true; }
        else if (ctrl && e.Key == Key.OemOpenBrackets) { _s.ZOrder(1); e.Handled = true; }
        else if (e.Key == Key.Delete) { OnDelete(this, e); e.Handled = true; }
        else if (e.Key == Key.F2) { OnRename(this, e); e.Handled = true; }
        else if (e.Key == Key.F5) { OnReloadResources(this, e); e.Handled = true; }
        else if (e.Key == Key.F7) { OnValidate(this, e); e.Handled = true; }
        else if (e.Key == Key.F8) { OnInstall(this, e); e.Handled = true; }
        else if (_s.Selection.Count > 0 && e.Key is Key.Left or Key.Right or Key.Up or Key.Down)
        {
            double step = shift ? 10 : 1;
            double dx = e.Key == Key.Left ? -step : e.Key == Key.Right ? step : 0, dy = e.Key == Key.Up ? step : e.Key == Key.Down ? -step : 0;
            _s.Move(_s.Selection, dx, dy, 0);
            e.Handled = true;
        }
    }

    // ---- menu handlers -----------------------------------------------------------------------------
    void Status(string s) => StatusText.Text = s;

    void OnNewProject(object sender, RoutedEventArgs e)
    {
        if (!ConfirmLoseChanges("create a new project")) return;
        var n = Dialogs.Prompt(this, "New project", "Project / layout name (letters, digits, '-' and '_'):", "MyMenus");
        while (n != null && LayoutName.Problem(n) is { } problem)
            n = Dialogs.Prompt(this, "New project", $"{problem}.\nProject / layout name:", LayoutName.Suggest(n));
        if (n != null) NewProject(n);
    }

    void OnOpenProject(object sender, RoutedEventArgs e)
    {
        if (!ConfirmLoseChanges("open another project")) return;
        var d = new OpenFileDialog { Filter = "Menu Builder project (*.mrmenu.json)|*.mrmenu.json|JSON|*.json" };
        if (d.ShowDialog(this) == true) OpenProject(d.FileName);
    }

    void OnCloseProject(object sender, RoutedEventArgs e)
    {
        if (!ConfirmLoseChanges("close the project")) return;
        _settings.LastProject = null; _settings.Save();
        NewProject("Untitled", saved: true);
        Status("Project closed");
    }

    void OnSave(object sender, RoutedEventArgs e) => SaveProject(false);
    void OnSaveAs(object sender, RoutedEventArgs e) => SaveProject(true);

    void OnClosing(object? sender, System.ComponentModel.CancelEventArgs e) { if (!Testing && !ConfirmLoseChanges("exit")) e.Cancel = true; }
    void OnExit(object sender, RoutedEventArgs e) => Close();

    /// <summary>Another game folder: the project, its unsaved edits and the undo history stay; resources are re-bound.</summary>
    void OnGameFolder(object sender, RoutedEventArgs e)
    {
        if (ChooseGameFolder() is not { } root) return;
        OpenWorkspace(root);
    }

    void OnReloadResources(object sender, RoutedEventArgs e)
    {
        if (_ws == null) return;
        if (OpenWorkspace(_ws.Data.Root)) Status("Game resources reloaded (pages, models, fonts); project and history kept");
    }

    void OnImportScreen(object sender, RoutedEventArgs e)
    {
        var d = new OpenFileDialog { Filter = "Screen (*.mrscreen.json)|*.mrscreen.json|JSON|*.json" };
        if (d.ShowDialog(this) != true) return;
        Try(() =>
        {
            var p = _s!.Project.Clone();
            var s = Workspace.ImportScreen(p, File.ReadAllText(d.FileName));
            _s.ReplaceProject(p); _s.SelectScreen(s.Name);
        });
    }

    void OnExportScreen(object sender, RoutedEventArgs e)
    {
        var d = new SaveFileDialog { Filter = "Screen (*.mrscreen.json)|*.mrscreen.json", FileName = _s!.Screen!.Name + ".mrscreen.json" };
        if (d.ShowDialog(this) == true) Try(() => { File.WriteAllText(d.FileName, Workspace.ExportScreen(_s.Project, _s.Screen.Name)); Status("Exported " + d.FileName); });
    }

    void OnExportPng(object sender, RoutedEventArgs e)
    {
        if (_canvas == null) return;
        var d = new SaveFileDialog { Filter = "PNG|*.png", FileName = $"{_s!.Screen!.Name}-{AspectKey().Replace(':', 'x')}.png" };
        if (d.ShowDialog(this) == true) Png.Save(d.FileName, _canvas.Px, _canvas.W, _canvas.H);
    }

    void OnUndo(object sender, RoutedEventArgs e) => _s?.Undo();
    void OnRedo(object sender, RoutedEventArgs e) => _s?.Redo();
    void OnCopy(object sender, RoutedEventArgs e) { if (_s?.Selection.Count > 0) { _clipboard = _s.Copy(_s.Selection); try { Clipboard.SetText(_clipboard); } catch { } Status($"copied {_s.Selection.Count}"); } }
    void OnPaste(object sender, RoutedEventArgs e)
    {
        string? text = null;
        try { text = Clipboard.ContainsText() ? Clipboard.GetText() : null; } catch { }
        text ??= _clipboard;
        if (text == null || _s == null) return;
        Try(() => _s.Paste(text, 10, -10));
    }
    void OnDuplicate(object sender, RoutedEventArgs e) { if (_s?.Selection.Count > 0) Try(() => _s.Duplicate(_s.Selection, 10, -10)); }

    void OnDelete(object sender, RoutedEventArgs e)
    {
        if (_s?.Selection.Count > 0) Try(() => _s.Delete(_s.Selection));
    }

    void OnHide(object sender, RoutedEventArgs e) { if (_s?.Selection.Count > 0) Try(() => _s.Hide(_s.Selection)); }
    void OnShow(object sender, RoutedEventArgs e) { if (_s?.Selection.Count > 0) Try(() => _s.Show(_s.Selection)); }
    void OnDisable(object sender, RoutedEventArgs e) { if (_s?.Selection.Count > 0) Try(() => _s.SetEnabled(_s.Selection, false)); }
    void OnEnable(object sender, RoutedEventArgs e) { if (_s?.Selection.Count > 0) Try(() => _s.SetEnabled(_s.Selection, true)); }

    void OnDependencies(object sender, RoutedEventArgs e)
    {
        if (_s?.Selection.Count > 0)
            Dialogs.Choice(this, "Native dependencies", $"{_s.Selection.Count} element(s) on {_s.Screen!.Name}",
                string.Join(Environment.NewLine + Environment.NewLine, _s.Selection.Select(n => _s.Dependencies(n).Summary)), "OK");
    }

    /// <summary>A blocked delete/rename: show what depends on the elements and offer the safe alternatives.</summary>
    void ResolveDependencies(DependencyException dex)
    {
        var names = dex.Reports.Select(r => r.Element).ToList();
        bool canHide = dex.Reports.All(r => r.CanHide);
        var details = string.Join(Environment.NewLine + Environment.NewLine, dex.Reports.Select(r => r.Summary));
        bool delete = dex.Message.StartsWith("Delete");
        var choices = new List<string>();
        if (canHide) { choices.Add("Hide instead"); choices.Add("Disable instead"); }
        choices.Add(delete ? "Delete anyway" : "Rename anyway");
        choices.Add("Cancel");
        int c = Dialogs.Choice(this, delete ? "Delete" : "Rename",
            $"{string.Join(", ", names)} {(names.Count == 1 ? "has" : "have")} native dependencies. {(delete ? "Deleting" : "Renaming")} can break the screen even if it still looks right.",
            details, choices.ToArray());
        if (c < 0 || choices[c] == "Cancel") return;
        try
        {
            switch (choices[c])
            {
                case "Hide instead": _s!.Hide(names); break;
                case "Disable instead": _s!.SetEnabled(names, false); break;
                case "Delete anyway":
                    if (MessageBox.Show(this, "Delete anyway? Native code may still look these elements up.", "Delete", MessageBoxButton.YesNo, MessageBoxImage.Warning) == MessageBoxResult.Yes)
                        _s!.Delete(names, force: true);
                    break;
                case "Rename anyway":
                    if (_pendingRename is var (old, n) && MessageBox.Show(this, "Rename anyway? Native code may look this element up by its old name.", "Rename", MessageBoxButton.YesNo, MessageBoxImage.Warning) == MessageBoxResult.Yes)
                        _s!.Rename(old, n, force: true);
                    break;
            }
        }
        catch (Exception ex) { MessageBox.Show(this, ex.Message, "Edit"); }
    }
    (string old, string name)? _pendingRename;

    void OnRename(object sender, RoutedEventArgs e)
    {
        if (_s?.Selection.Count != 1) return;
        var old = _s.Selection[0];
        var n = Dialogs.Prompt(this, "Rename", "New element name (letters, digits, '_'):", old);
        if (n == null || n == old) return;
        _pendingRename = (old, n);
        Try(() => _s.Rename(old, n));
    }

    void OnApplyStyle(object sender, RoutedEventArgs e)
    {
        var s = Dialogs.Pick(this, "Apply style", "Style:", _s!.Project.Styles.Keys.Prepend("(none)"));
        if (s != null) _s.ApplyStyle(s == "(none)" ? "" : s);
    }
    void OnStyleFromSelection(object sender, RoutedEventArgs e) { var n = Dialogs.Prompt(this, "New style", "Style name:"); if (n?.Length > 0) _s!.StyleFromSelection(n); }
    void OnComponentFromSelection(object sender, RoutedEventArgs e) { var n = Dialogs.Prompt(this, "New component", "Component name:"); if (n?.Length > 0) { _s!.ComponentFromSelection(n); BuildInsertMenu(); } }

    void BuildInsertMenu()
    {
        InsertMenu.Items.Clear();
        foreach (var (label, template) in Builtins)
        {
            var m = new MenuItem { Header = label, Tag = template, Foreground = Brushes.Black };
            m.Click += OnInsert;
            InsertMenu.Items.Add(m);
        }
        if (_s?.Project.Components.Count > 0)
        {
            InsertMenu.Items.Add(new Separator());
            foreach (var c in _s.Project.Components.Keys)
            {
                var m = new MenuItem { Header = "Component: " + c, Tag = "component:" + c, Foreground = Brushes.Black };
                m.Click += OnInsert;
                InsertMenu.Items.Add(m);
            }
        }
    }

    void OnInsert(object sender, RoutedEventArgs e)
    {
        if (_s?.Screen == null || sender is not MenuItem { Tag: string template }) return;
        Try(() =>
        {
            var stem = "MB_" + (template.StartsWith("component:") ? template[10..] : template[(template.IndexOf('/') + 1)..]);
            string? text = template.Contains("Button") || template.EndsWith("OnePlayer") || template.EndsWith("VehicleSetup") || template.EndsWith("SelectCar") ? "NEW BUTTON" : null;
            var added = _s.Add(template, stem, 260, 240, text: text);
            Status($"Added {added}; set its action in the properties panel");
        });
    }

    void OnAlign(object sender, RoutedEventArgs e) => _s?.Align((string)((MenuItem)sender).Tag);
    void OnDistribute(object sender, RoutedEventArgs e) => _s?.DistributeVertical();
    void OnBringForward(object sender, RoutedEventArgs e) => _s?.ZOrder(-1);
    void OnSendBackward(object sender, RoutedEventArgs e) => _s?.ZOrder(1);
    void OnAutoLink(object sender, RoutedEventArgs e) => _s?.AutoLinkVertical();

    void OnAddRetailScreen(object sender, RoutedEventArgs e)
    {
        var have = _s!.Project.Screens.Where(s => !Compiler.IsUnchanged(s)).Select(s => s.Base).ToHashSet(StringComparer.OrdinalIgnoreCase);
        var pick = Dialogs.Pick(this, "Open frontend screen", "Native frontend screens of this installation:", _ws!.RetailScreens().Where(r => !have.Contains(r.name)).Select(r => $"{r.name}  ({r.source})"));
        if (pick != null) Try(() => _s.OpenScreen(pick.Split(' ')[0]));
    }

    void OnAddCustomScreen(object sender, RoutedEventArgs e)
    {
        var r = Dialogs.Form(this, "New custom screen", ("Name (letters/digits):", "MyScreen"), ("Title:", "MY SCREEN"), ("Visual base (retail screen; its controller is replaced by the host AI):", Compiler.HostScreen));
        if (r == null || r[0].Length == 0) return;
        Try(() =>
        {
            if (_s!.Project.Screen(r[0]) != null || !Ids.IsScreenName(r[0])) throw new ArgumentException("the name exists or is invalid (letters and digits, first a letter, at most 32)");
            _s.AddScreen(_ws!.NewCustomScreen(r[0], r[1], r[2]));
        });
    }

    void OnScreenSettings(object sender, RoutedEventArgs e)
    {
        var sc = _s!.Screen!;
        var r = Dialogs.Form(this, "Screen settings", ("Default focus (Button ID, empty = native):", sc.DefaultFocus?.ToString() ?? ""), ("Title (custom screens):", sc.Title ?? ""),
            ("Back action: native | navigate.back | navigate.screen:<Screen>", sc.Back == null ? "native" : sc.Back.Type == ActionBinding.Navigate ? "navigate.screen:" + sc.Back.Screen : sc.Back.Type));
        if (r == null) return;
        Try(() => _s.Edit("Screen settings", () =>
        {
            sc.DefaultFocus = I(r[0]);
            sc.Title = r[1].Length == 0 ? null : r[1];
            sc.Back = r[2] == "native" ? null : r[2].StartsWith("navigate.screen:") ? new ActionBinding { Type = ActionBinding.Navigate, Screen = r[2][16..] } : new ActionBinding { Type = r[2] };
        }));
    }

    void OnRemoveScreen(object sender, RoutedEventArgs e)
    {
        if (_s?.Screen != null && MessageBox.Show(this, $"Remove {_s.Screen.Name} and all its edits from the project?", "Remove screen", MessageBoxButton.YesNo) == MessageBoxResult.Yes)
            _s.RemoveScreen(_s.Screen.Name);
    }

    void OnValidate(object sender, RoutedEventArgs e) { RunValidation(); Status("Validated"); }

    void OnInstall(object sender, RoutedEventArgs e)
    {
        if (_s == null || _ws == null) return;
        if (LayoutName.Problem(_s.Project.Name) is { } problem)
        {
            var n = Dialogs.Prompt(this, "Layout name", $"The project name '{_s.Project.Name}' cannot be a layout name: {problem}.\nNew project / layout name:", LayoutName.Suggest(_s.Project.Name));
            if (n == null || !LayoutName.IsValid(n)) return;
            _s.Edit("Rename project", () => _s.Project.Name = n);
        }
        _s.Project.Id ??= MenuProject.NewId();
        var res = _ws.Install(_s.Project);
        if (res.NameTaken &&
            Dialogs.Choice(this, "Layout name in use", res.Message, null, "Replace that layout", "Cancel") == 0)
            res = _ws.Install(_s.Project, new Installer.Options { ReplaceForeign = true });
        RunValidation();
        bool runtime = File.Exists(System.IO.Path.Combine(_ws.Data.Root, "dinput8.dll"));
        var errors = res.Findings.Where(f => f.Severity == Severity.Error).ToList();
        var details = errors.Count > 0 ? string.Join(Environment.NewLine, errors.Select(f => f.ToString())) : res.Ok && !runtime ? "dinput8.dll with the Menu Builder runtime is not in the game folder; the layout is installed but the game will show the Classic menus." : null;
        Status($"{res.Title}: {res.Message}");
        Dialogs.Choice(this, res.Title, res.Message, details, "OK");
    }

    void OnClassic(object sender, RoutedEventArgs e)
    {
        Try(() => { Installer.SetActive(_ws!.Data.Root, null); Status("Classic frontend selected (layouts stay installed)"); });
    }

    void OnLaunch(object sender, RoutedEventArgs e)
    {
        var exe = System.IO.Path.Combine(_ws!.Data.Root, "MRallye.exe");
        Try(() => Process.Start(new ProcessStartInfo(exe) { WorkingDirectory = _ws.Data.Root, UseShellExecute = true }));
    }

    void OnLoadLive(object sender, RoutedEventArgs e)
    {
        var file = System.IO.Path.Combine(_ws!.Data.Root, Installer.Folder, "live", CurrentSceneName() + ".txt");
        if (!File.Exists(file)) { MessageBox.Show(this, $"No live dump for {CurrentSceneName()} yet. Open the screen in game (LiveDump=1)."); return; }
        _live = new(); _liveScene = CurrentSceneName();
        int match = 0, total = 0;
        string variant = "4:3";
        foreach (var line in File.ReadAllLines(file))
        {
            var t = line.Split('\t');
            if (t[0] == "variant") variant = t[1];
            if (t[0] != "button" || t.Length < 6 || t[3] != "live") continue;
            var hit = t[5].Replace("hit=", "").Split(',').Select(v => double.Parse(v, CultureInfo.InvariantCulture)).ToArray();
            int id = int.Parse(t[1]);
            var rect = new UiRect(hit[0], hit[1], hit[2], hit[3]);
            _live[id] = (t[2], rect);
            total++;
            var egg = _scene?.Find(t[2]);
            if (egg != null) { var mine = _ws.Layout.Hitbox(egg).Offset(Shift(egg), 0); if (Math.Abs(mine.X0 - rect.X0) < 0.6 && Math.Abs(mine.Y0 - rect.Y0) < 0.6 && Math.Abs(mine.X1 - rect.X1) < 0.6 && Math.Abs(mine.Y1 - rect.Y1) < 0.6) match++; }
        }
        DrawOverlay();
        Status($"Live dump {file} (game variant {variant}): {match}/{total} hitboxes identical to the editor (cyan = in-game)");
    }

    // ---- self-test (MenuBuilder.exe --game DIR --project P --selftest OUTDIR) ------------------------------------
    // Drives the real handlers (pointer down/move/up with modifiers, game-folder rebind, undo) and saves window
    // snapshots plus a log; used by tools/menu-builder/test/run_editor_selftest.ps1. Never prompts, never saves.
    void Snap(string dir, string name)
    {
        UpdateLayout();
        var w = (int)ActualWidth; var h = (int)ActualHeight;
        var rtb = new RenderTargetBitmap(w, h, 96, 96, PixelFormats.Pbgra32);
        rtb.Render(this);
        var enc = new PngBitmapEncoder(); enc.Frames.Add(BitmapFrame.Create(rtb));
        using var f = File.Create(System.IO.Path.Combine(dir, name + ".png"));
        enc.Save(f);
    }

    Point PixelOf(double ux, double uy) { var p = _canvas!.ToPixel(ux, uy); return new Point(p.x, p.y); }

    async void SelfTest(string dir)
    {
        Directory.CreateDirectory(dir);
        var log = new List<string>();
        int pass = 0, fail = 0;
        void T(bool ok, string what) { if (ok) pass++; else fail++; log.Add($"{(ok ? "PASS" : "FAIL")} {what}"); }
        async Task Idle() => await Dispatcher.InvokeAsync(() => { }, System.Windows.Threading.DispatcherPriority.ApplicationIdle);
        try
        {
            Width = 1600; Height = 1000; await Idle();
            T(ScreenList.Items.Count > 40, $"screen list offers every frontend screen ({ScreenList.Items.Count} rows)");
            _s!.OpenScreen("VehicleConfig"); await Idle();
            _s.Selection.Clear(); _s.Selection.Add("VC_Model"); SyncSelection(); await Idle();
            Snap(dir, "01-selected");
            var egg = _scene!.Find("VC_Model")!;
            var box = SelectionBounds(_scene);
            float x0 = egg.X, sx0 = egg.ScaleX;

            // Move with smart guides: drag so the left edge lands 3 units right of the neighbour column → snaps back.
            var start = PixelOf((box.X0 + box.X1) / 2, (box.Y0 + box.Y1) / 2);
            PointerDown(start, null);
            PointerMove(new Point(start.X + 3 * _canvas!.W / _canvas.VirtualWidth, start.Y + 46 * _canvas.H / 480.0));
            await Idle();
            T(_guides.Count > 0 && Math.Abs(_dragDx - 3) > 1e-6 && _guides.Any(g => g.Vertical), $"move snaps to a neighbour line (proposed dx 3 → {_dragDx:0.##}, guides {_guides.Count})");
            Snap(dir, "02-move-guides");
            PointerMove(new Point(start.X + 120 * _canvas.W / _canvas.VirtualWidth, start.Y));
            await Idle();
            Snap(dir, "03-move-live");
            PointerUp(); await Idle();
            T(Math.Abs(_scene!.Find("VC_Model")!.X - (x0 + _dragDxCommitted)) < 0.6 && _s.Dirty, $"move committed ({_scene.Find("VC_Model")!.X:0.##})");
            _s.Undo(); await Idle();
            T(Math.Abs(_scene!.Find("VC_Model")!.X - x0) < 0.01, "undo restores the position");

            // Live resize from the right edge handle (3): left edge stays fixed.
            _s.Selection.Clear(); _s.Selection.Add("VC_Model"); SyncSelection(); await Idle();
            box = SelectionBounds(_scene!);
            var handle = Overlay.Children.OfType<Rectangle>().First(r => (r.Tag as string) == "h3");
            var hp = PixelOf(box.X1, (box.Y0 + box.Y1) / 2);
            PointerDown(hp, handle);
            PointerMove(new Point(hp.X - 60 * _canvas.W / _canvas.VirtualWidth, hp.Y));
            await Idle();
            var live = DraggedBox();
            T(_drag == DragKind.Scale && Math.Abs(live.X0 - box.X0) < 0.01 && live.Width < box.Width - 50, $"live resize keeps the left edge (box {live})");
            Snap(dir, "04-resize-live");
            PointerUp(); await Idle();
            var after = _scene!.Find("VC_Model")!;
            var nb = _ws!.Layout.Bounds(after);
            T(after.ScaleX < sx0 && Math.Abs(nb.X0 - box.X0) < 0.6, $"resize committed (scale {after.ScaleX:0.###}, left {nb.X0:0.##} vs {box.X0:0.##})");
            Snap(dir, "05-resized");

            // Corner + Shift keeps proportions.
            box = SelectionBounds(_scene);
            handle = Overlay.Children.OfType<Rectangle>().First(r => (r.Tag as string) == "h4");
            hp = PixelOf(box.X1, box.Y0);
            _testMods = ModifierKeys.Shift;
            PointerDown(hp, handle);
            PointerMove(new Point(hp.X + 40 * _canvas.W / _canvas.VirtualWidth, hp.Y + 5));
            T(Math.Abs(_kx - _ky) < 1e-9, "Shift + corner = proportional");
            PointerUp(); _testMods = null; await Idle();

            // Game folder change keeps project, dirty flag and history.
            var dirty = _s.Dirty; var path = _s.Path; var canUndo = _s.CanUndo;
            OpenWorkspace(_ws!.Data.Root); await Idle();
            T(_s.Dirty == dirty && _s.Path == path && _s.CanUndo == canUndo && Title.Contains('*') == dirty, "game folder change keeps dirty state, path and undo");
            _s.Undo(); _s.Undo(); await Idle();
            T(!_s.Dirty, "undo after the folder change returns to the saved state");

            // 16:9 centred preview of the same screen.
            ModeBox.SelectedIndex = 1; AspectBox.SelectedItem = "16:9"; await Idle();
            Snap(dir, "06-vc-16x9-centered");
            ModeBox.SelectedIndex = 0; AspectBox.SelectedItem = "4:3"; await Idle();

            // Blocked delete of a native element shows dependencies instead of deleting.
            _s.OpenScreen("MainMenu"); await Idle();
            var json = _s.Project.ToJson();
            bool blocked = false;
            try { _s.Delete(new[] { "Quit" }); } catch (DependencyException) { blocked = true; }
            T(blocked && _s.Project.ToJson() == json, "delete of retail Quit is blocked");
            _s.Selection.Clear(); _s.Selection.Add("Quit"); SyncSelection(); await Idle();
            Snap(dir, "07-native-required-props");
        }
        catch (Exception ex) { fail++; log.Add("FAIL exception " + ex); }
        log.Add($"RESULT pass={pass} fail={fail}");
        File.WriteAllLines(System.IO.Path.Combine(dir, "selftest.log"), log);
        Application.Current.Shutdown(fail == 0 ? 0 : 1);
    }

    void OnAbout(object sender, RoutedEventArgs e) => MessageBox.Show(this,
        $"Master Rallye Menu Builder {Installer.BuilderVersion}\n\nWYSIWYG editor of the native frontend scenes (DataScene/FrontendScreens).\n" +
        "Projects are declarative deltas over the installed pages; the dinput8 runtime serves compiled layouts to the real frontend.\n\n" +
        "Mouse: drag to move (smart guides snap to neighbours and the screen; Shift = axis lock, Alt = no snapping),\n" +
        "8 handles to resize live (Shift = keep proportions, Alt = from centre).\n\n" +
        "Command line / machine API: mrmenu.exe (JSON). Python: tools/menu-builder/python/mr_menu_builder.py.\nDocumentation: docs/menu-builder.md", "About");
}
