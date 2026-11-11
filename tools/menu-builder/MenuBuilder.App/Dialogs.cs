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

    /// <summary>
    /// Message with a choice of buttons; returns the index of the pressed button, or -1 when the window was closed
    /// (treated as Cancel). The last button is the Cancel button (Esc).
    /// </summary>
    public static int Choice(Window owner, string title, string message, string? details, params string[] buttons)
    {
        var panel = new StackPanel { Margin = new Thickness(14), MaxWidth = 720 };
        panel.Children.Add(new TextBlock { Text = message, TextWrapping = TextWrapping.Wrap, FontWeight = FontWeights.SemiBold });
        if (!string.IsNullOrEmpty(details))
            panel.Children.Add(new TextBox
            {
                Text = details, IsReadOnly = true, TextWrapping = TextWrapping.Wrap, Margin = new Thickness(0, 8, 0, 0), MaxHeight = 320,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto, FontFamily = new System.Windows.Media.FontFamily("Consolas"), FontSize = 12,
            });
        var row = new StackPanel { Orientation = Orientation.Horizontal, HorizontalAlignment = HorizontalAlignment.Right, Margin = new Thickness(0, 12, 0, 0) };
        panel.Children.Add(row);
        var w = new Window { Title = title, Owner = owner, Content = panel, SizeToContent = SizeToContent.WidthAndHeight, WindowStartupLocation = WindowStartupLocation.CenterOwner, ResizeMode = ResizeMode.NoResize, MinWidth = 380 };
        int result = -1;
        for (int i = 0; i < buttons.Length; i++)
        {
            int index = i;
            var b = new Button { Content = buttons[i], MinWidth = 90, Padding = new Thickness(10, 2, 10, 2), Margin = new Thickness(4), IsDefault = i == 0, IsCancel = i == buttons.Length - 1 };
            b.Click += (_, _) => { result = index; w.DialogResult = true; };
            row.Children.Add(b);
        }
        w.ShowDialog();
        return result;
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
