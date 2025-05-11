@echo off
echo === Thiet lap moi truong Python don gian ===

REM Tao moi truong ao
echo Dang tao moi truong ao Python...
python -m venv env

REM Kich hoat moi truong ao
echo Dang kich hoat moi truong ao...
call env\Scripts\activate.bat

REM Cai dat cac thu vien can thiet
echo Dang cai dat cac thu vien...
pip install django==5.0.1 selenium==4.18.1 beautifulsoup4==4.12.2 requests==2.31.0 Pillow==10.2.0 webdriver-manager==4.0.1

echo.
echo === Hoan thanh! ===
echo Moi truong ao da duoc kich hoat.
echo Bay gio ban co the chay: python crawl_data.py
echo.
