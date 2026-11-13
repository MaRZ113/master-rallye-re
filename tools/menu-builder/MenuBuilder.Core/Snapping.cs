namespace MenuBuilder.Core;

/// <summary>A guide line shown while snapping: vertical (x = Pos) or horizontal (y = Pos), spanning From..To.</summary>
public readonly record struct SnapGuide(bool Vertical, double Pos, double From, double To);

public sealed record SnapResult(double Dx, double Dy, List<SnapGuide> Guides, bool SnappedX, bool SnappedY);

/// <summary>
/// Smart guides in the spirit of image editors: the moving box's left/centre/right and bottom/middle/top lines snap to
/// the same lines of the other elements and to the screen's edges and centre when they come within a threshold
/// (in authored units). Grid snapping is applied separately by the editor and only when no guide matched.
/// </summary>
public static class Snapper
{
    static IEnumerable<double> Xs(UiRect r) { yield return r.X0; yield return (r.X0 + r.X1) / 2; yield return r.X1; }
    static IEnumerable<double> Ys(UiRect r) { yield return r.Y0; yield return (r.Y0 + r.Y1) / 2; yield return r.Y1; }

    /// <param name="moving">Box at its original position (before the drag).</param>
    /// <param name="dx">Proposed horizontal offset.</param>
    /// <param name="dy">Proposed vertical offset.</param>
    /// <param name="targets">Boxes of the other (non-moving) elements.</param>
    /// <param name="screen">Screen area whose edges and centre are targets too (visible area of the current view).</param>
    public static SnapResult Move(UiRect moving, double dx, double dy, IReadOnlyCollection<UiRect> targets, UiRect screen, double threshold)
    {
        var all = targets.Append(screen).ToList();
        var m = moving.Offset(dx, dy);
        var (bx, sx) = Best(Xs(m).ToArray(), all.SelectMany(Xs), threshold);
        var (by, sy) = Best(Ys(m).ToArray(), all.SelectMany(Ys), threshold);
        if (sx) dx += bx;
        if (sy) dy += by;
        var final = moving.Offset(dx, dy);
        return new SnapResult(dx, dy, Guides(final, all, sx, sy), sx, sy);
    }

    /// <summary>Snaps the dragged edges of a box being resized. <paramref name="edgesX"/>/<paramref name="edgesY"/> hold
    /// the current coordinates of the edges that move (empty when the axis does not change).</summary>
    public static (double ddx, double ddy, List<SnapGuide> guides) Edges(UiRect box, double[] edgesX, double[] edgesY, IReadOnlyCollection<UiRect> targets, UiRect screen, double threshold)
    {
        var all = targets.Append(screen).ToList();
        var (bx, sx) = Best(edgesX, all.SelectMany(Xs), threshold);
        var (by, sy) = Best(edgesY, all.SelectMany(Ys), threshold);
        var guides = new List<SnapGuide>();
        if (sx) foreach (var e in edgesX) guides.AddRange(Lines(true, e + bx, box, all));
        if (sy) foreach (var e in edgesY) guides.AddRange(Lines(false, e + by, box, all));
        return (sx ? bx : 0, sy ? by : 0, guides);
    }

    static (double delta, bool ok) Best(double[] mine, IEnumerable<double> theirs, double threshold)
    {
        double best = double.MaxValue;
        foreach (var t in theirs)
            foreach (var v in mine)
            {
                var d = t - v;
                if (Math.Abs(d) <= threshold && Math.Abs(d) < Math.Abs(best)) best = d;
            }
        return best == double.MaxValue ? (0, false) : (best, true);
    }

    static List<SnapGuide> Guides(UiRect box, List<UiRect> all, bool x, bool y)
    {
        var g = new List<SnapGuide>();
        if (x) foreach (var v in Xs(box)) g.AddRange(Lines(true, v, box, all));
        if (y) foreach (var v in Ys(box)) g.AddRange(Lines(false, v, box, all));
        return g;
    }

    /// <summary>One guide per aligned line, spanning the moving box and every target that shares the line.</summary>
    static IEnumerable<SnapGuide> Lines(bool vertical, double pos, UiRect box, List<UiRect> all)
    {
        var hits = all.Where(r => (vertical ? Xs(r) : Ys(r)).Any(v => Math.Abs(v - pos) < 0.01)).ToList();
        if (hits.Count == 0) yield break;
        var span = hits.Aggregate(box, (a, r) => a.Union(r));
        yield return vertical ? new SnapGuide(true, pos, span.Y0, span.Y1) : new SnapGuide(false, pos, span.X0, span.X1);
    }
}
