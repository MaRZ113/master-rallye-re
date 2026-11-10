<#
  Menu Builder runtime verification driver (Windows PowerShell 5.1).
  Drives a running MRallye.exe window: screenshots of the client area, DirectInput-compatible scan-code
  key presses and mouse moves/clicks at authored UI coordinates. Used by run_runtime_check.ps1; it never
  touches game files.

  mrdrive.ps1 shot <out.png>
  mrdrive.ps1 key <Up|Down|Left|Right|Enter|Escape> [count]
  mrdrive.ps1 click <ux> <uy> [mode] [right]     # authored 640x480 UI coordinates (y up); mode 0 stock, 1/2 widened
  mrdrive.ps1 move <ux> <uy> [mode]
  mrdrive.ps1 info
#>
param([string]$Command, [string]$A1, [string]$A2, [string]$A3, [string]$A4)
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class MrDrive {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
  [StructLayout(LayoutKind.Sequential)] public struct KEYBDINPUT { public ushort wVk; public ushort wScan; public uint dwFlags; public uint time; public IntPtr extra; }
  [StructLayout(LayoutKind.Sequential)] public struct INPUT { public uint type; public KEYBDINPUT ki; public long pad; }
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, int dx, int dy, uint d, IntPtr e);
  [DllImport("user32.dll")] public static extern uint SendInput(uint n, INPUT[] i, int size);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc p, IntPtr l);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  public static IntPtr LargestWindow(uint pid) {
    IntPtr best = IntPtr.Zero; long area = 0;
    EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p); RECT r;
      if (p == pid && IsWindowVisible(h) && GetClientRect(h, out r) && (long)r.R * r.B > area) { area = (long)r.R * r.B; best = h; }
      return true; }, IntPtr.Zero);
    return best;
  }
  public static void Key(ushort scan, bool extended) {
    var down = new INPUT { type = 1, ki = new KEYBDINPUT { wScan = scan, dwFlags = 8u | (extended ? 1u : 0u) } };
    var up = new INPUT { type = 1, ki = new KEYBDINPUT { wScan = scan, dwFlags = 8u | 2u | (extended ? 1u : 0u) } };
    SendInput(1, new[] { down }, Marshal.SizeOf(typeof(INPUT)));
    System.Threading.Thread.Sleep(90);
    SendInput(1, new[] { up }, Marshal.SizeOf(typeof(INPUT)));
  }
}
"@
[void][MrDrive]::SetProcessDPIAware()
$proc = Get-Process MRallye -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $proc) { Write-Output "NO_GAME_WINDOW"; exit 2 }
# Several wsUIWindow windows exist (game, renderer presentation, debug): use the largest visible client.
$h = [MrDrive]::LargestWindow([uint32]$proc.Id)
if ($h -eq [IntPtr]::Zero) { Write-Output "NO_GAME_WINDOW"; exit 2 }
$r = New-Object MrDrive+RECT; [void][MrDrive]::GetClientRect($h, [ref]$r)
$origin = New-Object MrDrive+POINT; [void][MrDrive]::ClientToScreen($h, [ref]$origin)
$w = $r.R; $hgt = $r.B

function ToScreen([double]$ux, [double]$uy, [int]$mode) {
  $vw = 640.0; $half = 0.0
  if ($mode -ne 0) { $vw = 480.0 * $w / $hgt; $half = ($vw - 640.0) / 2.0 }
  $px = ($ux + $half) * $w / $vw; $py = (480.0 - $uy) * $hgt / 480.0
  return @([int]($origin.X + $px), [int]($origin.Y + $py))
}

switch ($Command) {
  "info" { Write-Output "pid=$($proc.Id) client=${w}x${hgt} origin=$($origin.X),$($origin.Y)" }
  "shot" {
    # DWM capture (PW_RENDERFULLCONTENT): works while the window is covered; never steals focus.
    $wr = New-Object MrDrive+RECT; [void][MrDrive]::GetWindowRect($h, [ref]$wr)
    $ww = $wr.R - $wr.L; $wh = $wr.B - $wr.T
    $full = New-Object System.Drawing.Bitmap $ww, $wh
    $g = [System.Drawing.Graphics]::FromImage($full); $hdc = $g.GetHdc()
    $ok = $false
    for ($try = 0; $try -lt 8; $try++) {
      $ok = [MrDrive]::PrintWindow($h, $hdc, 2)
      # DWM can hand back an empty (uniform) surface while the D3D frame is being replaced: retry.
      $g.ReleaseHdc($hdc)
      $c1 = $full.GetPixel([int]($ww / 3), [int]($wh / 3)); $c2 = $full.GetPixel([int]($ww / 2), [int]($wh / 2)); $c3 = $full.GetPixel([int]($ww * 2 / 3), [int]($wh * 3 / 4))
      if (-not ($c1.ToArgb() -eq $c2.ToArgb() -and $c2.ToArgb() -eq $c3.ToArgb())) { break }
      Start-Sleep -Milliseconds 250; $hdc = $g.GetHdc()
    }
    $g.Dispose()
    $crop = $full.Clone((New-Object System.Drawing.Rectangle ($origin.X - $wr.L), ($origin.Y - $wr.T), $w, $hgt), $full.PixelFormat)
    $crop.Save($A1, [System.Drawing.Imaging.ImageFormat]::Png); $crop.Dispose(); $full.Dispose()
    Write-Output "SHOT $A1 ${w}x${hgt} printwindow=$ok"
  }
  "key" {
    [void][MrDrive]::SetForegroundWindow($h); Start-Sleep -Milliseconds 150
    $map = @{ Up = @(0x48, $true); Down = @(0x50, $true); Left = @(0x4B, $true); Right = @(0x4D, $true); Enter = @(0x1C, $false); Escape = @(0x01, $false) }
    $k = $map[$A1]; $n = if ($A2) { [int]$A2 } else { 1 }
    for ($i = 0; $i -lt $n; $i++) { [MrDrive]::Key([uint16]$k[0], [bool]$k[1]); Start-Sleep -Milliseconds 350 }
    Write-Output "KEY $A1 x$n"
  }
  { $_ -in "click", "move" } {
    [void][MrDrive]::SetForegroundWindow($h); Start-Sleep -Milliseconds 150
    $mode = if ($A3) { [int]$A3 } else { 0 }
    $p = ToScreen ([double]$A1) ([double]$A2) $mode
    [void][MrDrive]::SetCursorPos($p[0] - 3, $p[1]); Start-Sleep -Milliseconds 120
    [void][MrDrive]::SetCursorPos($p[0], $p[1]); Start-Sleep -Milliseconds 250
    if ($Command -eq "click") {
      if ($A4 -eq "right") { [MrDrive]::mouse_event(0x0008, 0, 0, 0, [IntPtr]::Zero); Start-Sleep -Milliseconds 120; [MrDrive]::mouse_event(0x0010, 0, 0, 0, [IntPtr]::Zero) }
      else { [MrDrive]::mouse_event(0x0002, 0, 0, 0, [IntPtr]::Zero); Start-Sleep -Milliseconds 120; [MrDrive]::mouse_event(0x0004, 0, 0, 0, [IntPtr]::Zero) }
    }
    Write-Output "$($Command.ToUpper()) ui=($A1,$A2) screen=($($p[0]),$($p[1]))"
  }
  default { Write-Output "usage: shot|key|click|move|info"; exit 1 }
}
