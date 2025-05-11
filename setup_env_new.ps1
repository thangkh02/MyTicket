# Script thiết lập môi trường ảo và cài đặt các thư viện cần thiết

# Tên thư mục môi trường ảo
$ENV_NAME = "venv"

Write-Host "Đang thiết lập môi trường ảo Python..." -ForegroundColor Green

# Kiểm tra Python đã được cài đặt chưa
try {
    $python_version = python --version
    Write-Host "Đã tìm thấy $python_version" -ForegroundColor Green
} catch {
    Write-Host "Không tìm thấy Python. Hãy cài đặt Python trước khi tiếp tục." -ForegroundColor Red
    exit 1
}

# Kiểm tra virtualenv đã được cài đặt chưa
try {
    $virtualenv_version = pip show virtualenv
    if (-not $virtualenv_version) {
        Write-Host "Đang cài đặt virtualenv..." -ForegroundColor Yellow
        python -m pip install virtualenv
    } else {
        Write-Host "virtualenv đã được cài đặt." -ForegroundColor Green
    }
} catch {
    Write-Host "Đang cài đặt virtualenv..." -ForegroundColor Yellow
    python -m pip install virtualenv
}

# Kiểm tra môi trường ảo đã tồn tại chưa
if (Test-Path -Path $ENV_NAME) {
    Write-Host "Môi trường ảo '$ENV_NAME' đã tồn tại." -ForegroundColor Green
} else {
    Write-Host "Đang tạo môi trường ảo '$ENV_NAME'..." -ForegroundColor Yellow
    python -m virtualenv $ENV_NAME
}

# Tạo requirements.txt nếu chưa tồn tại
if (-not (Test-Path -Path "requirements.txt")) {
    @"
django==5.0.1
selenium==4.18.1
beautifulsoup4==4.12.2
requests==2.31.0
Pillow==10.2.0
webdriver-manager==4.0.1
"@ | Out-File -FilePath "requirements.txt" -Encoding utf8
    Write-Host "Đã tạo file requirements.txt với các thư viện cần thiết." -ForegroundColor Green
}

# Cài đặt các thư viện từ requirements.txt
& "$ENV_NAME\Scripts\pip" install -r requirements.txt

Write-Host "`nMôi trường ảo đã được thiết lập thành công!" -ForegroundColor Green
Write-Host "`nĐể kích hoạt môi trường ảo, chạy:" -ForegroundColor Cyan
Write-Host ".\$ENV_NAME\Scripts\Activate.ps1" -ForegroundColor Yellow

Write-Host "`nĐể chạy script crawl dữ liệu sau khi kích hoạt, chạy:" -ForegroundColor Cyan
Write-Host "python crawl_data.py" -ForegroundColor Yellow

Write-Host "`nĐể thoát khỏi môi trường ảo, gõ 'deactivate'" -ForegroundColor Cyan
