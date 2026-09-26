param(
    [string]$Scenario = "a"
)

$diffFile = "fixtures\diffs\scenario_$Scenario.diff"
if (-not (Test-Path $diffFile)) {
    Write-Host "Scenario $Scenario diff file not found at $diffFile" -ForegroundColor Red
    exit 1
}

Write-Host "Running ChangeStory Analysis on Scenario $Scenario ($diffFile)..." -ForegroundColor Cyan
.\venv\Scripts\changestory.exe analyze --diff-file $diffFile --no-browser
