@echo off
rem Runs a hook script with a Python that actually works, for agents on Windows
rem that do not run their hooks through `sh`.
rem
rem   cmd /c run.cmd path\to\hook.py
rem
rem Each candidate is tried before it is used: on Windows `python3` is often a
rem shortcut to the Store that runs nothing. With no working Python it exits 0
rem in silence, because a hook must never fail a session.
setlocal enabledelayedexpansion
rem The agent sends and reads UTF-8. Without this, Python would use the old
rem Windows encoding and misread every character outside plain English.
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
for %%P in (py python python3) do (
  %%P -c "import sys" >nul 2>&1
  if not errorlevel 1 (
    %%P %*
    exit /b !ERRORLEVEL!
  )
)
exit /b 0
