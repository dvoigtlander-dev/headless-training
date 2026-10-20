# Kill old tunnels
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force

# Wait a moment
Start-Sleep -Seconds 2

# Start new tunnel
$process = Start-Process -FilePath "./cloudflared.exe" -ArgumentList "tunnel --url http://localhost:8008" -RedirectStandardOutput "api-tunnel.log" -PassThru -WindowStyle Hidden -WorkingDirectory (Get-Location)

# Wait for tunnel to start
Start-Sleep -Seconds 8

# Get the URL
$url = Select-String -Path "api-tunnel.log" -Pattern "https://.*trycloudflare.com" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Line

if ($url) {
    $cleanUrl = $url -replace ".*?(https://.*trycloudflare\.com).*", '$1'
    Write-Host "API Tunnel URL: $cleanUrl"
    Write-Host "Slash Command Request URL: $cleanUrl/slack/slash"
    $cleanUrl | Set-Content -Path "tunnel-url.txt"
} else {
    Write-Host "Tunnel not ready yet. Trying again in 5 seconds..."
    Start-Sleep -Seconds 5
    $url = Select-String -Path "api-tunnel.log" -Pattern "https://.*trycloudflare.com" -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Line
    if ($url) {
        $cleanUrl = $url -replace ".*?(https://.*trycloudflare\.com).*", '$1'
        Write-Host "API Tunnel URL: $cleanUrl"
        Write-Host "Slash Command Request URL: $cleanUrl/slack/slash"
        $cleanUrl | Set-Content -Path "tunnel-url.txt"
    }
}
