# Số lượng file muốn tạo
$so_luong_file = 18
# Hẹn giờ shutdown sau 60 giây
# shutdown.exe /s /t 5 /f
# Nội dung ghi vào file
$noi_dung = "ilovefemboy"

# Thư mục lưu file
$thu_muc = "Desktop"

# Tạo thư mục nếu chưa tồn tại
if (!(Test-Path $thu_muc)) {
    New-Item -ItemType Directory -Path $thu_muc | Out-Null
}

for ($i = 1; $i -le $so_luong_file; $i++) {
    $ten_file = Join-Path $thu_muc "$i.txt"
    
    # Ghi nội dung vào file
    Set-Content -Path $ten_file -Value $noi_dung -Encoding UTF8
    
    # Mở file bằng Notepad
    Start-Process "notepad.exe" -ArgumentList $ten_file
}


