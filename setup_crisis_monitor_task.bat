@echo off
REM ============================================================================
REM Financial Crisis Monitor - Windows Task Scheduler Setup
REM ============================================================================
REM This script creates a scheduled task to run the threat assessment every 15 minutes
REM Run this script as Administrator for proper permissions

echo.
echo ===============================================
echo Financial Crisis Monitor - Task Setup
echo ===============================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Running as Administrator - proceeding...
) else (
    echo ❌ ERROR: This script must be run as Administrator
    echo Right-click and select "Run as administrator"
    pause
    exit /b 1
)

echo.
echo 🔍 Setting up automated crisis monitoring...

REM Define variables
set TASK_NAME=Financial Crisis Monitor
set PYTHON_EXE=%~dp0.venv\Scripts\python.exe
set SCRIPT_PATH=%~dp0advanced_threat_assessment.py
set WORKING_DIR=%~dp0
set LOG_FILE=%~dp0logs\task_scheduler.log

REM Create logs directory if it doesn't exist
if not exist "%~dp0logs" mkdir "%~dp0logs"

REM Check if Python executable exists
if not exist "%PYTHON_EXE%" (
    echo ❌ ERROR: Python executable not found at %PYTHON_EXE%
    echo Please ensure your virtual environment is set up correctly
    pause
    exit /b 1
)

REM Check if script exists
if not exist "%SCRIPT_PATH%" (
    echo ❌ ERROR: Script not found at %SCRIPT_PATH%
    echo Please ensure advanced_threat_assessment.py is in the current directory
    pause
    exit /b 1
)

echo.
echo 📋 Task Configuration:
echo    Name: %TASK_NAME%
echo    Python: %PYTHON_EXE%
echo    Script: %SCRIPT_PATH%
echo    Interval: Every 15 minutes
echo    Start Time: 09:00 AM daily
echo.

REM Delete existing task if it exists
echo 🗑️  Removing any existing task...
schtasks /delete /tn "%TASK_NAME%" /f >nul 2>&1

REM Create the scheduled task
echo 🔧 Creating new scheduled task...
schtasks /create ^
    /tn "%TASK_NAME%" ^
    /tr "\"%PYTHON_EXE%\" \"%SCRIPT_PATH%\" --email-only" ^
    /sc minute ^
    /mo 15 ^
    /st 09:00 ^
    /sd 01/01/2025 ^
    /ed 12/31/2030 ^
    /ru "%USERNAME%" ^
    /f

if %errorLevel% == 0 (
    echo ✅ Task created successfully!
) else (
    echo ❌ ERROR: Failed to create task
    pause
    exit /b 1
)

REM Configure advanced task settings using PowerShell
echo 🔧 Configuring advanced settings...
powershell -Command "& {
    $task = Get-ScheduledTask -TaskName '%TASK_NAME%'
    $task.Settings.AllowStartIfOnBatteries = $true
    $task.Settings.DontStopIfGoingOnBatteries = $true
    $task.Settings.WakeToRun = $true
    $task.Settings.RestartCount = 3
    $task.Settings.RestartInterval = 'PT1M'
    $task.Settings.ExecutionTimeLimit = 'PT10M'
    $task.Settings.AllowDemandStart = $true
    $task.Settings.StartWhenAvailable = $true
    Set-ScheduledTask -InputObject $task
}"

if %errorLevel% == 0 (
    echo ✅ Advanced settings configured!
) else (
    echo ⚠️  WARNING: Some advanced settings may not be applied
)

REM Test the task
echo.
echo 🧪 Testing the task...
schtasks /run /tn "%TASK_NAME%"

if %errorLevel% == 0 (
    echo ✅ Task test started successfully!
    echo ⏱️  The threat assessment should run now...
    timeout /t 5 /nobreak >nul
) else (
    echo ❌ ERROR: Failed to start task test
)

REM Show task status
echo.
echo 📊 Task Status:
schtasks /query /tn "%TASK_NAME%" /fo table

echo.
echo ===============================================
echo Setup Complete!
echo ===============================================
echo.
echo ✅ The Financial Crisis Monitor is now scheduled to run:
echo    • Every 15 minutes during the day
echo    • Starting at 9:00 AM daily  
echo    • Will wake computer if needed
echo    • Sends email-only reports
echo.
echo 🔧 Management Commands:
echo    • View task: schtasks /query /tn "%TASK_NAME%" /fo list /v
echo    • Run now:   schtasks /run /tn "%TASK_NAME%"
echo    • Delete:    schtasks /delete /tn "%TASK_NAME%" /f
echo.
echo 📧 Email reports will be sent to your configured email address
echo 📁 Logs will be stored in: %LOG_FILE%
echo.

REM Create a management script
echo 🔧 Creating management script...
(
echo @echo off
echo REM Financial Crisis Monitor Management Script
echo.
echo echo ===============================================
echo echo Financial Crisis Monitor Management
echo echo ===============================================
echo echo.
echo echo [1] Check task status
echo echo [2] Run task now
echo echo [3] View task logs
echo echo [4] Delete task
echo echo [5] Exit
echo echo.
echo set /p choice="Select option (1-5): "
echo.
echo if "%%choice%%"=="1" (
echo     echo 📊 Task Status:
echo     schtasks /query /tn "%TASK_NAME%" /fo list /v
echo     pause
echo ^)
echo if "%%choice%%"=="2" (
echo     echo 🏃 Running task now...
echo     schtasks /run /tn "%TASK_NAME%"
echo     echo Task started!
echo     pause
echo ^)
echo if "%%choice%%"=="3" (
echo     echo 📋 Recent logs:
echo     if exist "%LOG_FILE%" (
echo         type "%LOG_FILE%"
echo     ^) else (
echo         echo No logs found yet
echo     ^)
echo     pause
echo ^)
echo if "%%choice%%"=="4" (
echo     set /p confirm="Are you sure? (y/N): "
echo     if /i "%%confirm%%"=="y" (
echo         schtasks /delete /tn "%TASK_NAME%" /f
echo         echo Task deleted!
echo     ^)
echo     pause
echo ^)
) > "%~dp0manage_crisis_monitor.bat"

echo ✅ Management script created: manage_crisis_monitor.bat
echo.

pause