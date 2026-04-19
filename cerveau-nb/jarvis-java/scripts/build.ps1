param()
$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Out = Join-Path $Root "out"

Write-Host "[build] javac..."
New-Item -ItemType Directory -Path $Out -Force | Out-Null
$srcs = @(
    (Join-Path $Root "src\main\java\niambay\Jarvis.java"),
    (Join-Path $Root "src\main\java\niambay\JarvisUI.java")
)
& javac -d $Out @srcs
if ($LASTEXITCODE -ne 0) { throw "javac failed" }

Write-Host "[build] packaging jar..."
$Manifest = Join-Path $Out "MANIFEST.MF"
@"
Manifest-Version: 1.0
Main-Class: niambay.Jarvis

"@ | Out-File -FilePath $Manifest -Encoding ascii -NoNewline

Push-Location $Out
try {
    & jar cfm (Join-Path $Root "jarvis.jar") "MANIFEST.MF" "niambay"
    if ($LASTEXITCODE -ne 0) { throw "jar failed" }
} finally { Pop-Location }

Write-Host "[build] OK -> $(Join-Path $Root 'jarvis.jar')"
Write-Host "Usage: java -jar (Join-Path $Root jarvis.jar) [--text|--once 'question'|--wake-word]"
