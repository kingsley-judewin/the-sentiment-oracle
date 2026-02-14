# Start Backend Server
Write-Host "Starting Sentiment Oracle Backend..." -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

Set-Location "d:\sentiment oracle\python-engine"
python -m app.main
