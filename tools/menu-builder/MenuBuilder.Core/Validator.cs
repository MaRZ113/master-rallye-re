namespace MenuBuilder.Core;

public enum Severity { Info, Warning, Error }

/// <summary>One diagnostic. ERROR blocks installation; WARNING and INFO never do.</summary>
public sealed record Finding(Severity Severity, string Screen, string? Element, string Code, string Message, string? Aspect = null)
{
    /// <summary>Element type (egg kind) when known.</summary>
    public string? ElementType { get; init; }
    /// <summary>Operation that failed or was checked (e.g. "create from template", "bind action").</summary>
    public string? Operation { get; init; }
    /// <summary>What the author can do about it.</summary>
    public string? Fix { get; init; }
    public override string ToString() => $"{Severity.ToString().ToUpperInvariant()} {Screen}{(Element != null ? "/" + Element : "")}{(ElementType != null ? " (" + ElementType + ")" : "")}{(Aspect != null ? " [" + Aspect + "]" : "")} {Code}: {Message}{(Operation != null ? " — during: " + Operation : "")}{(Fix != null ? " — fix: " + Fix : "")}";
}

/// <summary>
/// Checks a compiled layout against the native rules: navigation graph, typed bindings,
/// hitbox ⇔ visual identity, aspect visibility and the renderer's PreserveMargins rules.
/// </summary>
public sealed class Validator
{
    readonly LayoutEngine _layout;
    readonly ExeTables? _exe;
    /// <summary>Action IDs offered by the editor (catalog; legacy names stay valid).</summary>
    public IEnumerable<string> KnownExtensions => ActionCatalog.Actions.Select(a => a.Id);

    public Validator(LayoutEngine layout, ExeTables? exe) { _layout = layout; _exe = exe; }

