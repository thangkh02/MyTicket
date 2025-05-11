@echo off
echo Setting up Python virtual environment...

REM Thư mục môi trường ảo
set ENV_NAME=venv

REM Kiểm tra Python
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python not found. Please install Python first.
    exit /b 1
)
echo Python found!

REM Kiểm tra virtualenv
pip show virtualenv > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Installing virtualenv...
    pip install virtualenv
) else (
    echo virtualenv is already installed.
)

REM Kiểm tra môi trường ảo
if exist %ENV_NAME% (
    echo Virtual environment '%ENV_NAME%' already exists.
) else (
    echo Creating virtual environment '%ENV_NAME%'...
    python -m virtualenv %ENV_NAME%
)

REM Tạo requirements.txt nếu cần
if not exist requirements.txt (
    echo Creating requirements.txt...
    (
        echo django==5.0.1
        echo selenium==4.18.1
        echo beautifulsoup4==4.12.2
        echo requests==2.31.0
        echo Pillow==10.2.0
        echo webdriver-manager==4.0.1
    ) > requirements.txt
    echo Requirements file created.
)

REM Cài đặt các gói cần thiết
echo Installing required packages...
call %ENV_NAME%\Scripts\pip install -r requirements.txt

echo.
echo Setup completed successfully!
echo.
echo To activate the virtual environment, run:
echo     %ENV_NAME%\Scripts\activate.bat
echo.
echo To run the crawler after activating, run:
echo     python crawl_data.py
echo.
echo To deactivate the virtual environment when finished, type 'deactivate'
