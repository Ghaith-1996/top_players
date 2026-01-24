$env:DATABASE_URL="sqlite:///./top_players.db"

Write-Host "Starting Backend on Port 8000..."
Start-Process -FilePath ".\venv\Scripts\uvicorn" -ArgumentList "api.index:app --reload --port 8000" -NoNewWindow

Write-Host "Starting Frontend..."
Set-Location web
npm run dev
