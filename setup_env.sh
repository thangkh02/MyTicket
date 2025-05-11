#!/bin/bash
# Script thiết lập môi trường ảo và cài đặt các thư viện cần thiết (phiên bản Linux/Mac)

echo "Đang thiết lập môi trường ảo Python..."

# Kiểm tra Python đã được cài đặt chưa
if ! command -v python3 &> /dev/null; then
    echo "Không tìm thấy Python. Hãy cài đặt Python trước khi tiếp tục."
    exit 1
fi

ENV_NAME="venv"

# Kiểm tra venv module
python3 -c "import venv" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Module venv không khả dụng. Cài đặt python3-venv..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3-venv
    elif command -v brew &> /dev/null; then
        echo "Bạn đang sử dụng macOS. Đảm bảo Python được cài đặt từ Homebrew để có module venv."
    else
        echo "Không thể cài đặt python3-venv tự động. Vui lòng cài đặt thủ công."
        exit 1
    fi
fi

# Kiểm tra môi trường ảo đã tồn tại chưa
if [ -d "$ENV_NAME" ]; then
    echo "Môi trường ảo '$ENV_NAME' đã tồn tại."
else
    echo "Đang tạo môi trường ảo '$ENV_NAME'..."
    python3 -m venv $ENV_NAME
fi

# Tạo requirements.txt nếu chưa tồn tại
if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << EOF
django==5.0.1
selenium==4.18.1
beautifulsoup4==4.12.2
requests==2.31.0
Pillow==10.2.0
webdriver-manager==4.0.1
EOF
    echo "Đã tạo file requirements.txt với các thư viện cần thiết."
fi

# Cài đặt các thư viện từ requirements.txt
echo "Đang cài đặt các thư viện cần thiết..."
$ENV_NAME/bin/pip install -r requirements.txt

echo -e "\nMôi trường ảo đã được thiết lập thành công!"
echo -e "\nĐể kích hoạt môi trường ảo, chạy:"
echo "source $ENV_NAME/bin/activate"

echo -e "\nĐể chạy script crawl dữ liệu sau khi kích hoạt, chạy:"
echo "python crawl_data.py"

echo -e "\nĐể thoát khỏi môi trường ảo, gõ 'deactivate'"
