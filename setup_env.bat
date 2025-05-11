@echo off
REM Script để thiết lập môi trường ảo và cài đặt các thư viện cần thiết (phiên bản CMD)

echo Đang thiết lập môi trường ảo Python...

REM Kiểm tra Python đã được cài đặt chưa
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Không tìm thấy Python. Hãy cài đặt Python trước khi tiếp tục.
    exit /b 1
)

SET ENV_NAME=venv

REM Cài đặt virtualenv nếu chưa có
pip show virtualenv > nul 2>&1
if %errorlevel% neq 0 (
    echo Đang cài đặt virtualenv...
    python -m pip install virtualenv
)

REM Kiểm tra môi trường ảo đã tồn tại chưa
if exist %ENV_NAME% (
    echo Môi trường ảo '%ENV_NAME%' đã tồn tại.
) else (
    echo Đang tạo môi trường ảo '%ENV_NAME%'...
    python -m virtualenv %ENV_NAME%
)

REM Kiểm tra requirements.txt đã tồn tại chưa
if not exist requirements.txt (
    echo django==5.0.1 > requirements.txt
    echo selenium==4.18.1 >> requirements.txt
    echo beautifulsoup4==4.12.2 >> requirements.txt
    echo requests==2.31.0 >> requirements.txt
    echo Pillow==10.2.0 >> requirements.txt
    echo webdriver-manager==4.0.1 >> requirements.txt
    echo Đã tạo file requirements.txt với các thư viện cần thiết.
)

REM Cài đặt các thư viện từ requirements.txt
echo Đang cài đặt các thư viện cần thiết...
call %ENV_NAME%\Scripts\pip install -r requirements.txt

echo.
echo Môi trường ảo đã được thiết lập thành công!
echo.
echo Để kích hoạt môi trường ảo, chạy:
echo %ENV_NAME%\Scripts\activate
echo.
echo Để chạy script crawl dữ liệu sau khi kích hoạt, chạy:
echo python crawl_data.py
echo.
echo Để thoát khỏi môi trường ảo, gõ 'deactivate'

pause
