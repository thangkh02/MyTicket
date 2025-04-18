import os
import sys

def fix_null_bytes(file_path):
    try:
        # Đọc nội dung file
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Kiểm tra xem có null bytes không
        if b'\x00' not in content:
            print(f"File {file_path} không chứa null bytes.")
            return False
        
        # Xóa null bytes
        new_content = content.replace(b'\x00', b'')
        
        # Tạo bản sao lưu
        backup_path = file_path + '.backup'
        with open(backup_path, 'wb') as f:
            f.write(content)
        
        # Ghi nội dung mới vào file gốc
        with open(file_path, 'wb') as f:
            f.write(new_content)
        
        print(f"Đã sửa file {file_path} thành công. Bản sao lưu được tạo tại {backup_path}")
        return True
    except Exception as e:
        print(f"Lỗi khi sửa file {file_path}: {e}")
        return False

def fix_all_null_bytes(root_dir):
    files_fixed = 0
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                        if b'\x00' in content:
                            if fix_null_bytes(file_path):
                                files_fixed += 1
                except Exception as e:
                    print(f'Lỗi khi đọc file {file_path}: {e}')
    
    print(f"Đã sửa xong {files_fixed} file.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Nếu người dùng cung cấp đường dẫn file cụ thể
        fix_null_bytes(sys.argv[1])
    else:
        # Nếu không, quét toàn bộ thư mục
        fix_all_null_bytes('.')
    
    print("Quá trình sửa chữa hoàn tất.")