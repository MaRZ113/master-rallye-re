using System.Windows;
using System.Windows.Controls;

namespace MenuBuilder.App;

/// <summary>Small modal helpers (text prompt, list picker) built in code.</summary>
public static class Dialogs
{
    static Window Frame(Window owner, string title, UIElement content, out Button ok)
    {
        var panel = new StackPanel { Margin = new Thickness(12) };
        panel.Children.Add(content);
        var buttons = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 10, 0, 0) };
        ok = new Button { Content = "OK", Width = 80, IsDefault = true, Margin = new Thickness(4) };
        var cancel = new Button { Content = "Cancel", Width = 80, IsCancel = true, Margin = new Thickness(4) };
        buttons.Children.Add(ok); buttons.Children.Add(cancel);
        panel.Children.Add(buttons);
        var w = new Window { Title = title, Owner = owner, Content = panel, SizeToContent = SizeToContent.WidthAndHeight, WindowStartupLocation = WindowStartupLocation.CenterOwner, ResizeMode = ResizeMode.NoResize, MinWidth = 360 };
        ok.Click += (_, _) => { w.DialogResult = true; };
        return w;
    }

    public static string? Prompt(Window owner, string title, string label, string value = "")
    {
        var box = new TextBox { Text = value, MinWidth = 320, Margin = new Thickness(0, 4, 0, 0) };
        var content = new StackPanel();
        content.Children.Add(new TextBlock { Text = label });
        content.Children.Add(box);
        var w = Frame(owner, title, content, out _);
        w.Loaded += (_, _) => { box.Focus(); box.SelectAll(); };
        return w.ShowDialog() == true ? box.Text.Trim() : null;
    }

    public static string? Pick(Window owner, string title, string label, IEnumerable<string> items, string? selected = null)
    {
        var list = new ListBox { MinWidth = 320, Height = 320, Margin = new Thickness(0, 4, 0, 0) };
        foreach (var i in items) list.Items.Add(i);
        if (selected != null) list.SelectedItem = selected;
        var content = new StackPanel();
        content.Children.Add(new TextBlock { Text = label });
        content.Children.Add(list);
        var w = Frame(owner, title, content, out _);
        list.MouseDoubleClick += (_, _) => { if (list.SelectedItem != null) w.DialogResult = true; };
        return w.ShowDialog() == true ? list.SelectedItem as string : null;
    }

    /// <summary>Several labelled text fields; returns null on cancel.</summary>
    public static string[]? Form(Window owner, string title, params (string label, string value)[] fields)
    {
        var content = new StackPanel();
        var boxes = new List<TextBox>();
        foreach (var (label, value) in fields)
        {
            content.Children.Add(new TextBlock { Text = label, Margin = new Thickness(0, 6, 0, 0) });
            var b = new TextBox { Text = value, MinWidth = 320 };
            boxes.Add(b); content.Children.Add(b);
        }
        var w = Frame(owner, title, content, out _);
        w.Loaded += (_, _) => boxes.FirstOrDefault()?.Focus();
        return w.ShowDialog() == true ? boxes.Select(b => b.Text.Trim()).ToArray() : null;
    }
}
