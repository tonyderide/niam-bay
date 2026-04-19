param([Parameter(Mandatory=$true)][string]$File)
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('Microsoft Hortense Desktop')
$s.Volume = 100
$s.Rate = 0

$text = Get-Content -Path $File -Raw -Encoding UTF8
$blocs = $text -split "(?m)^\s*$" | Where-Object { $_.Trim() -ne "" }

foreach ($b in $blocs) {
    $clean = $b.Trim()
    Write-Host "  >> $clean"
    $s.Speak($clean)
    Start-Sleep -Milliseconds 400
}
