# Schedule Headless Training to start on Mondays at 8 AM
$taskName = "Headless Training Startup"
$taskPath = "C:\Users\dvoigtlander\claude\Headless_Training\START.bat"

# Check if task already exists and remove it
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing task..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create trigger for Monday at 8 AM
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 8am

# Create action to run the batch file
$action = New-ScheduledTaskAction -Execute $taskPath -WorkingDirectory "C:\Users\dvoigtlander\claude\Headless_Training"

# Create task with highest privileges
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

# Register the scheduled task
Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Principal $principal -Description "Start Headless Training API, Dashboard, and Tunnels"

Write-Host "Scheduled task created: $taskName"
Write-Host "Task will run every Monday at 8:00 AM"
Write-Host ""
Write-Host "To verify, run: Get-ScheduledTask -TaskName '$taskName'"
Write-Host "To run manually: Start-ScheduledTask -TaskName '$taskName'"
