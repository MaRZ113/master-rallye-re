namespace MenuBuilder.Core;

public sealed class RenderOptions
{
    public int Width { get; set; } = 1280;
    public int Height { get; set; } = 960;
    public InterfaceMode Mode { get; set; } = InterfaceMode.Stock;
    public int? FocusedId { get; set; }
    public bool ShowHitboxes { get; set; }
    public bool ShowNavigation { get; set; }
    public bool ShowSafeArea { get; set; }
    /// <summary>Draw hidden (en2d Visible=False) eggs at 35 % opacity.</summary>
    public bool GhostHidden { get; set; }
    /// <summary>Also draw eggs that the native AI keeps hidden until a state change (popups, confirmations).</summary>
    public bool ShowRuntimeHidden { get; set; }
    public uint Background { get; set; } = 0xFF000000;
}

/// <summary>
/// CPU rasterizer for frontend scenes: DXB triangles textured with the stored DXT rows, alpha blended in
/// Draw Priority order (higher value first, like the background 6 → pulser 1 stack). Coordinates go through
/// the same mapping as the D3D8 renderer's interface projection.
/// </summary>
public sealed class SceneRenderer
{
    readonly LayoutEngine _layout;
    public SceneRenderer(LayoutEngine layout) { _layout = layout; }

    public sealed class Canvas
    {
        public int W, H;
        public uint[] Px = Array.Empty<uint>();
        public double Ratio;
        public InterfaceMode Mode;
        public double Half => Mode == InterfaceMode.Stock ? 0 : WidescreenModel.Half(Ratio);
        public double VirtualWidth => Mode == InterfaceMode.Stock ? 640 : 640 + 2 * Half;
        public (double x, double y) ToPixel(double ux, double uy) => ((ux + Half) * W / VirtualWidth, (480 - uy) * H / 480.0);
        public (double x, double y) ToUi(double px, double py) => (px * VirtualWidth / W - Half, 480 - py * 480.0 / H);
    }

    public Canvas NewCanvas(RenderOptions o)
    {
        var c = new Canvas { W = o.Width, H = o.Height, Px = new uint[o.Width * o.Height], Ratio = (double)o.Width / o.Height, Mode = o.Mode };
        Array.Fill(c.Px, o.Background);
        return c;
    }

    public Canvas Render(SceneDocument doc, RenderOptions o)
    {
        var c = NewCanvas(o);
        var eggs = doc.Eggs.Select((e, i) => (e, i)).OrderByDescending(t => t.e.DrawPriority).ThenBy(t => t.i).Select(t => t.e).ToList();
        foreach (var egg in eggs)
        {
            if (!egg.UsesEn2d) continue;
            if (egg.Kind is ElementKind.Effect or ElementKind.Screen or ElementKind.Camera) continue;
            bool hidden = !egg.Visible || (!o.ShowRuntimeHidden && LayoutEngine.NativeHidden(doc, egg));
            if (hidden && !o.GhostHidden) continue;
            float alpha = hidden ? 0.35f : 1f;
            int state = LayoutEngine.State(egg, o.FocusedId);
            uint tint = state >= 2 ? 0x80E6E6E6 : 0xFFFFFFFF;
            double shift = WidescreenModel.RendererShift(o.Mode, c.Ratio, egg.X, egg.Y, egg.Kind == ElementKind.XYButton);
            DrawEgg(c, egg, shift, tint, alpha, state);
        }
        if (o.ShowSafeArea) DrawSafeArea(c);
        if (o.ShowHitboxes || o.ShowNavigation || o.FocusedId != null) DrawOverlays(c, doc, o);
        return c;
    }

