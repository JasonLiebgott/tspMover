# ============================================================================
# Financial Crisis Monitor - PowerShell Task Scheduler Setup
# ============================================================================
# Enhanced setup with better error handling and configuration options
# Run as Administrator in PowerShell

param(
    [int]$IntervalMinutes = 15,
    [string]$StartTime = "09:00",
    [switch]$TestOnly,
    [switch]$Uninstall
)

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "❌ This script must be run as Administrator"
    Write-Host "Right-click PowerShell and select 'Run as Administrator'"
    exit 1
}

$TaskName = "Financial Crisis Monitor"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PythonExe = Join-Path $ScriptDir ".venv\Scripts\python.exe"
$ScriptPath = Join-Path $ScriptDir "advanced_threat_assessment.py"
$LogDir = Join-Path $ScriptDir "logs"

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Financial Crisis Monitor - PowerShell Setup" -ForegroundColor Cyan  
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Handle uninstall
if ($Uninstall) {
    Write-Host "🗑️  Uninstalling Financial Crisis Monitor..." -ForegroundColor Yellow
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Host "✅ Task uninstalled successfully!" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Task not found or already uninstalled" -ForegroundColor Red
    }
    exit 0
}

# Validate prerequisites
Write-Host "🔍 Validating prerequisites..." -ForegroundColor Yellow

if (-not (Test-Path $PythonExe)) {
    Write-Error "❌ Python executable not found: $PythonExe"
    Write-Host "Please ensure your virtual environment is set up correctly" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $ScriptPath)) {
    Write-Error "❌ Script not found: $ScriptPath"
    Write-Host "Please ensure advanced_threat_assessment.py exists" -ForegroundColor Red
    exit 1
}

# Create logs directory
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

Write-Host "✅ Prerequisites validated" -ForegroundColor Green

# Test mode - just run the script once
if ($TestOnly) {
    Write-Host ""
    Write-Host "🧪 Running test assessment..." -ForegroundColor Yellow
    try {
        & $PythonExe $ScriptPath --email-only
        Write-Host "✅ Test completed successfully!" -ForegroundColor Green
    }
    catch {
        Write-Error "❌ Test failed: $($_.Exception.Message)"
    }
    exit 0
}

Write-Host ""
Write-Host "📋 Task Configuration:" -ForegroundColor Cyan
Write-Host "   Name: $TaskName" -ForegroundColor White
Write-Host "   Python: $PythonExe" -ForegroundColor White  
Write-Host "   Script: $ScriptPath" -ForegroundColor White
Write-Host "   Interval: Every $IntervalMinutes minutes" -ForegroundColor White
Write-Host "   Start Time: $StartTime daily" -ForegroundColor White
Write-Host ""

# Remove existing task if it exists
Write-Host "🗑️  Removing any existing task..." -ForegroundColor Yellow
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
}
catch {
    # Task doesn't exist, which is fine
}

# Create the task action
$Action = New-ScheduledTaskAction -Execute $PythonExe -Argument "$ScriptPath --email-only" -WorkingDirectory $ScriptDir

# Create the task trigger (daily with repetition)
$Trigger = New-ScheduledTaskTrigger -Daily -At $StartTime
$Trigger.Repetition = New-ScheduledTaskTrigger -Once -At $StartTime -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) -RepetitionDuration (New-TimeSpan -Days 9999)

# Create task settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -WakeToRun -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -StartWhenAvailable

# Create the principal (user account to run as)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Write-Host "🔧 Creating scheduled task..." -ForegroundColor Yellow

try {
    # Register the task
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "Automated financial threat assessment monitoring system"
    
    Write-Host "✅ Task created successfully!" -ForegroundColor Green
}
catch {
    Write-Error "❌ Failed to create task: $($_.Exception.Message)"
    exit 1
}

# Test the task
Write-Host ""
Write-Host "🧪 Testing the task..." -ForegroundColor Yellow
try {
    Start-ScheduledTask -TaskName $TaskName
    Write-Host "✅ Task started successfully!" -ForegroundColor Green
    Write-Host "⏱️  The threat assessment should be running now..." -ForegroundColor Cyan
}
catch {
    Write-Warning "⚠️  Failed to start task test: $($_.Exception.Message)"
}

# Show task information
Write-Host ""
Write-Host "📊 Task Information:" -ForegroundColor Cyan
try {
    $Task = Get-ScheduledTask -TaskName $TaskName
    $TaskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
    
    Write-Host "   State: $($Task.State)" -ForegroundColor White
    Write-Host "   Last Run: $($TaskInfo.LastRunTime)" -ForegroundColor White
    Write-Host "   Last Result: $($TaskInfo.LastTaskResult)" -ForegroundColor White
    Write-Host "   Next Run: $($TaskInfo.NextRunTime)" -ForegroundColor White
}
catch {
    Write-Warning "⚠️  Could not retrieve task information"
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "✅ The Financial Crisis Monitor is now scheduled to run:" -ForegroundColor Green
Write-Host "   • Every $IntervalMinutes minutes during the day" -ForegroundColor White
Write-Host "   • Starting at $StartTime daily" -ForegroundColor White
Write-Host "   • Will wake computer if needed" -ForegroundColor White
Write-Host "   • Sends email-only reports" -ForegroundColor White
Write-Host ""
Write-Host "🔧 PowerShell Management Commands:" -ForegroundColor Cyan
Write-Host "   • View task:   Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo" -ForegroundColor White
Write-Host "   • Run now:     Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
Write-Host "   • Check logs:  Get-WinEvent -LogName 'Microsoft-Windows-TaskScheduler/Operational' | Where-Object {`$_.Message -like '*$TaskName*'}" -ForegroundColor White
Write-Host "   • Uninstall:   .\setup_crisis_monitor_task.ps1 -Uninstall" -ForegroundColor White
Write-Host ""
Write-Host "📧 Email reports will be sent to your configured email address" -ForegroundColor Cyan
Write-Host "📁 Working directory: $ScriptDir" -ForegroundColor Cyan
Write-Host ""

# Create a quick management script
$ManagementScript = @"
# Financial Crisis Monitor Management
Write-Host "Financial Crisis Monitor - Quick Management" -ForegroundColor Cyan
Write-Host ""
Write-Host "[1] Check Status    [2] Run Now    [3] View Logs    [4] Uninstall    [5] Exit"
`$choice = Read-Host "Select option"

switch (`$choice) {
    "1" { 
        Get-ScheduledTask -TaskName "$TaskName" | Get-ScheduledTaskInfo | Format-List
        pause
    }
    "2" { 
        Start-ScheduledTask -TaskName "$TaskName"
        Write-Host "Task started!" -ForegroundColor Green
        pause
    }
    "3" { 
        Get-WinEvent -LogName 'Microsoft-Windows-TaskScheduler/Operational' -MaxEvents 20 | Where-Object {`$_.Message -like '*$TaskName*'} | Format-Table TimeCreated, LevelDisplayName, Message
        pause
    }
    "4" { 
        `$confirm = Read-Host "Are you sure? (y/N)"
        if (`$confirm -eq "y") {
            Unregister-ScheduledTask -TaskName "$TaskName" -Confirm:`$false
            Write-Host "Task uninstalled!" -ForegroundColor Green
        }
        pause
    }
}
"@

$ManagementScriptPath = Join-Path $ScriptDir "manage_crisis_monitor.ps1"
$ManagementScript | Out-File -FilePath $ManagementScriptPath -Encoding UTF8

Write-Host "Quick management script created: manage_crisis_monitor.ps1" -ForegroundColor Green
Write-Host ""