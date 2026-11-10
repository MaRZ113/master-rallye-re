using System.Text.Json;


namespace MenuBuilder.Core;

/// <summary>
/// Editing state of one project: every change goes through <see cref="Edit"/> so it is undoable and is
/// stored as a delta (ElementDef patch / aspect override) — the retail scene is never modified.
/// </summary>
public sealed class EditorSession
{
    public Workspace Ws { get; }
    public MenuProject Project { get; private set; }
    public string? Path { get; set; }
    public bool Dirty { get; private set; }
    public ScreenDef? Screen { get; private set; }
    public string Aspect { get; set; } = "4:3";
    /// <summary>When true, geometry edits go to Aspects[Aspect] instead of the base layout.</summary>
    public bool EditAspectOverride { get; set; }
    public List<string> Selection { get; } = new();
    readonly Stack<string> _undo = new(), _redo = new();
    public event Action? Changed;

    public EditorSession(Workspace ws, MenuProject project, string? path)
    {
        Ws = ws; Project = project; Path = path;
        Screen = project.Screens.FirstOrDefault();
    }

    public void SelectScreen(string name)
    {
        Screen = Project.Screen(name);
        Selection.Clear();
        Changed?.Invoke();
    }

    // ---- scene views -------------------------------------------------------------------------
    public SceneDocument Scene() => Screen == null ? throw new InvalidOperationException("no screen") : Ws.Compiler.BuildScene(Project, Screen);
    public SceneDocument Variant() => Ws.Compiler.Variant(Project, Screen!, Scene(), Aspect);
    public SceneDocument Original() => Ws.Compiler.Base(Screen!.Base);

    // ---- undo ----------------------------------------------------------------------------------
    public void Edit(string what, Action change)
    {
        _undo.Push(Project.ToJson());
        _redo.Clear();
        change();
        Dirty = true;
        LastEdit = what;
        Changed?.Invoke();
    }
    public string LastEdit { get; private set; } = "";
    public bool CanUndo => _undo.Count > 0;
    public bool CanRedo => _redo.Count > 0;
    void Restore(string json)
    {
        var screen = Screen?.Name;
        Project = MenuProject.FromJson(json);
        Screen = screen != null ? Project.Screen(screen) ?? Project.Screens.FirstOrDefault() : Project.Screens.FirstOrDefault();
        if (Screen != null) { var scene = Scene(); Selection.RemoveAll(n => scene.Find(n) == null); } else Selection.Clear();
        Dirty = true;
        Changed?.Invoke();
    }
    public void Undo() { if (_undo.Count == 0) return; _redo.Push(Project.ToJson()); Restore(_undo.Pop()); }
    public void Redo() { if (_redo.Count == 0) return; _undo.Push(Project.ToJson()); Restore(_redo.Pop()); }

    public void Save(string? path = null)
    {
        Path = path ?? Path ?? throw new InvalidOperationException("no path");
        Project.Save(Path);
        Dirty = false;
        Changed?.Invoke();
    }

    // ---- element definitions -------------------------------------------------------------------
    /// <summary>Definition that owns an egg of the current screen, created on first edit for retail eggs.</summary>
    public ElementDef Def(string egg)
    {
        var s = Screen!;
        var def = s.Element(egg) ?? s.ForBase(egg);
        if (def != null) return def;
        def = new ElementDef { Name = egg, Base = egg };
        s.Elements.Add(def);
        return def;
    }

    /// <summary>Patch target: the base delta or the aspect override of the current variant.</summary>
    public ElementPatch PatchFor(string egg)
    {
        if (!EditAspectOverride || Aspect == "4:3") return Def(egg).Patch;
        if (!Screen!.Aspects.TryGetValue(Aspect, out var map)) Screen.Aspects[Aspect] = map = new();
        if (!map.TryGetValue(egg, out var p)) map[egg] = p = new ElementPatch();
        return p;
    }

    public void Patch(IEnumerable<string> eggs, string what, Action<ElementPatch, Egg> apply)
    {
        var scene = Variant();
        Edit(what, () =>
        {
            foreach (var name in eggs.ToList())
                if (scene.Find(name) is { } egg) apply(PatchFor(name), egg);
        });
    }

    public void Move(IEnumerable<string> eggs, double dx, double dy, double snap)
    {
        Patch(eggs, "Move", (p, egg) =>
        {
            p.X = (float)Snap(egg.X + dx, snap);
            p.Y = (float)Snap(egg.Y + dy, snap);
        });
    }

