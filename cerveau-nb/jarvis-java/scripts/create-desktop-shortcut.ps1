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

$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut($Shortcut)
$sc.TargetPath = $BatLauncher
$sc.WorkingDirectory = $Root
$sc.Description = "Niam-Bay Jarvis - assistant vocal personnel"
$sc.IconLocation = "imageres.dll,168"  # icone "son" Windows
$sc.WindowStyle = 7  # minimized
$sc.Save()

Write-Host "[ok] Raccourci créé : $Shortcut"
Write-Host "     Double-clique dessus pour lancer Jarvis."
