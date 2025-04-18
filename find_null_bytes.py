import os

def check_for_null_bytes(root_dir):
    found_null = False
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'rb') as f:
                        content = f.read()
                        if b'\x00' in content:
                            print(f'Tìm thấy null bytes trong file: {filepath}')
                            found_null = True
                except Exception as e:
                    print(f'Lỗi khi đọc file {filepath}: {e}')
    
    if not found_null:
        print('Không tìm thấy file nào chứa null bytes.')

if __name__ == "__main__":
    check_for_null_bytes('.')
    print("Quá trình kiểm tra hoàn tất.")