    public static double Snap(double v, double step) => step <= 0 ? Math.Round(v, 2) : Math.Round(v / step) * step;

    public void Delete(IEnumerable<string> eggs)
    {
        Edit("Delete", () =>
        {
            foreach (var name in eggs.ToList())
            {
                var s = Screen!;
                var def = s.Element(name) ?? s.ForBase(name);
                if (def != null && def.IsNew) s.Elements.Remove(def);
                else Def(name).Deleted = true;
                foreach (var a in s.Aspects.Values) a.Remove(name);
            }
            Selection.Clear();
        });
    }

    public string UniqueName(string stem)
    {
        var scene = Scene();
        var names = scene.Eggs.Select(e => e.Name).Concat(Screen!.Elements.Select(e => e.Name)).ToHashSet();
        if (!names.Contains(stem)) return stem;
        for (int i = 2; ; i++) if (!names.Contains(stem + i)) return stem + i;
    }

    /// <summary>Next free Button ID, ignoring <paramref name="except"/> (the element being assigned).</summary>
    int NextButtonId(string? except = null)
    {
        var scene = Scene();
        var used = scene.Eggs.Where(e => e.IsFocusable && e.Name != except).Select(e => e.ButtonId ?? 0).ToHashSet();
        int id = Screen!.IsCustom ? 1 : Math.Max(10, used.DefaultIfEmpty(0).Max() + 1);
        while (used.Contains(id)) id++;
        return id;
    }

    /// <summary>Adds a new element from a template ("Egg", "Screen/Egg" or "component:Name").</summary>
    public string Add(string template, string stem, float x, float y, ActionBinding? action = null, string? text = null)
    {
        string name = UniqueName(stem);
        Edit("Add " + name, () =>
        {
            var def = new ElementDef { Name = name, Template = template, Patch = new ElementPatch { X = x, Y = y } };
            if (text != null) def.Patch.Text = text;
            Screen!.Elements.Add(def);
            var egg = Scene().Find(name);
            if (egg?.Focusable != null)
            {
                def.Patch.ButtonId = NextButtonId(name);
                def.Patch.Up = def.Patch.Down = def.Patch.Left = def.Patch.Right = 0;
                def.Action = action ?? new ActionBinding { Type = ActionBinding.None };
            }
            Selection.Clear(); Selection.Add(name);
        });
        return name;
    }

    /// <summary>Copies of eggs as new elements (same screen: template = the egg's base/template; patch = current values).</summary>
    public List<string> Duplicate(IEnumerable<string> eggs, float dx, float dy)
    {
        var created = new List<string>();
        var scene = Variant();
        Edit("Duplicate", () =>
        {
            foreach (var n in eggs.ToList())
            {
                var egg = scene.Find(n);
                if (egg == null) continue;
                var src = Screen!.Element(n) ?? Screen.ForBase(n);
                var copy = src?.Clone() ?? new ElementDef();
                copy.Name = UniqueName(n + "Copy");
                copy.Deleted = false;
                copy.Template = src?.IsNew == true ? src.Template : (src?.Base ?? n);
                copy.Base = null;
                copy.Patch.X = egg.X + dx; copy.Patch.Y = egg.Y + dy;
                Screen.Elements.Add(copy);
                if (Scene().Find(copy.Name)?.Focusable != null)
                {
                    copy.Patch.ButtonId = NextButtonId(copy.Name);
                    copy.Patch.Up = copy.Patch.Down = copy.Patch.Left = copy.Patch.Right = 0;
                    copy.Action ??= new ActionBinding { Type = ActionBinding.None };
                }
                created.Add(copy.Name);
            }
            Selection.Clear(); Selection.AddRange(created);
        });
        return created;
    }

    public void Rename(string egg, string newName)
    {
        if (string.IsNullOrWhiteSpace(newName) || Scene().Find(newName) != null) throw new ArgumentException("name already used or empty");
        Edit("Rename", () =>
        {
            Def(egg).Name = newName;
            foreach (var a in Screen!.Aspects.Values)
                if (a.Remove(egg, out var p)) a[newName] = p;
            Selection.Clear(); Selection.Add(newName);
        });
    }

