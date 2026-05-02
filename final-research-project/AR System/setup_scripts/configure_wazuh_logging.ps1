$ErrorActionPreference = "Stop"

$ErrorActionPreference = "Stop"

# 1. Define Paths
$ArsLogPath = "$env:ProgramData\AR_System\ars_events.json"
$OssecConfigPath = "C:\Program Files (x86)\ossec-agent\ossec.conf"

Write-Host "=== Wazuh Agent Log Configuration ===" -ForegroundColor Cyan
Write-Host "Target Log File: $ArsLogPath"

# 2. Check if Agent is installed
if (-not (Test-Path $OssecConfigPath)) {
    Write-Host "[ERROR] Wazuh Agent config not found at: $OssecConfigPath" -ForegroundColor Red
    Write-Host "Please ensure Wazuh Agent is installed."
    exit
}

# 3. Read Config
[xml]$xml = Get-Content $OssecConfigPath

# 4. Check if already configured
$existing = $xml.ossec_config.localfile | Where-Object { $_.location -eq $ArsLogPath }

if ($existing) {
    Write-Host "[INFO] Configuration already exists. Skipping." -ForegroundColor Yellow
}
else {
    Write-Host "[INFO] Adding AR System log to Wazuh configuration..." -ForegroundColor Green
    
    # Create new XML node
    $newFileBase = $xml.CreateElement("localfile")
    
    $locNode = $xml.CreateElement("location")
    $locNode.InnerText = $ArsLogPath
    $newFileBase.AppendChild($locNode)
    
    $fmtNode = $xml.CreateElement("log_format")
    $fmtNode.InnerText = "json"
    $newFileBase.AppendChild($fmtNode)

    # Append to root
    $xml.ossec_config.AppendChild($newFileBase)
    
    # Save (Needs Admin)
    try {
        $xml.Save($OssecConfigPath)
        Write-Host "[SUCCESS] Config updated." -ForegroundColor Green
    }
    catch {
        Write-Host "[ERROR] Failed to save config. PLEASE RUN AS ADMINISTRATOR." -ForegroundColor Red
        exit
    }
}

# 5. Restart Agent
Write-Host "[INFO] Restarting Wazuh Service..."
Restart-Service -Name WazuhSvc -Force
Write-Host "[SUCCESS] Wazuh Agent restarted. Logs are now being shipped!" -ForegroundColor Cyan
