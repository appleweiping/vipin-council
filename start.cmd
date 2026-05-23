@echo off
REM start.cmd — launch both backend and frontend dev server
REM Usage: start.cmd

echo.
echo   ^<^< Vipin Council ^>^>
echo.

REM Check .env
if not exist .env (
    echo   [WARN] .env not found. Copying .env.example...
    copy .env.example .env >nul
    echo   [WARN] Add your OPENROUTER_API_KEY to .env
    echo.
)

REM Start backend in new window
echo   Starting backend on http://localhost:8000 ...
start "vc-backend" cmd /k "uvicorn backend.main:app --reload --port 8000"

REM Wait a moment then start frontend
timeout /t 2 /nobreak >nul
echo   Starting frontend on http://localhost:5173 ...
start "vc-frontend" cmd /k "cd frontend && npm run dev"

echo.
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API docs: http://localhost:8000/docs
echo.
echo   CLI:  python vc.py          (one-shot)
echo   CLI:  python vc.py          (interactive REPL — no args)
echo.