    public List<Finding> Validate(MenuProject project, CompiledLayout compiled)
    {
        var r = new List<Finding>();
        if (_exe != null && !_exe.IsRetail) r.Add(new(Severity.Warning, "*", null, "EXE_NOT_RETAIL", $"MRallye.exe {_exe.Sha256[..12]}… is not the certified retail image; native addresses are only verified for retail"));
        if (LayoutName.Problem(project.Name) is { } np)
            r.Add(new(Severity.Error, "*", null, "LAYOUT_NAME", $"project name '{project.Name}' cannot be a layout name: {np}") { Operation = "install", Fix = $"rename the project, e.g. '{LayoutName.Suggest(project.Name)}'" });
        r.AddRange(compiled.Diagnostics);
        foreach (var cs in compiled.Screens)
        {
            var def = project.Screen(cs.Name)!;
            r.AddRange(cs.Diagnostics);
            if (!cs.IsCustom && cs.NativeId < 0) r.Add(new(Severity.Error, cs.Name, null, "UNKNOWN_SCREEN", $"{cs.Base} is not in the native screen table"));
            if (cs.BaseSource == "loose") r.Add(new(Severity.Info, cs.Name, null, "BASE_LOOSE", $"base page comes from a loose file of another mod (sha {cs.BaseSha256[..12]}…); the delta is applied on top of it"));
            if (cs.BaseSource == "overlay") r.Add(new(Severity.Info, cs.Name, null, "BASE_OVERLAY", $"base page comes from the active Vehicle Manager roster (sha {cs.BaseSha256[..12]}…); the layout is served only while that roster page is unchanged"));
            if (def.BaseSha256 != null && def.BaseSha256 != cs.BaseSha256)
                r.Add(new(Severity.Warning, cs.Name, null, "BASE_CHANGED", "base page differs from the one the project was authored against; edits re-apply by egg name — review the screen"));
            var doc = cs.Variants["4:3"];
            if (cs.IsCustom && doc.ScreenAi != Compiler.HostAi)
                r.Add(new(Severity.Error, cs.Name, null, "NO_HOST", $"custom screen needs the {Compiler.HostAi} host egg"));
            // Unique names and IDs.
            foreach (var g in doc.Eggs.GroupBy(e => e.Name).Where(g => g.Count() > 1))
                r.Add(new(Severity.Error, cs.Name, g.Key, "DUPLICATE_NAME", "egg names must be unique (native lookups are by name)"));
            foreach (var g in cs.Buttons.GroupBy(b => b.Id).Where(g => g.Count() > 1))
                r.Add(new(Severity.Error, cs.Name, string.Join(",", g.Select(b => b.Egg)), "DUPLICATE_ID", $"Button ID {g.Key} is used by several focusables"));
            var ids = cs.Buttons.Select(b => b.Id).ToHashSet();
            var hiddenIds = cs.Buttons.Where(b => b.Hidden).Select(b => b.Id).ToHashSet();
            var dynamicIds = cs.Buttons.Where(b => b.VisibleWhen != null && !b.Hidden).Select(b => b.Id).ToHashSet();
            if (cs.DefaultFocus is int df)
            {
                if (!ids.Contains(df)) r.Add(new(Severity.Error, cs.Name, null, "FOCUS_TARGET", $"default focus {df} is not a focusable of this screen") { Operation = "screen settings", Fix = "pick an existing Button ID or clear the default focus" });
                else if (hiddenIds.Contains(df)) r.Add(new(Severity.Error, cs.Name, null, "FOCUS_HIDDEN", $"default focus {df} is a hidden element") { Operation = "screen settings", Fix = "pick a visible button" });
            }
            foreach (var b in cs.Buttons)
            {
                foreach (var (dir, target) in new[] { ("Up", b.Up), ("Down", b.Down), ("Left", b.Left), ("Right", b.Right) })
                {
                    if (target != 0 && !ids.Contains(target))
                        r.Add(new(Severity.Error, cs.Name, b.Egg, "NAV_TARGET", $"{dir} Path → {target} does not exist") { ElementType = b.Kind.ToString(), Operation = "focus navigation", Fix = "relink navigation" });
                    else if (target != 0 && !b.Hidden && dynamicIds.Contains(target))
                        r.Add(new(Severity.Info, cs.Name, b.Egg, "NAV_TO_DYNAMIC", $"{dir} Path → {target} is a dynamic row: focus continues past it while it is hidden"));
                    else if (target != 0 && !b.Hidden && hiddenIds.Contains(target))
                        r.Add(new(Severity.Error, cs.Name, b.Egg, "NAV_TO_HIDDEN", $"{dir} Path → {target} leads focus onto a hidden element") { ElementType = b.Kind.ToString(), Operation = "focus navigation", Fix = "use Hide (reroutes paths) or relink navigation" });
                }
                if (b.Hidden) r.Add(new(Severity.Info, cs.Name, b.Egg, "HIDDEN", "hidden: no hitbox, not focusable, command ignored by the runtime"));
                else if (b.Blocked && !b.Enabled) r.Add(new(Severity.Info, cs.Name, b.Egg, "DISABLED", "disabled: drawn greyed, command ignored"));
                else if (b.Blocked) r.Add(new(Severity.Warning, cs.Name, b.Egg, "DISABLED_NO_NATIVE_STATE", "this button has no native Enabled state: it is drawn normally but its command is ignored") { Fix = "hide it, or change its text to show that it is unavailable" });
                switch (b.Status)
                {
                    case BindingStatus.Unbound when !b.Blocked:
                        r.Add(new(Severity.Error, cs.Name, b.Egg, "UNBOUND", $"focusable without a working handler ('{b.Action.Type}' is not a retail command of this screen nor a typed action)")
                            { ElementType = b.Kind.ToString(), Operation = "bind action", Fix = "choose an action type, or hide/disable the button" }); break;
                    case BindingStatus.Extension:
                        CheckExtension(r, cs.Name, b); break;
                    case BindingStatus.Disabled when !b.Blocked:
                        r.Add(new(Severity.Info, cs.Name, b.Egg, "NO_ACTION", "action 'none': the button does nothing when pressed")); break;
                }
                if (b.Action.Type == ActionBinding.Forward)
                {
                    var target = b.Action.Screen ?? "";
                    if ((_exe?.ScreenId(target) ?? -1) < 0) r.Add(new(Severity.Error, cs.Name, b.Egg, "FORWARD_SCREEN", $"native.forward needs a retail screen, '{target}' is not one"));
                    else if (b.Action.Command is not int c || c <= 0) r.Add(new(Severity.Error, cs.Name, b.Egg, "FORWARD_COMMAND", "native.forward needs a positive command"));
                }
                if (b.Action.Type == ActionBinding.Navigate)
                {
                    var target = b.Action.Screen ?? "";
                    bool ok = project.Screens.Any(s => s.IsCustom && s.Name == target) || (_exe?.ScreenId(target) ?? -1) >= 0;
                    if (!ok) r.Add(new(Severity.Error, cs.Name, b.Egg, "NAV_SCREEN", $"navigate target '{target}' is neither a retail nor a custom screen"));
                }
                if ((b.Action.Type is ActionBinding.SetInt or ActionBinding.ToggleBool or ActionBinding.CycleInt) && !Ids.IsBrokerKey(b.Action.Key))
                    r.Add(new(Severity.Error, cs.Name, b.Egg, "BROKER_KEY", $"Broker action needs a key like 'Group/Name' (got '{b.Action.Key}')") { Operation = "bind action", Fix = "enter the Broker key" });
                if (b.Action.Type == ActionBinding.CycleInt && (b.Action.Min ?? 0) > (b.Action.Max ?? 1))
                    r.Add(new(Severity.Error, cs.Name, b.Egg, "CYCLE_RANGE", "cycle min is greater than max") { Operation = "bind action" });
                if (b.Action.Type == ActionBinding.Native && b.Action.Command is int nc && (nc <= 0 || nc > 255))
                    r.Add(new(Severity.Error, cs.Name, b.Egg, "COMMAND_RANGE", $"native command {nc} is outside 1..255") { Operation = "bind action" });
                if (b.Local.IsEmpty && !b.Hidden)
                    r.Add(new(Severity.Error, cs.Name, b.Egg, "NO_HITBOX", "focusable has neither a sprite nor text; it cannot be drawn or hit") { ElementType = b.Kind.ToString(), Operation = "create hitbox", Fix = "give it a sprite or a label" });
            }
            foreach (var v in cs.Values) CheckValue(r, cs.Name, v);
            // Reachability from the default focus over Up/Down/Left/Right (focusables with paths only).
            var pathful = cs.Buttons.Where(b => b.Kind is ElementKind.Button or ElementKind.Multistate or ElementKind.Popup or ElementKind.Toggle).ToList();
            if (pathful.Count > 0)
            {
                int start = cs.DefaultFocus ?? (ids.Contains(1) ? 1 : pathful[0].Id);
                var seen = new HashSet<int> { start };
                var queue = new Queue<int>(seen);
                while (queue.Count > 0)
                {
                    int current = queue.Dequeue();
                    var b = cs.Buttons.FirstOrDefault(x => x.Id == current);
                    if (b == null) continue;
                    foreach (var t in new[] { b.Up, b.Down, b.Left, b.Right }) if (t != 0 && seen.Add(t)) queue.Enqueue(t);
                }
                foreach (var b in pathful.Where(b => !seen.Contains(b.Id) && b.Enabled))
                    r.Add(new(Severity.Warning, cs.Name, b.Egg, "UNREACHABLE", $"not reachable with keyboard/gamepad from focus {start}"));
            }
            // Hitbox overlap and visibility per aspect.
            foreach (var aspect in compiled.Aspects)
            {
                var hits = cs.Buttons.Where(b => b.Hit.ContainsKey(aspect)).ToList();
                for (int i = 0; i < hits.Count; i++)
                    for (int j = i + 1; j < hits.Count; j++)
                        if (hits[i].Hit[aspect].Intersects(hits[j].Hit[aspect]) && hits[i].Kind != ElementKind.XYButton)
                            r.Add(new(Severity.Warning, cs.Name, $"{hits[i].Egg},{hits[j].Egg}", "HITBOX_OVERLAP", "mouse hitboxes overlap; the topmost (lower Draw Priority) wins", aspect));
                var ratio = Aspect.Parse(aspect).Ratio;
                var (left, right) = WidescreenModel.VisibleRange(aspect == "4:3" ? InterfaceMode.Stock : InterfaceMode.Centered4x3, ratio);
                var vdoc = cs.Variants[aspect];
                foreach (var egg in vdoc.Eggs.Where(e => e.Visible && e.Kind is not (ElementKind.Screen or ElementKind.Camera or ElementKind.Effect or ElementKind.Background)))
                {
                    var bnd = _layout.Bounds(egg);
                    if (bnd.X1 < left || bnd.X0 > right || bnd.Y1 < 0 || bnd.Y0 > 480)
                        r.Add(new(Severity.Warning, cs.Name, egg.Name, "OFFSCREEN", $"bounds {bnd} outside the visible area {left:0}..{right:0}", aspect));
                }
                // An active hitbox that cannot be seen is an invisible click area.
                foreach (var b in hits.Where(b => !b.Blocked))
                {
                    var h = b.Hit[aspect];
                    if (h.X1 <= left || h.X0 >= right || h.Y1 <= 0 || h.Y0 >= 480)
                        r.Add(new(Severity.Error, cs.Name, b.Egg, "HITBOX_OFFSCREEN", $"active hitbox {h} is entirely outside the visible area {left:0}..{right:0}", aspect)
                            { ElementType = b.Kind.ToString(), Operation = "create hitbox", Fix = "move the element on screen, or hide it in this aspect" });
                    else if (VisibleShare(h, left, right) < 0.75)
                        r.Add(new(Severity.Warning, cs.Name, b.Egg, "HITBOX_CLIPPED", $"hitbox {h} extends past the visible area {left:0}..{right:0}", aspect));
                }
            }
            // Renderer PreserveMargins rules (Widescreen = 2) on the 16:9 variant.
            var wide = cs.Variants.ContainsKey("16:9") ? "16:9" : compiled.Aspects.Last();
            foreach (var egg in cs.Variants[wide].Eggs.Where(e => e.Visible))
            {
                var dir = WidescreenModel.MarginDirection(egg.X, egg.Y, egg.Kind == ElementKind.XYButton);
                if (dir == 0) continue;
                // Handled when the rest of its column already follows the same margin in this variant.
                double half = WidescreenModel.Half(Aspect.Parse(wide).Ratio);
                var column = doc.Eggs.Where(o => o.Name != egg.Name && Math.Abs(o.X - egg.X) <= 2 && o.Visible &&
                    o.Kind is not (ElementKind.Screen or ElementKind.Camera or ElementKind.Background) &&
                    WidescreenModel.MarginDirection(o.X, o.Y, o.Kind == ElementKind.XYButton) == 0).ToList();
                bool handled = column.Count > 0 && column.All(o => cs.Variants[wide].Find(o.Name) is { } w && Math.Abs(w.X - (o.X + dir * half)) < 0.05);
                if (handled)
                    r.Add(new(Severity.Info, cs.Name, egg.Name, "WS_MARGIN_HANDLED", $"PreserveMargins shift of ({egg.X:0},{egg.Y:0}) is matched by its anchored column ({string.Join(", ", column.Select(c => c.Name))})", wide));
                else
                    r.Add(new(Severity.Warning, cs.Name, egg.Name, "WS_MARGIN_RULE",
                        $"at ({egg.X:0},{egg.Y:0}) the renderer's PreserveMargins mode shifts this element {(dir > 0 ? "right" : "left")} by half the extra width while its neighbours stay; quick fix: {(WidescreenModel.PointRules.Any(p => p.X == egg.X && p.Y == egg.Y) ? "nudge 1 unit in the wide variants" : "anchor its column to the same margin")}", wide));
            }
            // Text overflow inside button boxes.
            foreach (var egg in doc.Eggs.Where(e => e.TextAi?.Name == "enUITextButtonAI"))
            {
                var run = _layout.Text(egg);
                var img = _layout.Image(egg);
                if (run != null && img != null && !run.Dynamic && run.Width + (egg.TextAi!.GetInt("Text OffsetX") ?? 0) > img.Width + 4)
                    r.Add(new(Severity.Warning, cs.Name, egg.Name, "TEXT_OVERFLOW", $"label width {run.Width} exceeds the button image ({img.Width})"));
            }
        }
        foreach (var m in _layout.Assets.Missing.Distinct()) r.Add(new(Severity.Error, "*", null, "MISSING_ASSET", m) { Operation = "load resource", Fix = "pick an existing model or font" });
        return r;
    }

