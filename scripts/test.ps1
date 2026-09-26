Write-Host "Running ChangeStory Test Suites..." -ForegroundColor Cyan

Write-Host "`n1. Running Backend Unit, Integration, and Security Tests:" -ForegroundColor Yellow
Push-Location backend
..\venv\Scripts\python.exe -m pytest tests -v
$backendResult = $LASTEXITCODE
Pop-Location

Write-Host "`n2. Running Sample Project Test Suite:" -ForegroundColor Yellow
$env:PYTHONPATH = "sample-project"
.\venv\Scripts\python.exe -m pytest sample-project\tests -v
$sampleResult = $LASTEXITCODE

if ($backendResult -eq 0 -and $sampleResult -eq 0) {
    Write-Host "`nAll ChangeStory tests PASSED successfully!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`nSome tests failed." -ForegroundColor Red
    exit 1
}