    public void DrawEgg(Canvas c, Egg egg, double shift, uint tint, float alpha, int state = 0)
    {
        var img = _layout.Image(egg, state);
        if (img != null)
            foreach (var t in img.Triangles)
            {
                var tex = _layout.Assets.Texture(egg.Model, t.Texture);
                Tri(c, tex, egg.X + shift, egg.Y, egg.ScaleX, egg.ScaleY, t, 0, 0, tint, alpha);
            }
        if (_layout.Icon(egg) is { } icon)
            foreach (var t in icon.Triangles)
                Tri(c, _layout.Assets.Texture(LayoutEngine.IconBank, t.Texture), egg.X + shift, egg.Y, egg.ScaleX, egg.ScaleY, t, 4, -5, tint, alpha);
        var run = _layout.Text(egg);
        if (run?.Font != null && run.Text.Length > 0)
        {
            uint col = tint;
            var ai = egg.TextAi!;
            if (ai.Get("Colour") is { } cs)
            {
                var v = cs.Split(' ').Select(s => float.Parse(s, System.Globalization.CultureInfo.InvariantCulture)).ToArray();
                col = Pack(v[3], v[0], v[1], v[2]);
            }
            int top = int.MaxValue;
            foreach (var ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ") if (run.Font.Glyph(ch) is { } g0) top = Math.Min(top, g0.MinY);
            if (top == int.MaxValue) top = 0;
            double pen = run.LocalX;
            foreach (var ch in run.Text)
            {
                var g = run.Font.Glyph(ch) ?? run.Font.Glyph(char.ToUpperInvariant(ch));
                if (g == null) continue;
                foreach (var t in g.Triangles)
                    Tri(c, _layout.Assets.Texture(run.FontName!, t.Texture), egg.X + shift, egg.Y, egg.ScaleX, egg.ScaleY, t, pen - g.MinX, run.LocalY - top, col, alpha);
                pen += g.Width;
            }
        }
    }

    static uint Pack(float a, float r, float g, float b) =>
        ((uint)(Math.Clamp(a, 0, 1) * 255) << 24) | ((uint)(Math.Clamp(r, 0, 1) * 255) << 16) | ((uint)(Math.Clamp(g, 0, 1) * 255) << 8) | (uint)(Math.Clamp(b, 0, 1) * 255);

    void Tri(Canvas c, DxtTexture? tex, double ex, double ey, double sx, double sy, DxbTriangle t, double lx, double ly, uint tint, float alpha)
    {
        // Local DXB (y down) → authored (y up) → pixel.
        var p0 = c.ToPixel(ex + sx * (t.X0 + lx), ey - sy * (t.Y0 + ly));
        var p1 = c.ToPixel(ex + sx * (t.X1 + lx), ey - sy * (t.Y1 + ly));
        var p2 = c.ToPixel(ex + sx * (t.X2 + lx), ey - sy * (t.Y2 + ly));
        double area = (p1.x - p0.x) * (p2.y - p0.y) - (p2.x - p0.x) * (p1.y - p0.y);
        if (Math.Abs(area) < 1e-9) return;
        int minX = Math.Max(0, (int)Math.Floor(Math.Min(p0.x, Math.Min(p1.x, p2.x))));
        int maxX = Math.Min(c.W - 1, (int)Math.Ceiling(Math.Max(p0.x, Math.Max(p1.x, p2.x))));
        int minY = Math.Max(0, (int)Math.Floor(Math.Min(p0.y, Math.Min(p1.y, p2.y))));
        int maxY = Math.Min(c.H - 1, (int)Math.Ceiling(Math.Max(p0.y, Math.Max(p1.y, p2.y))));
        float ta = ((tint >> 24) & 255) / 255f * alpha, tr = ((tint >> 16) & 255) / 255f, tg = ((tint >> 8) & 255) / 255f, tb = (tint & 255) / 255f;
        for (int y = minY; y <= maxY; y++)
        {
            double py = y + 0.5;
            for (int x = minX; x <= maxX; x++)
            {
                double px = x + 0.5;
                double w0 = ((p1.x - px) * (p2.y - py) - (p2.x - px) * (p1.y - py)) / area;
                double w1 = ((p2.x - px) * (p0.y - py) - (p0.x - px) * (p2.y - py)) / area;
                double w2 = 1 - w0 - w1;
                if (w0 < -1e-6 || w1 < -1e-6 || w2 < -1e-6) continue;
                float u = (float)(w0 * t.U0 + w1 * t.U1 + w2 * t.U2), v = (float)(w0 * t.V0 + w1 * t.V1 + w2 * t.V2);
                uint s = tex?.Sample(u, v) ?? 0xFFFF00FF;
                float sa = ((s >> 24) & 255) / 255f * ta;
                if (sa <= 0.002f) continue;
                float sr = ((s >> 16) & 255) * tr, sg = ((s >> 8) & 255) * tg, sb = (s & 255) * tb;
                ref uint d = ref c.Px[y * c.W + x];
                float dr = (d >> 16) & 255, dg = (d >> 8) & 255, db = d & 255;
                uint r = (uint)(sr * sa + dr * (1 - sa)), g = (uint)(sg * sa + dg * (1 - sa)), b = (uint)(sb * sa + db * (1 - sa));
                d = 0xFF000000 | (Math.Min(r, 255u) << 16) | (Math.Min(g, 255u) << 8) | Math.Min(b, 255u);
            }
        }
    }

    public static void Rect(Canvas c, double x0, double y0, double x1, double y1, uint color, bool fill = false)
    {
        int ix0 = (int)Math.Max(0, Math.Min(x0, x1)), ix1 = (int)Math.Min(c.W - 1, Math.Max(x0, x1));
        int iy0 = (int)Math.Max(0, Math.Min(y0, y1)), iy1 = (int)Math.Min(c.H - 1, Math.Max(y0, y1));
        for (int y = iy0; y <= iy1; y++)
            for (int x = ix0; x <= ix1; x++)
                if (fill || y == iy0 || y == iy1 || x == ix0 || x == ix1) Blend(c, x, y, color);
    }

    static void Blend(Canvas c, int x, int y, uint color)
    {
        float a = ((color >> 24) & 255) / 255f;
        ref uint d = ref c.Px[y * c.W + x];
        uint r = (uint)(((color >> 16) & 255) * a + ((d >> 16) & 255) * (1 - a));
        uint g = (uint)(((color >> 8) & 255) * a + ((d >> 8) & 255) * (1 - a));
        uint b = (uint)((color & 255) * a + (d & 255) * (1 - a));
        d = 0xFF000000 | (r << 16) | (g << 8) | b;
    }

    public static void Line(Canvas c, double x0, double y0, double x1, double y1, uint color)
    {
        int n = (int)Math.Max(Math.Abs(x1 - x0), Math.Abs(y1 - y0)) + 1;
        for (int i = 0; i <= n; i++)
        {
            int x = (int)(x0 + (x1 - x0) * i / n), y = (int)(y0 + (y1 - y0) * i / n);
            if (x >= 0 && y >= 0 && x < c.W && y < c.H) Blend(c, x, y, color);
        }
    }

    void DrawSafeArea(Canvas c)
    {
        // 4:3 authored frame and a 5 % title-safe inset.
        var a = c.ToPixel(0, 0); var b = c.ToPixel(640, 480);
        Rect(c, a.x, b.y, b.x, a.y, 0xC000C8FF);
        var s0 = c.ToPixel(32, 24); var s1 = c.ToPixel(608, 456);
        Rect(c, s0.x, s1.y, s1.x, s0.y, 0x8000FF80);
    }

    void DrawOverlays(Canvas c, SceneDocument doc, RenderOptions o)
    {
        var focus = doc.Focusables.ToList();
        foreach (var egg in focus)
        {
            var hb = _layout.Hitbox(doc.VisualOf(egg));
            double shift = WidescreenModel.RendererShift(o.Mode, c.Ratio, egg.X, egg.Y, egg.Kind == ElementKind.XYButton);
            hb = hb.Offset(shift, 0);
            var a = c.ToPixel(hb.X0, hb.Y0); var b = c.ToPixel(hb.X1, hb.Y1);
            if (o.ShowHitboxes) Rect(c, a.x, b.y, b.x, a.y, 0xA0FF3030);
            if (o.FocusedId is int fid && egg.ButtonId == fid) { Rect(c, a.x - 2, b.y - 2, b.x + 2, a.y + 2, 0xFFFFD000); Rect(c, a.x - 3, b.y - 3, b.x + 3, a.y + 3, 0xFFFFD000); }
        }
        if (!o.ShowNavigation) return;
        foreach (var egg in focus)
        {
            var f = egg.Focusable!;
            var from = _layout.Hitbox(doc.VisualOf(egg));
            foreach (var (path, color) in new[] { ("Up Path", 0xFF40C0FFu), ("Down Path", 0xFF40FF80u), ("Left Path", 0xFFFFA040u), ("Right Path", 0xFFFF60D0u) })
            {
                int t = f.GetInt(path) ?? 0;
                if (t == 0) continue;
                var to = focus.FirstOrDefault(e => e.ButtonId == t);
                if (to == null) continue;
                var tr = _layout.Hitbox(doc.VisualOf(to));
                var p = c.ToPixel((from.X0 + from.X1) / 2, (from.Y0 + from.Y1) / 2);
                var q = c.ToPixel((tr.X0 + tr.X1) / 2, (tr.Y0 + tr.Y1) / 2);
                double off = path[0] switch { 'U' => -6, 'D' => 6, 'L' => -3, _ => 3 };
                Line(c, p.x + off, p.y, q.x + off, q.y, color);
                Rect(c, q.x + off - 2, q.y - 2, q.x + off + 2, q.y + 2, color, true);
            }
        }
    }
}