    // ---- clipboard ------------------------------------------------------------------------------
    public string Copy(IEnumerable<string> eggs)
    {
        var scene = Variant();
        var items = eggs.Select(n => (n, egg: scene.Find(n), def: Screen!.Element(n) ?? Screen.ForBase(n)))
            .Where(t => t.egg != null)
            .Select(t => new ElementDef
            {
                Name = t.n,
                Template = t.def?.IsNew == true ? t.def.Template : $"{Screen!.Base}/{t.def?.Base ?? t.n}",
                Patch = (t.def?.Patch.Clone() ?? new ElementPatch()).Merge(new ElementPatch { X = t.egg!.X, Y = t.egg.Y }),
                Action = t.def?.Action?.Clone(), Style = t.def?.Style,
            }).ToList();
        return JsonSerializer.Serialize(items, MenuProject.Json);
    }

    public void Paste(string json, float dx, float dy)
    {
        var items = JsonSerializer.Deserialize<List<ElementDef>>(json, MenuProject.Json) ?? new();
        var names = new List<string>();
        Edit("Paste", () =>
        {
            foreach (var it in items)
            {
                it.Name = UniqueName(it.Name);
                it.Base = null; it.Deleted = false;
                it.Patch.X += dx; it.Patch.Y += dy;
                Screen!.Elements.Add(it);
                if (Scene().Find(it.Name)?.Focusable != null)
                {
                    it.Patch.ButtonId = NextButtonId(it.Name);
                    it.Patch.Up = it.Patch.Down = it.Patch.Left = it.Patch.Right = 0;
                    it.Action ??= new ActionBinding { Type = ActionBinding.None };
                }
                names.Add(it.Name);
            }
            Selection.Clear(); Selection.AddRange(names);
        });
    }

    // ---- arrangement -------------------------------------------------------------------------
    public void Align(string how)
    {
        if (Selection.Count < 2) return;
        var scene = Variant();
        var eggs = Selection.Select(n => scene.Find(n)).Where(e => e != null).Select(e => e!).ToList();
        var bounds = eggs.ToDictionary(e => e.Name, e => Ws.Layout.Bounds(e));
        var all = bounds.Values.Aggregate((a, b) => a.Union(b));
        Patch(Selection, "Align " + how, (p, egg) =>
        {
            var b = bounds[egg.Name];
            switch (how)
            {
                case "left": p.X = (float)(egg.X + all.X0 - b.X0); break;
                case "right": p.X = (float)(egg.X + all.X1 - b.X1); break;
                case "hcenter": p.X = (float)(egg.X + (all.X0 + all.X1) / 2 - (b.X0 + b.X1) / 2); break;
                case "top": p.Y = (float)(egg.Y + all.Y1 - b.Y1); break;
                case "bottom": p.Y = (float)(egg.Y + all.Y0 - b.Y0); break;
                case "vcenter": p.Y = (float)(egg.Y + (all.Y0 + all.Y1) / 2 - (b.Y0 + b.Y1) / 2); break;
            }
        });
    }

    public void DistributeVertical()
    {
        if (Selection.Count < 3) return;
        var scene = Variant();
        var eggs = Selection.Select(n => scene.Find(n)).Where(e => e != null).Select(e => e!).OrderByDescending(e => e.Y).ToList();
        double top = eggs.First().Y, bottom = eggs.Last().Y, step = (bottom - top) / (eggs.Count - 1);
        var targets = eggs.Select((e, i) => (e.Name, y: top + i * step)).ToDictionary(t => t.Name, t => t.y);
        Patch(Selection, "Distribute", (p, egg) => p.Y = (float)Math.Round(targets[egg.Name], 2));
    }

    /// <summary>Links the selected focusables top-to-bottom (Up/Down, wrapping), the native menu convention.</summary>
    public void AutoLinkVertical()
    {
        var scene = Scene();
        var eggs = Selection.Select(n => scene.Find(n)).Where(e => e?.IsPrimaryFocusable == true).Select(e => e!).OrderByDescending(e => e.Y).ToList();
        if (eggs.Count < 2) return;
        Edit("Link navigation", () =>
        {
            for (int i = 0; i < eggs.Count; i++)
            {
                var p = Def(eggs[i].Name).Patch;
                p.Up = eggs[(i - 1 + eggs.Count) % eggs.Count].ButtonId;
                p.Down = eggs[(i + 1) % eggs.Count].ButtonId;
            }
        });
    }

