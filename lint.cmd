@echo off
setlocal

set FIX=0
if "%~1"=="--fix" set FIX=1
if "%~1"=="-Fix" set FIX=1

echo [*] Running Ruff Check...
if %FIX%==1 (
    uv run ruff check --fix .
) else (
    uv run ruff check .
)

if %ERRORLEVEL% neq 0 (
    echo [!] Ruff Check failed.
    exit /b 1
)

echo [*] Running Ruff Format...
if %FIX%==1 (
    uv run ruff format .
) else (
    uv run ruff format --check .
)

if %ERRORLEVEL% neq 0 (
    echo [!] Ruff Format failed.
    exit /b 1
)

echo [+] All checks passed!
exit /b 0
