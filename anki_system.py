#!/usr/bin/env python3
"""
🎯 ANKI VOCABULARY LEARNING SYSTEM
Hệ thống học từ vựng Anki hoàn chỉnh

CÁCH SỬ DỤNG:
1. Ngày đầu: Chạy script này, chọn tạo template
2. Điền từ vựng từ ảnh sách vào file CSV
3. Chạy lại script, chọn tạo thẻ Anki
4. Import vào Anki và bắt đầu học

NGÀY HÔM SAU:
- Chỉ cần chụp ảnh mới → tạo template → điền → tạo thẻ!
"""

import os
import sys
import subprocess
from datetime import datetime

def check_requirements():
    """Kiểm tra các thư viện cần thiết"""
    required_packages = ['pandas', 'requests', 'gtts']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Thiếu các thư viện cần thiết:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\n📦 Cài đặt bằng lệnh:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    return True

def show_menu():
    """Hiển thị menu chính"""
    print("\n" + "="*60)
    print("🎯 HỆ THỐNG HỌC TỪ VỰNG ANKI HOÀN CHỈNH")
    print("="*60)
    print("📚 QUY TRÌNH HỌC TẬP:")
    print("1️⃣  Tạo template cho bài học mới")
    print("2️⃣  Tạo thẻ Anki từ file CSV đã điền") 
    print("3️⃣  Xem hướng dẫn sử dụng")
    print("4️⃣  Kiểm tra file và thư mục")
    print("0️⃣  Thoát")
    print("="*60)

def create_templates():
    """Chạy script tạo template"""
    print("\n🚀 Đang khởi động Template Generator...")
    
    # Lấy đường dẫn thư mục hiện tại của script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_script = os.path.join(script_dir, 'create_input_template.py')
    
    try:
        subprocess.run([sys.executable, template_script], cwd=script_dir, check=True)
    except FileNotFoundError:
        print("❌ Không tìm thấy file create_input_template.py")
        print(f"Kiểm tra trong folder: {script_dir}")
        print("Vui lòng đảm bảo tất cả file script ở cùng folder")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi chạy template generator: {e}")

def generate_anki_cards():
    """Chạy script tạo thẻ Anki"""
    print("\n🚀 Đang tạo thẻ Anki...")
    
    # Lấy đường dẫn thư mục hiện tại của script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(script_dir, 'input')
    generator_script = os.path.join(script_dir, 'enhanced_anki_generator.py')
    
    # Kiểm tra folder input
    if not os.path.exists(input_dir):
        print(f"❌ Không tìm thấy folder 'input' tại: {input_dir}")
        print("Vui lòng tạo template trước!")
        return
    
    csv_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]
    if not csv_files:
        print(f"❌ Không tìm thấy file CSV nào trong folder: {input_dir}")
        print("Vui lòng tạo template và điền thông tin trước!")
        return
    
    print(f"📁 Tìm thấy {len(csv_files)} file CSV:")
    for f in csv_files:
        print(f"   - {f}")
    
    try:
        subprocess.run([sys.executable, generator_script], cwd=script_dir, check=True)
    except FileNotFoundError:
        print("❌ Không tìm thấy file enhanced_anki_generator.py")
        print(f"Kiểm tra trong folder: {script_dir}")
        print("Vui lòng đảm bảo tất cả file script ở cùng folder")
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi tạo thẻ Anki: {e}")

