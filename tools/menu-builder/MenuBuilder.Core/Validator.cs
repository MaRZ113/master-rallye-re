namespace MenuBuilder.Core;

public enum Severity { Info, Warning, Error }

public sealed record Finding(Severity Severity, string Screen, string? Element, string Code, string Message, string? Aspect = null)
{
    public override string ToString() => $"{Severity.ToString().ToUpperInvariant()} {Screen}{(Element != null ? "/" + Element : "")}{(Aspect != null ? " [" + Aspect + "]" : "")} {Code}: {Message}";
}

/// <summary>
/// Checks a compiled layout against the native rules: navigation graph, typed bindings,
/// hitbox ⇔ visual identity, aspect visibility and the renderer's PreserveMargins rules.
/// </summary>
public sealed class Validator
{
    readonly LayoutEngine _layout;
    readonly ExeTables? _exe;
    public HashSet<string> KnownExtensions { get; } = new(StringComparer.Ordinal) { "extra_options.model_source", "game.quit" };

    public Validator(LayoutEngine layout, ExeTables? exe) { _layout = layout; _exe = exe; }

    public List<Finding> Validate(MenuProject project, CompiledLayout compiled)
    {
        var r = new List<Finding>();
        if (_exe != null && !_exe.IsRetail) r.Add(new(Severity.Warning, "*", null, "EXE_NOT_RETAIL", $"MRallye.exe {_exe.Sha256[..12]}… is not the certified retail image; native addresses are only verified for retail"));
        foreach (var cs in compiled.Screens)
        {
            var def = project.Screen(cs.Name)!;
            foreach (var n in cs.Notes) r.Add(new(Severity.Warning, cs.Name, null, "BUILD", n));
            if (!cs.IsCustom && cs.NativeId < 0) r.Add(new(Severity.Error, cs.Name, null, "UNKNOWN_SCREEN", $"{cs.Base} is not in the native screen table"));
            if (cs.BaseSource == "loose") r.Add(new(Severity.Info, cs.Name, null, "BASE_LOOSE", $"base page comes from a loose file of another mod (sha {cs.BaseSha256[..12]}…); the delta is applied on top of it"));
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
            foreach (var b in cs.Buttons)
            {
                foreach (var (dir, target) in new[] { ("Up", b.Up), ("Down", b.Down), ("Left", b.Left), ("Right", b.Right) })
                    if (target != 0 && !ids.Contains(target))
                        r.Add(new(Severity.Error, cs.Name, b.Egg, "NAV_TARGET", $"{dir} Path → {target} does not exist"));
                switch (b.Status)
                {
                    case BindingStatus.Unbound:
                        r.Add(new(Severity.Error, cs.Name, b.Egg, "UNBOUND", "focusable without a working handler (not a retail command of this screen and no typed action)")); break;
                    case BindingStatus.Extension:
                        var ext = b.Action.Extension ?? "";
                        r.Add(KnownExtensions.Contains(ext)
                            ? new(Severity.Info, cs.Name, b.Egg, "EXTENSION", $"provider '{ext}' is built into the runtime; it reports UNAVAILABLE when its owner (e.g. Extra Options) is disabled")
                            : new(Severity.Warning, cs.Name, b.Egg, "EXTENSION_EXTERNAL", $"provider '{ext}' must be registered by another module via MRMenuRegisterActionV1; until then the button is shown disabled in game"));
                        break;
                    case BindingStatus.Disabled:
                        r.Add(new(Severity.Info, cs.Name, b.Egg, "DISABLED", "action 'none': the button is shown disabled")); break;
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
                if ((b.Action.Type is ActionBinding.SetInt or ActionBinding.ToggleBool or ActionBinding.CycleInt) && string.IsNullOrWhiteSpace(b.Action.Key))
                    r.Add(new(Severity.Error, cs.Name, b.Egg, "BROKER_KEY", "Broker action without key"));
                if (b.Local.IsEmpty)
                    r.Add(new(Severity.Error, cs.Name, b.Egg, "NO_HITBOX", "focusable has neither a sprite nor text; it cannot be drawn or hit"));
            }
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
        foreach (var m in _layout.Assets.Missing.Distinct()) r.Add(new(Severity.Error, "*", null, "MISSING_ASSET", m));
        return r;
    }
}
