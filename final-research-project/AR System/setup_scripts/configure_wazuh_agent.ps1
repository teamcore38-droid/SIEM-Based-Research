<#
.SYNOPSIS
    Configures the Wazuh Agent to connect to a specific Wazuh Manager.
.DESCRIPTION
    This script updates the ossec.conf file with the provided Manager IP address,
    restarts the Wazuh service, and checks the connection status.
    Must be run as Administrator.
#>

# Check for Administrator privileges
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {  
    Write-Warning "You do not have Administrator rights to run this script!`nPlease re-run this script as an Administrator."
    Break
}

Clear-Host
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "      Wazuh Agent Configuration Utility       " -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""

# 1. Get Wazuh Manager IP
$rawInput = Read-Host -Prompt "Enter the IP Address of your Wazuh Manager (e.g., 20.239.185.152)"

if ([string]::IsNullOrWhiteSpace($rawInput)) {
    Write-Error "IP Address cannot be empty."
    exit
}

# Clean input: Remove https://, http://, and trailing slashes
$managerIp = $rawInput -replace "^https?://", "" -replace "/$", ""
$managerIp = $managerIp.Trim()

Write-Host "Using Manager IP: $managerIp" -ForegroundColor Gray

# 2. Define Paths
$x86Path = "C:\Program Files (x86)\ossec-agent"
$x64Path = "C:\Program Files\ossec-agent"
$agentPath = ""

if (Test-Path $x86Path) {
    $agentPath = $x86Path
}
elseif (Test-Path $x64Path) {
    $agentPath = $x64Path
}
else {
    Write-Error "Wazuh Agent installation not found in standard directories."
    exit
}

$configFile = Join-Path $agentPath "ossec.conf"
$logFile = Join-Path $agentPath "ossec.log"

Write-Host "Found Wazuh Agent at: $agentPath" -ForegroundColor Gray

# 3. Backup Config
$backupFile = "$configFile.bak"
Copy-Item -Path $configFile -Destination $backupFile -Force
Write-Host "Backup created at $backupFile" -ForegroundColor Green

# 4. Update Config
Write-Host "Updating configuration..." -ForegroundColor Yellow
try {
    # Read content
    [xml]$xml = Get-Content $configFile

    # Update Manager IP
    # Logic to handle different XML structures or multiple server entries
    $clientNode = $xml.SelectSingleNode("//client")
    
    if ($null -eq $clientNode) {
        throw "Could not find <client> section in ossec.conf"
    }
    
    $serverNode = $clientNode.SelectSingleNode("server")
    
    if ($null -eq $serverNode) {
        # Create server node if missing (unlikely on fresh install but safe)
        $serverNode = $xml.CreateElement("server")
        $clientNode.AppendChild($serverNode) | Out-Null
    }

    $addressNode = $serverNode.SelectSingleNode("address")
    
    if ($null -eq $addressNode) {
        # Create address node if missing
        $addressNode = $xml.CreateElement("address")
        $serverNode.AppendChild($addressNode) | Out-Null
    }

    # Explicitly set InnerText to the string IP
    $addressNode.InnerText = [string]$managerIp

    # Save
    $xml.Save($configFile)
    Write-Host "Configuration updated with Manager IP: $managerIp" -ForegroundColor Green
}
catch {
    Write-Error "Failed to update ossec.conf: $_"
    exit
}

# 5. Restart Service
Write-Host "Restarting Wazuh Service..." -ForegroundColor Yellow
Restart-Service -Name WazuhSvc -Force
$service = Get-Service -Name WazuhSvc
if ($service.Status -eq 'Running') {
    Write-Host "Service is running." -ForegroundColor Green
}
else {
    Write-Error "Service failed to start."
}

# 6. Check Logs (Wait a moment for connection)
Write-Host "Waiting for agent to connect..." -ForegroundColor Cyan
Start-Sleep -Seconds 5
if (Test-Path $logFile) {
    Get-Content $logFile -Tail 10 | ForEach-Object {
        if ($_ -match "Connected to the server") {
            Write-Host $_ -ForegroundColor Green
        }
        elseif ($_ -match "error") {
            # Highlight errors but don't panic
            Write-Host $_ -ForegroundColor Red
        }
        else {
            Write-Host $_ -ForegroundColor Gray
        }
    }
}
else {
    Write-Warning "Log file not found yet. The service might still be starting."
}

Write-Host ""
Write-Host "Configuration Complete." -ForegroundColor Cyan
Write-Host "If you see 'Connected to the server', you are good to go!" -ForegroundColor Green