    /// <summary>Visible share of a hitbox's area (retail long buttons run slightly past the right edge by design).</summary>
    static double VisibleShare(UiRect h, double left, double right)
    {
        double w = Math.Max(0, Math.Min(h.X1, right) - Math.Max(h.X0, left)), hh = Math.Max(0, Math.Min(h.Y1, 480) - Math.Max(h.Y0, 0));
        return h.Width * h.Height <= 0 ? 0 : w * hh / (h.Width * h.Height);
    }

    static void CheckExtension(List<Finding> r, string screen, CompiledButton b)
    {
        var id = b.Action.Extension ?? "";
        var info = ActionCatalog.Find(id);
        bool optional = b.Action.Optional != false;
        if (!ActionCatalog.IsValidId(id))
        {
            r.Add(new(Severity.Error, screen, b.Egg, "ACTION_ID", $"'{id}' is not a valid action ID (lower-case dotted name, e.g. vehicle.paint)")
                { ElementType = b.Kind.ToString(), Operation = "bind action", Fix = "pick an action from the list" });
            return;
        }
        if (info != null && !info.IsAction)
        {
            r.Add(new(Severity.Error, screen, b.Egg, "ACTION_NOT_ACTION", $"'{id}' is a value, not an action") { Operation = "bind action", Fix = "bind it as the element's value instead" });
            return;
        }
        switch (info?.Owner)
        {
            case ActionOwner.BuiltIn:
                r.Add(new(Severity.Info, screen, b.Egg, "ACTION_BUILTIN", $"'{id}' is executed by the Menu Builder runtime")); break;
            case ActionOwner.ExtraOptions:
                r.Add(new(Severity.Info, screen, b.Egg, "ACTION_EXTRA_OPTIONS", $"'{id}' is executed by Extra Options; with the standalone runtime or Extra Options disabled the button is served disabled")); break;
            case ActionOwner.Planned when optional:
                r.Add(new(Severity.Warning, screen, b.Egg, "ACTION_NOT_IMPLEMENTED", $"'{id}' ({info.Title}) has no runtime handler yet; the button is served disabled until a module registers it")); break;
            case ActionOwner.Planned:
                r.Add(new(Severity.Error, screen, b.Egg, "ACTION_REQUIRED_MISSING", $"'{id}' is marked required but has no runtime handler")
                    { Operation = "bind action", Fix = "mark the action optional or bind an implemented action" }); break;
            default:
                if (optional) r.Add(new(Severity.Warning, screen, b.Egg, "ACTION_EXTERNAL", $"'{id}' must be registered by another module (MRMenuRegisterActionV1); until then the button is served disabled"));
                else r.Add(new(Severity.Error, screen, b.Egg, "ACTION_REQUIRED_MISSING", $"required action '{id}' is not provided by any known module")
                    { Operation = "bind action", Fix = "mark it optional or use a catalog action" });
                break;
        }
    }

