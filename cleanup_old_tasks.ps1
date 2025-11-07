# ============================================================================
# Cleanup Old Crisis Monitor Tasks - Run as Administrator
# ============================================================================
# This script removes the old scheduled tasks and keeps only the new dual email system

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "❌ This script must be run as Administrator"
    Write-Host "Right-click PowerShell and select 'Run as Administrator'"
    pause
    exit 1
}

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "Crisis Monitor Task Cleanup" -ForegroundColor Cyan  
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# List all current crisis/finance related tasks
Write-Host "Current Crisis/Finance Tasks:" -ForegroundColor Yellow
Get-ScheduledTask | Where-Object {$_.TaskName -like "*Crisis*" -or $_.TaskName -like "*Finance*"} | Format-Table TaskName, State, LastRunTime

Write-Host ""

# Tasks to keep (NEW dual email system)
$TasksToKeep = @(
    "Dual Email Crisis Monitor",
    "Daily Finance Report"
)

# Tasks to remove (OLD systems)
$TasksToRemove = @(
    "Financial Crisis Monitor",
    "Enhanced Crisis Monitor v2"
)

Write-Host "Removing Old Tasks:" -ForegroundColor Yellow
foreach ($TaskName in $TasksToRemove) {
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            Write-Host "   Removing: $TaskName" -ForegroundColor Red
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
            Write-Host "   Removed: $TaskName" -ForegroundColor Green
        } else {
            Write-Host "   Not found: $TaskName" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "   Failed to remove: $TaskName - $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Keeping New Dual Email System:" -ForegroundColor Green
foreach ($TaskName in $TasksToKeep) {
    try {
        $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        if ($task) {
            $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName
            Write-Host "   $TaskName" -ForegroundColor Green
            Write-Host "      State: $($task.State)" -ForegroundColor White
            Write-Host "      Last Run: $($taskInfo.LastRunTime)" -ForegroundColor White
            Write-Host "      Next Run: $($taskInfo.NextRunTime)" -ForegroundColor White
        } else {
            Write-Host "   Missing: $TaskName" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "   Error checking: $TaskName" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Final Task List:" -ForegroundColor Cyan
Get-ScheduledTask | Where-Object {$_.TaskName -like "*Crisis*" -or $_.TaskName -like "*Finance*"} | Format-Table TaskName, State

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "Cleanup Complete!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Active System:" -ForegroundColor Cyan
Write-Host "   Dual Email Crisis Monitor (every 15 minutes)" -ForegroundColor White
Write-Host "   Daily Finance Report (9:00 AM daily)" -ForegroundColor White
Write-Host ""
Write-Host "Email Types:" -ForegroundColor Cyan
Write-Host "   Daily Finance View: MM/DD/YYYY (comprehensive)" -ForegroundColor White
Write-Host "   Finance Alert: Immediate Action (when needed)" -ForegroundColor White
Write-Host ""

pause