    public void ZOrder(int delta) => Patch(Selection, delta < 0 ? "Bring forward" : "Send backward", (p, egg) => p.DrawPriority = Math.Max(0, egg.DrawPriority + delta));

    /// <summary>
    /// Fix for a renderer PreserveMargins match on <paramref name="egg"/>: an exact reference point is left by
    /// a 1-unit nudge in every wide variant; a left-band match anchors the egg's column (same X ±2) to the
    /// same margin so the column moves together. Returns a description of what was changed.
    /// </summary>
    public string FixMargin(string egg)
    {
        var scene = Scene();
        var e = scene.Find(egg) ?? throw new KeyNotFoundException(egg);
        int dir = WidescreenModel.MarginDirection(e.X, e.Y, e.Kind == ElementKind.XYButton);
        if (dir == 0) return "no PreserveMargins rule matches";
        bool point = WidescreenModel.PointRules.Any(r => r.X == e.X && r.Y == e.Y);
        var wide = Project.Settings.Aspects.Where(a => a != "4:3").ToList();
        if (point)
        {
            Edit("Nudge out of margin rule", () =>
            {
                foreach (var a in wide)
                {
                    if (!Screen!.Aspects.TryGetValue(a, out var map)) Screen.Aspects[a] = map = new();
                    if (!map.TryGetValue(egg, out var p)) map[egg] = p = new ElementPatch();
                    p.X = e.X - dir;
                }
            });
            return $"{egg}: X {e.X}→{e.X - dir} in {string.Join(", ", wide)} (stays with its row)";
        }
        var column = scene.Eggs.Where(o => o.Name != egg && Math.Abs(o.X - e.X) <= 2 && o.Visible && o.Kind is not (ElementKind.Screen or ElementKind.Camera or ElementKind.Background)
                                           && WidescreenModel.MarginDirection(o.X, o.Y, o.Kind == ElementKind.XYButton) == 0).Select(o => o.Name).ToList();
        Edit("Anchor column to margin", () => { foreach (var n in column) Def(n).Patch.Anchor = dir < 0 ? "left" : "right"; });
        return $"anchored {column.Count} column eggs {(dir < 0 ? "left" : "right")}: {string.Join(", ", column)}";
    }

    public void SetAction(string egg, ActionBinding? action) => Edit("Action", () => Def(egg).Action = action);

    public void ApplyStyle(string style) => Edit("Style " + style, () => { foreach (var n in Selection) Def(n).Style = style.Length == 0 ? null : style; });

    public void StyleFromSelection(string name)
    {
        if (Selection.Count == 0) return;
        var def = Def(Selection[0]);
        Edit("New style " + name, () =>
        {
            var p = def.Patch.Clone();
            p.X = p.Y = null; p.ButtonId = p.Up = p.Down = p.Left = p.Right = null; p.Text = null; p.TextId = p.TextIndex = null;
            Project.Styles[name] = p;
        });
    }

    public void ComponentFromSelection(string name)
    {
        if (Selection.Count == 0) return;
        var n = Selection[0];
        var def = Screen!.Element(n) ?? Screen.ForBase(n);
        Edit("New component " + name, () =>
        {
            var p = (def?.Patch.Clone() ?? new ElementPatch());
            p.X = p.Y = null; p.ButtonId = p.Up = p.Down = p.Left = p.Right = null;
            Project.Components[name] = new ComponentDef
            {
                Template = def?.IsNew == true && def.Template != null && !def.Template.StartsWith("component:") && def.Template.Contains('/') ? def.Template : $"{Screen.Base}/{def?.Base ?? n}",
                Style = def?.Style, Patch = p, Description = $"from {Screen.Name}/{n}",
            };
        });
    }

    public void AddScreen(ScreenDef s) => Edit("Add screen " + s.Name, () => { Project.Screens.Add(s); Screen = s; Selection.Clear(); });
    public void RemoveScreen(string name) => Edit("Remove screen " + name, () => { Project.Screens.RemoveAll(x => x.Name == name); Screen = Project.Screens.FirstOrDefault(); Selection.Clear(); });
    public void ReplaceProject(MenuProject p) { _undo.Push(Project.ToJson()); _redo.Clear(); Project = p; Screen = p.Screens.FirstOrDefault(); Selection.Clear(); Dirty = true; Changed?.Invoke(); }
}