    static void CheckValue(List<Finding> r, string screen, CompiledValue v)
    {
        var info = ActionCatalog.Find(v.Source);
        if (info != null && !info.HasValue)
            r.Add(new(Severity.Error, screen, v.Egg, "VALUE_NOT_VALUE", $"'{v.Source}' has no value to show") { Operation = "bind value", Fix = "pick a value source" });
        else if (info?.Owner == ActionOwner.Planned)
            r.Add(new(Severity.Warning, screen, v.Egg, "VALUE_NOT_IMPLEMENTED", $"'{v.Source}' has no provider yet; the element shows '{Compiler.FormatValue(v.Format, v.Fallback)}'"));
        else if (info == null)
            r.Add(new(Severity.Warning, screen, v.Egg, "VALUE_EXTERNAL", $"'{v.Source}' must be registered by another module (MRMenuRegisterValueV1); until then the element shows '{Compiler.FormatValue(v.Format, v.Fallback)}'"));
        if (v.Direct && v.Format != "{value}")
            r.Add(new(Severity.Warning, screen, v.Egg, "VALUE_FORMAT_IGNORED", $"'{v.Source}' is a native name shown as is; the format '{v.Format}' is not applied") { Fix = "put the caption in a separate text element" });
        else if (!v.Format.Contains("{value}")) r.Add(new(Severity.Warning, screen, v.Egg, "VALUE_FORMAT", "the format has no {value} placeholder"));
        if ((v.Format + v.Fallback).Any(c => c > '~' || c < ' '))
            r.Add(new(Severity.Error, screen, v.Egg, "VALUE_TEXT", "value format/fallback must be printable ASCII (native Name text)") { Operation = "bind value" });
    }
}
