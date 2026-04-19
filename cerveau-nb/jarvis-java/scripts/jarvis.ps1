param(
    [switch]$Text,
    [switch]$WakeWord,
    [string]$Once,
    [switch]$Build
)
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Jar = Join-Path $Root "jarvis.jar"

if ($Build -or -not (Test-Path $Jar)) {
    Write-Host "[jarvis] building..."
    & (Join-Path $PSScriptRoot "build.ps1")
}

$javaArgs = @("-jar", $Jar)
if ($Text) { $javaArgs += "--text" }
if ($WakeWord) { $javaArgs += "--wake-word" }
if ($Once) { $javaArgs += "--once"; $javaArgs += $Once }

Write-Host "[jarvis] java $javaArgs"
& java @javaArgs