def show_guide():
    """Hiển thị hướng dẫn chi tiết"""
    guide = """
📖 HƯỚNG DẪN SỬ DỤNG CHI TIẾT

🎯 BƯỚC 1: CHUẨN BỊ
┌─────────────────────────────────────────────────────────────┐
│ • Chụp ảnh các trang từ vựng từ sách                        │
│ • Đảm bảo ảnh rõ nét, đọc được                              │
│ • Có kết nối internet (để tải ảnh và âm thanh)             │
└─────────────────────────────────────────────────────────────┘

🎯 BƯỚC 2: TẠO TEMPLATE
┌─────────────────────────────────────────────────────────────┐
│ 1. Chọn "1" ở menu chính                                    │
│ 2. Chọn loại template cần tạo:                             │
│    - Vocabulary: Danh sách từ vựng                         │
│    - Exercises: Bài tập điền từ                            │
│    - Cả hai: Tạo luôn cả hai file                          │
│ 3. File CSV sẽ được tạo trong folder 'input/'              │
└─────────────────────────────────────────────────────────────┘

🎯 BƯỚC 3: ĐIỀN THÔNG TIN
┌─────────────────────────────────────────────────────────────┐
│ • Mở file CSV bằng Excel hoặc Google Sheets                │
│ • Điền thông tin từ ảnh đã chụp:                           │
│   - Word: từ tiếng Anh                                     │
│   - Pronunciation: phiên âm (copy từ sách)                 │
│   - Vietnamese: nghĩa tiếng Việt                           │
│   - Example_Sentence: câu ví dụ                           │
│ • Lưu file sau khi điền xong                               │
└─────────────────────────────────────────────────────────────┘

🎯 BƯỚC 4: TẠO THẺ ANKI
┌─────────────────────────────────────────────────────────────┐
│ 1. Chọn "2" ở menu chính                                    │
│ 2. Chờ script tải ảnh và âm thanh                          │
│ 3. File .txt sẽ được tạo trong folder 'output/anki_import/'│
│ 4. Đọc file hướng dẫn để import vào Anki                   │
└─────────────────────────────────────────────────────────────┘

🎯 BƯỚC 5: IMPORT VÀO ANKI
┌─────────────────────────────────────────────────────────────┐
│ 1. Copy file media vào folder Anki                         │
│ 2. Trong Anki: File > Import                               │
│ 3. Chọn file .txt vừa tạo                                  │
│ 4. Tick "Allow HTML in fields"                             │
│ 5. Import và bắt đầu học!                                  │
└─────────────────────────────────────────────────────────────┘

💡 MẸO HAY:
• Quick Input: Nhập nhanh danh sách từ không cần mở Excel
• Batch Processing: Có thể tạo nhiều file CSV cùng lúc
• Auto Media: Script tự động tải ảnh + âm thanh cho từng từ
• Multi Types: Tạo nhiều loại thẻ (từ vựng, điền từ, phát âm)

⚠️  LƯU Ý:
• Cần internet để tải media
• API Pixabay có giới hạn 100 request/phút
• File phải ở định dạng CSV (không phải Excel .xlsx)
• Backup file CSV để tái sử dụng

🎓 CHIẾN LƯỢC HỌC:
• Ngày 1-7: Chỉ học thẻ từ vựng cơ bản
• Ngày 8-14: Thêm thẻ điền từ
• Ngày 15+: Sử dụng tất cả loại thẻ
• Mỗi ngày: 15-30 phút, đều đặn
"""
    print(guide)

def check_files_and_folders():
    """Kiểm tra trạng thái file và thư mục"""
    print("\n🔍 KIỂM TRA HỆ THỐNG")
    print("="*50)
    
    # Lấy đường dẫn thư mục hiện tại
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"📍 Thư mục làm việc: {script_dir}")
    
    # Kiểm tra các script cần thiết
    required_scripts = [
        'enhanced_anki_generator.py',
        'create_input_template.py'
    ]
    
    print("\n📄 Các file script:")
    for script in required_scripts:
        script_path = os.path.join(script_dir, script)
        if os.path.exists(script_path):
            print(f"   ✅ {script}")
        else:
            print(f"   ❌ {script} - THIẾU!")
    
    # Kiểm tra thư mục
    print("\n📁 Thư mục:")
    folders = ['input', 'output', 'output/media', 'output/anki_import']
    for folder in folders:
        folder_path = os.path.join(script_dir, folder)
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)
            print(f"   ✅ {folder}/ ({len(files)} files)")
        else:
            print(f"   📂 {folder}/ - sẽ tạo khi cần")
    
    # Kiểm tra file CSV trong input
    input_path = os.path.join(script_dir, 'input')
    if os.path.exists(input_path):
        csv_files = [f for f in os.listdir(input_path) if f.endswith('.csv')]
        if csv_files:
            print(f"\n📋 File CSV trong input/ ({len(csv_files)} files):")
            for f in csv_files:
                print(f"   - {f}")
        else:
            print(f"\n📋 Chưa có file CSV nào trong input/")
    
    # Kiểm tra output
    anki_path = os.path.join(script_dir, 'output', 'anki_import')
    if os.path.exists(anki_path):
        anki_files = [f for f in os.listdir(anki_path) if f.endswith('.txt')]
        if anki_files:
            print(f"\n🎴 File Anki đã tạo ({len(anki_files)} files):")
            for f in anki_files:
                print(f"   - {f}")
    
    print(f"\n⏰ Thời gian kiểm tra: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Hàm chính"""
    # Kiểm tra requirements
    if not check_requirements():
        input("\nNhấn Enter để thoát...")
        return
    
    while True:
        show_menu()
        choice = input("\n👉 Chọn chức năng (0-4): ").strip()
        
        if choice == '1':
            create_templates()
            
        elif choice == '2':
            generate_anki_cards()
            
        elif choice == '3':
            show_guide()
            
        elif choice == '4':
            check_files_and_folders()
            
        elif choice == '0':
            print("\n👋 Cảm ơn bạn đã sử dụng! Chúc bạn học tốt! 🎓")
            break
            
        else:
            print("❌ Lựa chọn không hợp lệ! Vui lòng chọn từ 0-4")
        
        input("\n⏸️  Nhấn Enter để tiếp tục...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Tạm biệt!")
    except Exception as e:
        print(f"\n❌ Lỗi không mong muốn: {e}")
        input("Nhấn Enter để thoát...")