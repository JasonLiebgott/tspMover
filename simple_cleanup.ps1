# Simple Task Cleanup - Run as Administrator
# Removes old crisis monitor tasks, keeps new dual email system

Write-Host "Task Cleanup Starting..." -ForegroundColor Yellow

# Remove old tasks
$TasksToRemove = @("Financial Crisis Monitor", "Enhanced Crisis Monitor v2")

foreach ($TaskName in $TasksToRemove) {
    try {
        Write-Host "Removing: $TaskName"
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
        Write-Host "SUCCESS: Removed $TaskName" -ForegroundColor Green
    }
    catch {
        Write-Host "INFO: $TaskName not found or already removed" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Remaining tasks:" -ForegroundColor Cyan
Get-ScheduledTask | Where-Object {$_.TaskName -like "*Crisis*" -or $_.TaskName -like "*Finance*"} | Format-Table TaskName, State

Write-Host "Cleanup complete!" -ForegroundColor Green