#!/usr/bin/env bash
set -e

FIX=0
if [ "$1" = "--fix" ] || [ "$1" = "-Fix" ]; then
    FIX=1
fi

echo "[*] Running Ruff Check..."
if [ $FIX -eq 1 ]; then
    uv run ruff check --fix .
else
    uv run ruff check .
fi

if [ $? -ne 0 ]; then
    echo "[!] Ruff Check failed."
    exit 1
fi

echo "[*] Running Ruff Format..."
if [ $FIX -eq 1 ]; then
    uv run ruff format .
else
    uv run ruff format --check .
fi

if [ $? -ne 0 ]; then
    echo "[!] Ruff Format failed."
    exit 1
fi

echo "[+] All checks passed!"
exit 0
