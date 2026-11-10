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
    public string? GameRoot { get; set; }
    public string? LastProject { get; set; }
    static string File_ => System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "MRMenuBuilder", "settings.json");
    public static AppSettings Load() { try { return JsonSerializer.Deserialize<AppSettings>(File.ReadAllText(File_)) ?? new(); } catch { return new(); } }
    public void Save() { Directory.CreateDirectory(System.IO.Path.GetDirectoryName(File_)!); File.WriteAllText(File_, JsonSerializer.Serialize(this)); }
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
    // drag state
    enum DragKind { None, Move, Scale }
    DragKind _drag;
    Point _dragStart;
    double _dragDx, _dragDy;
    UiRect _dragRect;
    double _dragScaleX, _dragScaleY;
    string? _clipboard;

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
        ("Value text (Broker)", "QuickRace/ModeText"),
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
        Loaded += (_, _) => Startup();
    }

    // ---- startup / project --------------------------------------------------------------------
    void Startup()
    {
        var root = _settings.GameRoot;
        if (root == null || !File.Exists(System.IO.Path.Combine(root, "Data.sma")))
        {
            MessageBox.Show(this, "Select the Master Rallye game folder (the one with MRallye.exe and Data.sma). The editor only reads it; layouts are installed into <game>\\MenuBuilder.", "Menu Builder");
            if (!ChooseGameFolder()) { Close(); return; }
        }
        OpenWorkspace(_settings.GameRoot!);
        if (_settings.LastProject != null && File.Exists(_settings.LastProject)) OpenProject(_settings.LastProject);
        else NewProject("MyMenus");
    }

    bool ChooseGameFolder()
    {
        var d = new OpenFolderDialog { Title = "Master Rallye game folder" };
        if (d.ShowDialog(this) != true) return false;
        _settings.GameRoot = d.FolderName; _settings.Save();
        return true;
    }

    void OpenWorkspace(string root)
    {
        _ws?.Dispose();
        _ws = new Workspace(root);
        BuildInsertMenu();
        Status($"Game: {root}  EXE {(_ws.Exe?.IsRetail == true ? "retail (verified)" : _ws.Exe != null ? "NOT retail" : "missing")}");
    }

    void Attach(EditorSession s)
    {
        if (_s != null) _s.Changed -= OnSessionChanged;
        _s = s; _s.Changed += OnSessionChanged;
        _interactFocus = null; _live = null;
        RefreshAll();
    }

    void NewProject(string name)
    {
        var p = new MenuProject { Name = name };
        p.Screens.Add(_ws!.NewRetailScreen("MainMenu"));
        Attach(new EditorSession(_ws, p, null));
    }

    void OpenProject(string path)
    {
        try
        {
            var p = MenuProject.Load(path);
            Attach(new EditorSession(_ws!, p, path));
            _settings.LastProject = path; _settings.Save();
        }
        catch (Exception ex) { MessageBox.Show(this, ex.Message, "Open project"); }
    }

    void OnSessionChanged() => RefreshAll();

    void RefreshAll()
    {
        if (_s == null) return;
        _refreshing = true;
        Title = $"Master Rallye Menu Builder — {_s.Project.Name}{(_s.Dirty ? " *" : "")} — {(_s.Path ?? "unsaved")}";
        ScreenList.Items.Clear();
        foreach (var sc in _s.Project.Screens)
            ScreenList.Items.Add(new ListBoxItem { Content = $"{(sc.IsCustom ? "★ " : "")}{sc.Name}{(sc.IsCustom ? "  (custom)" : "")}", Tag = sc.Name, IsSelected = sc == _s.Screen });
        _refreshing = false;
        RenderView();
        RefreshElements();
        RefreshProps();
        RunValidation();
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

    void RenderView()
    {
        if (_s?.Screen == null || _ws == null) return;
        var ratio = Aspect.Parse(AspectKey()).Ratio;
        double availW = Math.Max(200, ViewHost.ActualWidth - 16), availH = Math.Max(150, ViewHost.ActualHeight - 16);
        int h = (int)Math.Min(availH, availW / ratio), w = (int)(h * ratio);
        if (w < 64 || h < 48) return;
        _s.Aspect = VariantKey();
        try { _scene = _s.Variant(); }
        catch (Exception ex) { Status("Build error: " + ex.Message); return; }
        var opt = new RenderOptions
        {
            Width = w, Height = h, Mode = Mode(), ShowHitboxes = HitboxBox.IsChecked == true, ShowNavigation = NavBox.IsChecked == true,
            ShowSafeArea = SafeBox.IsChecked == true, GhostHidden = HiddenBox.IsChecked == true, ShowRuntimeHidden = HiddenBox.IsChecked == true,
            FocusedId = InteractBox.IsChecked == true ? _interactFocus ?? FirstFocus() : SelectedFocusId(),
        };
        var compare = CompareBox.SelectedIndex;
        SceneRenderer.Canvas c;
        if (compare == 1) c = _ws.Renderer.Render(_s.Original(), opt);
        else
        {
            c = _ws.Renderer.Render(_scene, opt);
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
        double step = 20;
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

    double Shift(Egg e) => WidescreenModel.RendererShift(Mode(), _canvas!.Ratio, e.X, e.Y, e.TextAi != null && e.Kind is ElementKind.Text or ElementKind.Label);

    UiRect ShownBounds(Egg e) => _ws!.Layout.Bounds(e).Offset(Shift(e), 0);

    void DrawOverlay()
    {
        Overlay.Children.Clear();
        if (_canvas == null || _scene == null) return;
        if (GuidesBox.IsChecked == true)
        {
            var a = PixelRect(new UiRect(0, 0, 640, 480));
            AddRect(a, Brushes.Transparent, new SolidColorBrush(Color.FromArgb(120, 0, 200, 255)), 1, dash: true);
            var mid = _canvas.ToPixel(320, 240);
            AddLine(mid.x, 0, mid.x, _canvas.H, Color.FromArgb(70, 0, 200, 255));
            AddLine(0, mid.y, _canvas.W, mid.y, Color.FromArgb(70, 0, 200, 255));
        }
        foreach (var name in _s!.Selection)
        {
            var egg = _scene.Find(name);
            if (egg == null) continue;
            var r = PixelRect(ShownBounds(egg));
            if (_drag == DragKind.Move) r.Offset(_dragDx * _canvas.W / _canvas.VirtualWidth, -_dragDy * _canvas.H / 480);
            AddRect(r, new SolidColorBrush(Color.FromArgb(30, 255, 208, 0)), Brushes.Gold, 1.5);
            if (_s.Selection.Count == 1)
            {
                var handle = new Rectangle { Width = 9, Height = 9, Fill = Brushes.Gold, Cursor = Cursors.SizeNWSE, Tag = "scale" };
                Canvas.SetLeft(handle, r.Right - 4); Canvas.SetTop(handle, r.Bottom - 4);
                Overlay.Children.Add(handle);
                if (egg.IsPrimaryFocusable && HitboxBox.IsChecked != true)
                    AddRect(PixelRect(_ws!.Layout.Hitbox(egg).Offset(Shift(egg), 0)), Brushes.Transparent, Brushes.OrangeRed, 1, dash: true);
            }
        }
        if (_live != null && _liveScene != null && string.Equals(_liveScene, CurrentSceneName(), StringComparison.OrdinalIgnoreCase))
            foreach (var (id, (egg, rect)) in _live)
                AddRect(PixelRect(rect), Brushes.Transparent, Brushes.Cyan, 1, dash: true);
        // Visible area of a stretched/centred UI in the chosen window.
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

    void AddLine(double x0, double y0, double x1, double y1, Color c) =>
        Overlay.Children.Add(new Line { X1 = x0, Y1 = y0, X2 = x1, Y2 = y1, Stroke = new SolidColorBrush(c), StrokeThickness = 1, IsHitTestVisible = false });

    string CurrentSceneName() => _s!.Screen!.IsCustom ? "MB_" + _s.Screen.Name : _s.Screen.Base;

    int? SelectedFocusId() => _s!.Selection.Count == 1 ? _scene?.Find(_s.Selection[0])?.ButtonId : null;
    int? FirstFocus() => _s!.Screen!.DefaultFocus ?? _scene?.Focusables.Select(e => e.ButtonId).FirstOrDefault();

    // ---- canvas interaction ------------------------------------------------------------------------
    Egg? HitEgg(Point p)
    {
        if (_scene == null || _canvas == null) return null;
        var (ux, uy) = _canvas.ToUi(p.X, p.Y);
        var order = _scene.Eggs.Select((e, i) => (e, i)).OrderBy(t => t.e.DrawPriority).ThenByDescending(t => t.i).Select(t => t.e);
        foreach (var e in order)
        {
            if (e.Kind is ElementKind.Screen or ElementKind.Camera or ElementKind.Effect) continue;
            if ((!e.Visible || LayoutEngine.NativeHidden(_scene, e)) && HiddenBox.IsChecked != true) continue;
            if (e.Kind == ElementKind.Background && _s!.Selection.Count == 0 && Keyboard.Modifiers == ModifierKeys.None) { }
            if (ShownBounds(e).Contains(ux, uy) && e.Kind != ElementKind.Background) return e;
        }
        return order.FirstOrDefault(e => e.Kind == ElementKind.Background && ShownBounds(e).Contains(ux, uy));
    }

    void OnCanvasDown(object sender, MouseButtonEventArgs e)
    {
        if (_s == null || _canvas == null) return;
        Overlay.Focus();
        var p = e.GetPosition(Overlay);
        if (InteractBox.IsChecked == true)
        {
            var (ux, uy) = _canvas.ToUi(p.X, p.Y);
            var b = _scene!.Focusables.Where(f => _ws!.Layout.Hitbox(f).Offset(Shift(f), 0).Contains(ux, uy)).LastOrDefault();
            if (b != null) { _interactFocus = b.ButtonId; RenderView(); ReportAction(b); }
            return;
        }
        if (e.OriginalSource is Rectangle { Tag: "scale" } && _s.Selection.Count == 1 && _scene!.Find(_s.Selection[0]) is { } se)
        {
            _drag = DragKind.Scale; _dragStart = p; _dragRect = _ws!.Layout.SpriteRect(se); _dragScaleX = se.ScaleX; _dragScaleY = se.ScaleY;
            Overlay.CaptureMouse(); return;
        }
        var egg = HitEgg(p);
        if (egg == null) { _s.Selection.Clear(); SyncSelection(); return; }
        if (Keyboard.Modifiers.HasFlag(ModifierKeys.Control))
        {
            if (!_s.Selection.Remove(egg.Name)) _s.Selection.Add(egg.Name);
        }
        else if (!_s.Selection.Contains(egg.Name)) { _s.Selection.Clear(); _s.Selection.Add(egg.Name); }
        SyncSelection();
        _drag = DragKind.Move; _dragStart = p; _dragDx = _dragDy = 0;
        Overlay.CaptureMouse();
    }

    void OnCanvasMove(object sender, MouseEventArgs e)
    {
        if (_canvas == null) return;
        var p = e.GetPosition(Overlay);
        var (ux, uy) = _canvas.ToUi(p.X, p.Y);
        var hover = _drag == DragKind.None ? HitEgg(p) : null;
        CursorText.Text = $"ui ({ux:0.0}, {uy:0.0})  {(hover != null ? hover.Name + " [" + hover.Kind + "]" : "")}  variant {VariantKey()}";
        if (_drag == DragKind.Move)
        {
            double k = _canvas.VirtualWidth / _canvas.W;
            _dragDx = EditorSession.Snap((p.X - _dragStart.X) * k, SnapStep());
            _dragDy = EditorSession.Snap(-(p.Y - _dragStart.Y) * 480.0 / _canvas.H, SnapStep());
            DrawOverlay();
            Status($"move {_dragDx:+0.#;-0.#;0}, {_dragDy:+0.#;-0.#;0}");
        }
        else if (_drag == DragKind.Scale)
        {
            double k = _canvas.VirtualWidth / _canvas.W;
            double w0 = Math.Max(1, _dragRect.Width), h0 = Math.Max(1, _dragRect.Height);
            double sx = _dragScaleX * (w0 + (p.X - _dragStart.X) * k) / w0, sy = _dragScaleY * (h0 + (p.Y - _dragStart.Y) * 480.0 / _canvas.H) / h0;
            if (Keyboard.Modifiers.HasFlag(ModifierKeys.Shift)) sy = sx * _dragScaleY / _dragScaleX;
            Status($"scale {sx:0.00} × {sy:0.00}");
            _pendingScale = (Math.Round(Math.Max(0.1, sx), 2), Math.Round(Math.Max(0.1, sy), 2));
        }
    }
    (double, double)? _pendingScale;

    void OnCanvasUp(object sender, MouseButtonEventArgs e)
    {
        Overlay.ReleaseMouseCapture();
        if (_drag == DragKind.Move && (_dragDx != 0 || _dragDy != 0)) { var (dx, dy) = (_dragDx, _dragDy); _drag = DragKind.None; _s!.Move(_s.Selection, dx, dy, 0); }
        else if (_drag == DragKind.Scale && _pendingScale is var (sx, sy)) { _drag = DragKind.None; _s!.Patch(_s.Selection, "Scale", (p, _) => { p.ScaleX = (float)sx; p.ScaleY = (float)sy; }); }
        _drag = DragKind.None; _pendingScale = null; _dragDx = _dragDy = 0;
        DrawOverlay();
    }

    void OnCanvasRightUp(object sender, MouseButtonEventArgs e)
    {
        if (InteractBox.IsChecked == true) { Status("Back (-3): " + (_s!.Screen!.Back?.ToString() ?? (_s.Screen.IsCustom ? "← back" : "native"))); return; }
        var menu = new ContextMenu();
        void Item(string text, Action a) { var m = new MenuItem { Header = text }; m.Click += (_, _) => a(); menu.Items.Add(m); }
        Item("Duplicate", () => OnDuplicate(this, new RoutedEventArgs()));
        Item("Rename…", () => OnRename(this, new RoutedEventArgs()));
        Item("Delete", () => OnDelete(this, new RoutedEventArgs()));
        Item("Bring forward", () => _s!.ZOrder(-1));
        Item("Send backward", () => _s!.ZOrder(1));
        Item("Link navigation top→bottom", () => _s!.AutoLinkVertical());
        menu.IsOpen = true;
    }

    void ReportAction(Egg b)
    {
        var def = _s!.Screen!.Element(b.Name) ?? _s.Screen.ForBase(b.Name);
        var cb = _compiled?.Screens.FirstOrDefault(x => x.Name == _s.Screen.Name)?.Buttons.FirstOrDefault(x => x.Egg == b.Name);
        Status($"#{b.ButtonId} {b.Name}: {cb?.Action.ToString() ?? def?.Action?.ToString() ?? "native"} [{cb?.Status.ToString() ?? "?"}]");
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
            var text = $"{KindGlyph(e.Kind)} {e.Name}{(e.ButtonId is int id ? $"  #{id}" : "")}{mark}";
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
        DrawOverlay();
        RenderView();
    }

    void OnScreenSelected(object sender, SelectionChangedEventArgs e)
    {
        if (_refreshing || _s == null || ScreenList.SelectedItem is not ListBoxItem { Tag: string name }) return;
        _interactFocus = null;
        _s.SelectScreen(name);
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

    void Row(string label, UIElement editor, string? tip = null)
    {
        var g = new Grid { Margin = new Thickness(0, 1, 0, 1) };
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(120) });
        g.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        var t = new TextBlock { Text = label, VerticalAlignment = VerticalAlignment.Center, ToolTip = tip };
        g.Children.Add(t); Grid.SetColumn(editor, 1); g.Children.Add(editor);
        Props.Children.Add(g);
    }

    void Field(string label, string? value, Action<string> commit, string? tip = null)
    {
        var box = new TextBox { Text = value ?? "", ToolTip = tip };
        void Do() { if (box.Text != (value ?? "")) Try(() => commit(box.Text.Trim())); }
        box.LostFocus += (_, _) => Do();
        box.KeyDown += (_, e) => { if (e.Key == Key.Enter) { Do(); e.Handled = true; } };
        Row(label, box, tip);
    }

    void Check(string label, bool value, Action<bool> commit)
    {
        var c = new CheckBox { IsChecked = value };
        c.Click += (_, _) => Try(() => commit(c.IsChecked == true));
        Row(label, c);
    }

    void Combo(string label, IEnumerable<string> items, string? value, Action<string> commit, bool editable = false)
    {
        var c = new ComboBox { IsEditable = editable };
        foreach (var i in items) c.Items.Add(i);
        if (editable) c.Text = value ?? ""; else c.SelectedItem = value;
        bool ready = false;
        c.SelectionChanged += (_, _) => { if (ready && c.SelectedItem is string s && s != value) Try(() => commit(s)); };
        if (editable) c.LostFocus += (_, _) => { if (c.Text != (value ?? "")) Try(() => commit(c.Text)); };
        ready = true;
        Row(label, c);
    }

    void Try(Action a) { try { a(); } catch (Exception ex) { MessageBox.Show(this, ex.Message, "Edit"); } }

    static float? F(string s) => s.Length == 0 ? null : float.Parse(s, CultureInfo.InvariantCulture);
    static int? I(string s) => s.Length == 0 ? null : int.Parse(s, CultureInfo.InvariantCulture);
    static string Fs(float v) => v.ToString("0.##", CultureInfo.InvariantCulture);

    void RefreshProps()
    {
        Props.Children.Clear();
        if (_s?.Screen == null || _scene == null) return;
        var sc = _s.Screen;
        if (_s.Selection.Count != 1)
        {
            Header($"SCREEN {sc.Name}");
            Props.Children.Add(new TextBlock { Text = $"{(sc.IsCustom ? "Custom screen hosted by " + Compiler.HostAi : "Retail screen " + sc.Base)}\nbase {sc.Base}  {_ws!.Data.Source(Compiler.ScenePath(sc.Base))}\n{_s.Selection.Count} selected", TextWrapping = TextWrapping.Wrap });
            if (_s.Selection.Count > 1)
            {
                Header("MULTIPLE SELECTION");
                Combo("Style", _s.Project.Styles.Keys.Prepend(""), null, v => _s.ApplyStyle(v));
                Combo("Anchor", new[] { "none", "left", "right", "center" }, null, v => _s.Patch(_s.Selection, "Anchor", (p, _) => p.Anchor = v == "none" ? null : v));
            }
            return;
        }
        var egg = _scene.Find(_s.Selection[0]);
        if (egg == null) return;
        var def = sc.Element(egg.Name) ?? sc.ForBase(egg.Name);
        var name = egg.Name;
        Header($"{egg.Kind.ToString().ToUpperInvariant()}  {name}");
        Props.Children.Add(new TextBlock { Text = def?.IsNew == true ? $"new element from {def.Template}" : $"retail egg{(def?.Name != def?.Base && def != null ? " (renamed from " + def.Base + ")" : "")}", Foreground = Brushes.Gray, TextWrapping = TextWrapping.Wrap });
        Props.Children.Add(new TextBlock { Text = "AIs: " + string.Join(", ", egg.AiNames), Foreground = Brushes.Gray, TextWrapping = TextWrapping.Wrap });
        if (_s.EditAspectOverride && _s.Aspect != "4:3") Props.Children.Add(new TextBlock { Text = $"Geometry edits apply to the {_s.Aspect} variant only", Foreground = Brushes.Orange });

        Header("GEOMETRY");
        Field("X", Fs(egg.X), v => _s.Patch(new[] { name }, "X", (p, _) => p.X = F(v)), "authored units, 640x480, y up");
        Field("Y", Fs(egg.Y), v => _s.Patch(new[] { name }, "Y", (p, _) => p.Y = F(v)));
        Field("Scale X", Fs(egg.ScaleX), v => _s.Patch(new[] { name }, "Scale", (p, _) => p.ScaleX = F(v)), "en2d matrix scale: sprite, label and icon scale together in game");
        Field("Scale Y", Fs(egg.ScaleY), v => _s.Patch(new[] { name }, "Scale", (p, _) => p.ScaleY = F(v)));
        Field("Draw priority", egg.DrawPriority.ToString(), v => _s.Patch(new[] { name }, "Priority", (p, _) => p.DrawPriority = I(v)), "higher = further back (background 6, buttons 3, titles 2)");
        Check("Visible", egg.Visible, v => _s.Patch(new[] { name }, "Visible", (p, _) => p.Visible = v));
        Combo("Anchor (wide)", new[] { "none", "left", "right", "center" }, def?.Patch.Anchor ?? "none", v => _s.Patch(new[] { name }, "Anchor", (p, _) => p.Anchor = v == "none" ? null : v));
        var b = ShownBounds(egg);
        Props.Children.Add(new TextBlock { Text = $"bounds {b}\nhitbox {(egg.IsPrimaryFocusable ? _ws!.Layout.Hitbox(egg).ToString() : "—")}", Foreground = Brushes.Gray });
        int dir = WidescreenModel.MarginDirection(egg.X, egg.Y, egg.TextAi != null && egg.Kind is ElementKind.Text or ElementKind.Label);
        if (dir != 0) Props.Children.Add(new TextBlock { Text = $"⚠ Widescreen 'preserve margins' shifts this element {(dir > 0 ? "right" : "left")} (reference rule at {egg.X:0},{egg.Y:0}).", Foreground = Brushes.Orange, TextWrapping = TextWrapping.Wrap });

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
            Field("Text", t.Get("Text String") is { } ts && ts != "Null" ? ts : "", v => _s.Patch(new[] { name }, "Text", (p, _) => p.Text = v), "literal text (clears Text ID / Broker key)");
            Field("Text ID", t.Get("Text ID#"), v => _s.Patch(new[] { name }, "Text ID", (p, _) => { p.TextId = I(v); p.Text = null; }), $"gaLocal group; current: {run?.Text}");
            Field("Text index", t.Get("Text ID Index#"), v => _s.Patch(new[] { name }, "Text index", (p, _) => p.TextIndex = I(v)));
            Field("Broker key", t.Get("Text*") is { } tk && tk != "Null" ? tk : "", v => _s.Patch(new[] { name }, "Text key", (p, _) => p.TextKey = v.Length == 0 ? "Null" : v));
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
            if (f.Has("Enabled")) Check("Enabled", f.Get("Enabled") != "False", v => _s.Patch(new[] { name }, "Enabled", (p, _) => p.Enabled = v));
            Header("ACTION");
            var cb = _compiled?.Screens.FirstOrDefault(x => x.Name == sc.Name)?.Buttons.FirstOrDefault(x => x.Egg == name);
            Props.Children.Add(new TextBlock { Text = $"status: {cb?.Status.ToString() ?? "?"}", Foreground = cb?.Status is BindingStatus.Unbound ? Brushes.OrangeRed : Brushes.LightGreen });
            var action = def?.Action;
            Combo("Type", ActionBinding.Types.Prepend("(retail native)"), action?.Type ?? "(retail native)", v =>
                _s.SetAction(name, v == "(retail native)" ? null : new ActionBinding { Type = v, Command = v == ActionBinding.Native ? egg.ButtonId : null }));
            if (action != null)
            {
                var screens = (_ws.Exe?.Screens ?? new List<string>()).Distinct().Concat(_s.Project.Screens.Where(x => x.IsCustom).Select(x => x.Name)).OrderBy(x => x).ToList();
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
                    Combo("Provider", _ws.Validator.KnownExtensions.OrderBy(x => x), action.Extension, v => { var a = Copy(); a.Extension = v; _s.SetAction(name, a); }, editable: true);
                    Field("Args", action.Args, v => { var a = Copy(); a.Args = v.Length == 0 ? null : v; _s.SetAction(name, a); });
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
        foreach (var f in _findings.OrderByDescending(f => f.Severity))
            FindingsList.Items.Add(new ListBoxItem
            {
                Content = f.ToString(), Tag = f,
                Foreground = f.Severity == Severity.Error ? Brushes.OrangeRed : f.Severity == Severity.Warning ? Brushes.Gold : Brushes.LightGray,
            });
        int e = _findings.Count(x => x.Severity == Severity.Error), w = _findings.Count(x => x.Severity == Severity.Warning);
        FindingsTitle.Text = $"VALIDATION  {e} errors, {w} warnings";
        RefreshProps();
    }

    void OnFindingActivated(object sender, MouseButtonEventArgs e)
    {
        if (FindingsList.SelectedItem is not ListBoxItem { Tag: Finding f } || _s == null) return;
        if (_s.Project.Screen(f.Screen) != null && _s.Screen?.Name != f.Screen) _s.SelectScreen(f.Screen);
        if (f.Aspect != null && AspectBox.Items.Contains(f.Aspect)) AspectBox.SelectedItem = f.Aspect;
        if (f.Element != null) { _s.Selection.Clear(); _s.Selection.AddRange(f.Element.Split(',').Where(n => _scene?.Find(n) != null)); SyncSelection(); }
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
        else if (ctrl && e.Key == Key.S) { OnSave(this, e); e.Handled = true; }
        else if (ctrl && e.Key == Key.C) { OnCopy(this, e); e.Handled = true; }
        else if (ctrl && e.Key == Key.V) { OnPaste(this, e); e.Handled = true; }
        else if (ctrl && e.Key == Key.D) { OnDuplicate(this, e); e.Handled = true; }
        else if (ctrl && e.Key == Key.OemCloseBrackets) { _s.ZOrder(-1); e.Handled = true; }
        else if (ctrl && e.Key == Key.OemOpenBrackets) { _s.ZOrder(1); e.Handled = true; }
        else if (e.Key == Key.Delete) { OnDelete(this, e); e.Handled = true; }
        else if (e.Key == Key.F2) { OnRename(this, e); e.Handled = true; }
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
        if (!ConfirmDiscard()) return;
        var n = Dialogs.Prompt(this, "New project", "Project / layout name:", "MyMenus");
        if (n != null) NewProject(n);
    }

    void OnOpenProject(object sender, RoutedEventArgs e)
    {
        if (!ConfirmDiscard()) return;
        var d = new OpenFileDialog { Filter = "Menu Builder project (*.mrmenu.json)|*.mrmenu.json|JSON|*.json" };
        if (d.ShowDialog(this) == true) OpenProject(d.FileName);
    }

    void OnSave(object sender, RoutedEventArgs e) { if (_s?.Path == null) OnSaveAs(sender, e); else { _s.Save(); Status("Saved " + _s.Path); } }

    void OnSaveAs(object sender, RoutedEventArgs e)
    {
        var d = new SaveFileDialog { Filter = "Menu Builder project (*.mrmenu.json)|*.mrmenu.json", FileName = _s!.Project.Name + ".mrmenu.json" };
        if (d.ShowDialog(this) != true) return;
        _s.Save(d.FileName); _settings.LastProject = d.FileName; _settings.Save(); Status("Saved " + d.FileName);
    }

    bool ConfirmDiscard() => _s == null || !_s.Dirty || MessageBox.Show(this, "Discard unsaved changes?", "Menu Builder", MessageBoxButton.YesNo) == MessageBoxResult.Yes;
    void OnClosing(object? sender, System.ComponentModel.CancelEventArgs e) { if (!ConfirmDiscard()) e.Cancel = true; }
    void OnExit(object sender, RoutedEventArgs e) => Close();

    void OnGameFolder(object sender, RoutedEventArgs e)
    {
        if (!ChooseGameFolder()) return;
        OpenWorkspace(_settings.GameRoot!);
        if (_s != null) Attach(new EditorSession(_ws!, _s.Project, _s.Path));
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
    void OnCopy(object sender, RoutedEventArgs e) { if (_s?.Selection.Count > 0) { _clipboard = _s.Copy(_s.Selection); Clipboard.SetText(_clipboard); Status($"copied {_s.Selection.Count}"); } }
    void OnPaste(object sender, RoutedEventArgs e)
    {
        var text = Clipboard.ContainsText() ? Clipboard.GetText() : _clipboard;
        if (text == null || _s == null) return;
        Try(() => _s.Paste(text, 10, -10));
    }
    void OnDuplicate(object sender, RoutedEventArgs e) { if (_s?.Selection.Count > 0) Try(() => _s.Duplicate(_s.Selection, 10, -10)); }
    void OnDelete(object sender, RoutedEventArgs e)
    {
        if (_s?.Selection.Count > 0 && _scene!.Find(_s.Selection[0])?.Kind == ElementKind.Screen) { MessageBox.Show(this, "The screen controller egg cannot be deleted."); return; }
        if (_s?.Selection.Count > 0) _s.Delete(_s.Selection);
    }
    void OnRename(object sender, RoutedEventArgs e)
    {
        if (_s?.Selection.Count != 1) return;
        var old = _s.Selection[0];
        var def = _s.Screen!.Element(old) ?? _s.Screen.ForBase(old);
        if (def?.IsNew != true && MessageBox.Show(this, "Renaming a retail egg can break native code that looks it up by name (e.g. SureText). Continue?", "Rename", MessageBoxButton.YesNo) != MessageBoxResult.Yes) return;
        var n = Dialogs.Prompt(this, "Rename", "New egg name:", old);
        if (n != null && n != old) Try(() => _s.Rename(old, n));
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
            _s.Add(template, stem, 260, 240, text: text);
            Status($"Added {stem}; set its action in the properties panel");
        });
    }

    void OnAlign(object sender, RoutedEventArgs e) => _s?.Align((string)((MenuItem)sender).Tag);
    void OnDistribute(object sender, RoutedEventArgs e) => _s?.DistributeVertical();
    void OnBringForward(object sender, RoutedEventArgs e) => _s?.ZOrder(-1);
    void OnSendBackward(object sender, RoutedEventArgs e) => _s?.ZOrder(1);
    void OnAutoLink(object sender, RoutedEventArgs e) => _s?.AutoLinkVertical();

    void OnAddRetailScreen(object sender, RoutedEventArgs e)
    {
        var have = _s!.Project.Screens.Select(s => s.Base).ToHashSet(StringComparer.OrdinalIgnoreCase);
        var pick = Dialogs.Pick(this, "Add retail screen", "Native frontend screens of this installation:", _ws!.RetailScreens().Where(r => !have.Contains(r.name)).Select(r => $"{r.name}  ({r.source})"));
        if (pick != null) _s.AddScreen(_ws.NewRetailScreen(pick.Split(' ')[0]));
    }

    void OnAddCustomScreen(object sender, RoutedEventArgs e)
    {
        var r = Dialogs.Form(this, "New custom screen", ("Name (letters/digits):", "MyScreen"), ("Title:", "MY SCREEN"), ("Visual base (retail screen; its controller is replaced by the host AI):", Compiler.HostScreen));
        if (r == null || r[0].Length == 0) return;
        Try(() =>
        {
            if (_s!.Project.Screen(r[0]) != null || !r[0].All(char.IsLetterOrDigit)) throw new ArgumentException("name exists or has invalid characters");
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
        RunValidation();
        int errors = _findings.Count(f => f.Severity == Severity.Error);
        if (errors > 0 && MessageBox.Show(this, $"{errors} validation errors. Buttons without a working handler would be installed. Install anyway?", "Install", MessageBoxButton.YesNo) != MessageBoxResult.Yes) return;
        Try(() =>
        {
            var res = Installer.Install(_s!.Project, _compiled!, _ws!.Data, _ws.Exe);
            bool runtime = File.Exists(System.IO.Path.Combine(_ws.Data.Root, "dinput8.dll"));
            Status($"Installed {res.Files.Count} files to {res.Directory}{(runtime ? "" : " — dinput8.dll with the Menu Builder runtime is not installed in the game folder")}");
        });
    }

    void OnClassic(object sender, RoutedEventArgs e) { Installer.SetActive(_ws!.Data.Root, null); Status("Classic frontend selected (layouts stay installed)"); }

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

    void OnAbout(object sender, RoutedEventArgs e) => MessageBox.Show(this,
        "Master Rallye Menu Builder 1.0\n\nWYSIWYG editor of the native frontend scenes (DataScene/FrontendScreens).\n" +
        "Projects are declarative deltas over the installed pages; the dinput8 runtime serves compiled layouts to the real frontend.\n\n" +
        "Command line / machine API: mrmenu.exe (JSON). Python: tools/menu-builder/python/mr_menu_builder.py.\nDocumentation: docs/menu-builder.md", "About");
}
