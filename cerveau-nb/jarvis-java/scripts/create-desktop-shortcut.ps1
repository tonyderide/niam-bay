# Creates a "Niam-Bay Jarvis" shortcut on the Windows Desktop.
# Usage: .\scripts\create-desktop-shortcut.ps1
param()
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BatLauncher = Join-Path $Root "scripts\Jarvis.bat"

if (-not (Test-Path $BatLauncher)) {
    throw "Jarvis.bat introuvable : $BatLauncher"
}

$Desktop = [Environment]::GetFolderPath("Desktop")
$Shortcut = Join-Path $Desktop "Niam-Bay Jarvis.lnk"

# Delete existing shortcut first (clean recreate)
if (Test-Path $Shortcut) {
    Remove-Item $Shortcut -Force
}

$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($Shortcut)
$sc.TargetPath = $BatLauncher
$sc.WorkingDirectory = $Root
$sc.Description = "Niam-Bay Jarvis - assistant vocal personnel"
# Icone plus visible : micro (imageres 220) ou speaker (shell32 277)
$sc.IconLocation = "shell32.dll,277"
$sc.WindowStyle = 7  # minimized
$sc.Save()

# Force Explorer to refresh the desktop
$signature = @"
[DllImport("shell32.dll")]
public static extern void SHChangeNotify(int wEventId, int uFlags, IntPtr dwItem1, IntPtr dwItem2);
"@
Add-Type -MemberDefinition $signature -Namespace Win32 -Name Shell -ErrorAction SilentlyContinue
[Win32.Shell]::SHChangeNotify(0x08000000, 0, [IntPtr]::Zero, [IntPtr]::Zero)

Write-Host "[ok] Raccourci (re)crée : $Shortcut"
Write-Host "     Si toujours invisible, fais Win+D ou F5 sur le Desktop."
