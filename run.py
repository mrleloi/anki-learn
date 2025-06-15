#!/usr/bin/env python3
"""
SIMPLE RUNNER - Chạy trực tiếp không qua subprocess
Đặt tất cả file .py trong C:\htdocs\anki-scripts\ và chạy file này
"""

import os
import sys

# Thêm thư mục hiện tại vào Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def show_menu():
    print("\n" + "="*60)
    print("🎯 HỆ THỐNG HỌC TỪ VỰNG ANKI")
    print("="*60)
    print("1️⃣  Tạo template cho bài học mới")
    print("2️⃣  Tạo thẻ Anki từ file CSV") 
    print("3️⃣  Kiểm tra file")
    print("0️⃣  Thoát")
    print("="*60)

def run_template_generator():
    """Chạy template generator trực tiếp"""
    print("\n🚀 Template Generator")
    print("=" * 40)
    
    try:
        # Import và chạy trực tiếp
        import create_input_template
        create_input_template.main()
    except ImportError:
        print("❌ Không tìm thấy file create_input_template.py")
        print(f"Đường dẫn hiện tại: {current_dir}")
        print("Vui lòng đảm bảo file create_input_template.py có trong folder này")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def run_anki_generator():
    """Chạy anki generator trực tiếp"""
    print("\n🚀 Anki Generator")
    print("=" * 40)
    
    # Kiểm tra input folder
    input_folder = os.path.join(current_dir, 'input')
    if not os.path.exists(input_folder):
        print("❌ Không tìm thấy folder 'input'")
        print("Vui lòng tạo template trước!")
        return
    
    csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
    if not csv_files:
        print("❌ Không tìm thấy file CSV nào trong folder 'input'")
        print("Vui lòng tạo template và điền thông tin trước!")
        return
    
    print(f"📁 Tìm thấy {len(csv_files)} file CSV:")
    for f in csv_files:
        print(f"   - {f}")
    
    try:
        # Import và chạy trực tiếp
        import enhanced_anki_generator
        enhanced_anki_generator.main()
    except ImportError:
        print("❌ Không tìm thấy file enhanced_anki_generator.py")
        print(f"Đường dẫn hiện tại: {current_dir}")
        print("Vui lòng đảm bảo file enhanced_anki_generator.py có trong folder này")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def check_system():
    """Kiểm tra hệ thống"""
    print("\n🔍 KIỂM TRA HỆ THỐNG")
    print("=" * 50)
    print(f"📍 Thư mục làm việc: {current_dir}")
    
    # Kiểm tra các file cần thiết
    required_files = [
        'enhanced_anki_generator.py',
        'create_input_template.py',
        'vocabularylist.csv',
        'exercises.csv'
    ]
    
    print("\n📄 Các file cần thiết:")
    for filename in required_files:
        filepath = os.path.join(current_dir, filename)
        if filename.endswith('.csv'):
            # CSV files nên ở trong input folder
            filepath = os.path.join(current_dir, 'input', filename)
        
        if os.path.exists(filepath):
            print(f"   ✅ {filename}")
        else:
            print(f"   ❌ {filename} - THIẾU!")
    
    # Kiểm tra thư mục
    print("\n📁 Thư mục:")
    folders = ['input', 'output', 'output/media', 'output/anki_import']
    for folder in folders:
        folder_path = os.path.join(current_dir, folder)
        if os.path.exists(folder_path):
            files = [f for f in os.listdir(folder_path) if not f.startswith('.')]
            print(f"   ✅ {folder}/ ({len(files)} files)")
            if files and len(files) <= 5:  # Hiển thị file nếu ít
                for f in files:
                    print(f"      - {f}")
        else:
            print(f"   📂 {folder}/ - chưa tạo")
    
    # Kiểm tra thư viện Python
    print("\n📦 Thư viện Python:")
    required_packages = ['pandas', 'requests', 'gtts']
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - chưa cài!")
    
    print(f"\n💡 Nếu thiếu thư viện, chạy: pip install pandas requests gtts")

def setup_initial_files():
    """Setup file ban đầu nếu chưa có"""
    print("\n🔧 SETUP BAN ĐẦU")
    
    # Tạo thư mục input nếu chưa có
    input_dir = os.path.join(current_dir, 'input')
    os.makedirs(input_dir, exist_ok=True)
    
    # Copy file CSV mẫu vào input nếu chưa có
    sample_files = ['vocabularylist.csv', 'exercises.csv']
    
    for filename in sample_files:
        source_path = os.path.join(current_dir, filename)
        target_path = os.path.join(input_dir, filename)
        
        if os.path.exists(source_path) and not os.path.exists(target_path):
            import shutil
            shutil.copy2(source_path, target_path)
            print(f"✅ Đã copy {filename} vào input/")
    
    print("✅ Setup hoàn tất!")

def main():
    """Main function"""
    # Setup ban đầu
    setup_initial_files()
    
    while True:
        show_menu()
        choice = input("\n👉 Chọn chức năng (0-3): ").strip()
        
        if choice == '1':
            run_template_generator()
            
        elif choice == '2':
            run_anki_generator()
            
        elif choice == '3':
            check_system()
            
        elif choice == '0':
            print("\n👋 Tạm biệt! Chúc bạn học tốt! 🎓")
            break
            
        else:
            print("❌ Lựa chọn không hợp lệ!")
        
        input("\n⏸️  Nhấn Enter để tiếp tục...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Tạm biệt!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        input("Nhấn Enter để thoát...")