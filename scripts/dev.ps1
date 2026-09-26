# Start ChangeStory development environment (Backend + Frontend)
Write-Host "Starting ChangeStory Development Servers..." -ForegroundColor Cyan

$backendProcess = Start-Process -FilePath "..\venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload" -WorkingDirectory "$PSScriptRoot\..\backend" -PassThru

$frontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev" -WorkingDirectory "$PSScriptRoot\..\frontend" -PassThru

Write-Host "`nChangeStory Servers Running:" -ForegroundColor Green
Write-Host "  Backend API:  http://127.0.0.1:8000 (Docs: /docs, Health: /health)"
Write-Host "  Frontend UI:  http://localhost:3000"
Write-Host "`nPress CTRL+C or stop processes to exit."

try {
    Wait-Process -Id $backendProcess.Id, $frontendProcess.Id
} finally {
    Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendProcess.Id -ErrorAction SilentlyContinue
}
