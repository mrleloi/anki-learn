#!/usr/bin/env python3
"""
TEMPLATE GENERATOR FOR ANKI VOCABULARY SYSTEM
Tạo template để bạn có thể dễ dàng thêm từ vựng và bài tập mới

Chạy file này để tạo template CSV mới cho bài học tiếp theo
"""

import pandas as pd
import os
from datetime import datetime

def create_vocabulary_template():
    """Tạo template cho vocabulary list"""
    template_data = [
        {
            'Word': 'example',
            'Pronunciation': '/ɪɡˈzɑːmpəl/',
            'Vietnamese': 'ví dụ, mẫu',
            'Part_of_Speech': 'noun',
            'Example_Sentence': 'This is an example sentence.',
            'Fill_in_Blank_Question': 'Can you give me an _______ of how to use this word?',
            'Fill_in_Blank_Answer': 'example'
        },
        # Thêm các dòng trống để điền
        {
            'Word': '',
            'Pronunciation': '',
            'Vietnamese': '',
            'Part_of_Speech': '',
            'Example_Sentence': '',
            'Fill_in_Blank_Question': '',
            'Fill_in_Blank_Answer': ''
        }
    ]
    
    return pd.DataFrame(template_data)

def create_exercise_template():
    """Tạo template cho exercises"""
    template_data = [
        {
            'Question': 'A/an _______ person who is very smart and quick to understand.',
            'Answer': 'intelligent',
            'Type': 'definition',
            'Difficulty': 'basic',
            'Context': 'personality traits'
        },
        {
            'Question': 'A: She always helps everyone. B: Yes, she can be very _______ at times.',
            'Answer': 'helpful',
            'Type': 'dialogue',
            'Difficulty': 'basic',
            'Context': 'personality traits'
        },
        # Thêm các dòng trống để điền
        {
            'Question': '',
            'Answer': '',
            'Type': 'definition',  # hoặc 'dialogue'
            'Difficulty': 'basic',  # basic, intermediate, advanced
            'Context': 'personality traits'
        }
    ]
    
    return pd.DataFrame(template_data)

def extract_from_images_guide():
    """Tạo hướng dẫn trích xuất từ ảnh"""
    guide = """
# HƯỚNG DẪN TRÍCH XUẤT TỪ VỰNG TỪ ẢNH

## Bước 1: Chuẩn bị ảnh đầu vào

## Bước 2: Tạo file vocabularylist.csv
Từ ảnh đầu vào, sử dụng AI để điền vào file CSV theo mẫu:

### Cột Word: 
- Ghi từ tiếng Anh (ví dụ: friendly)

### Cột Pronunciation:
- Copy phiên âm từ sách (ví dụ: /ˈfrendli/)
- Nếu không có, để trống

### Cột Vietnamese:
- Ghi nghĩa tiếng Việt (ví dụ: thân thiện), nếu nghĩa này không phù hợp với Word (kết hợp cả các cột khác) thì tự cho nghĩa tiếng việt khác

### Cột Part_of_Speech:
- adj (tính từ), noun (danh từ), verb (động từ), adv (trạng từ)

### Cột Example_Sentence:
- Tạo câu ví dụ hoặc copy từ sách
- Nếu không có, để trống

### Cột Fill_in_Blank_Question:
- Tạo câu hỏi điền từ (ví dụ: "She is very _______ to everyone.")
- Nếu không muốn tạo, để trống

### Cột Fill_in_Blank_Answer:
- Điền từ cần điền (thường giống với cột Word)

## Bước 3: Tạo file exercises.csv (nếu có bài tập)
Từ ảnh bài tập, điền vào file CSV:

### Cột Question:
- Copy nguyên câu hỏi, thay đáp án bằng _______
- Ví dụ: "A/an _______ person who is very kind."

### Cột Answer:
- Điền đáp án đúng

### Cột Type:
- "definition" cho bài định nghĩa
- "dialogue" cho bài đối thoại

### Cột Difficulty:
- "basic", "intermediate", hoặc "advanced"

### Cột Context:
- Chủ đề (ví dụ: "personality traits")

## Bước 4: Chạy script
1. Đặt các file CSV vào folder 'input/'
2. Chạy: python run.py
3. Import vào Anki theo hướng dẫn

## MẸO HAY:
- Có thể chụp nhiều trang, tạo nhiều file CSV
- Đặt tên file theo chủ đề: "lesson1_vocabulary.csv", "lesson1_exercises.csv"
- Script sẽ tự động xử lý tất cả file CSV trong folder input/
"""
    return guide

def create_quick_input_from_word_list():
    """Tạo function để nhanh chóng nhập danh sách từ"""
    print("🚀 QUICK INPUT - Nhập nhanh danh sách từ vựng")
    print("=" * 50)
    print("Nhập từng từ vựng, mỗi từ một dòng.")
    print("Format: word | pronunciation | vietnamese | part_of_speech")
    print("Ví dụ: friendly | /ˈfrendli/ | thân thiện | adj")
    print("Gõ 'done' để kết thúc nhập")
    print("")
    
    words = []
    while True:
        user_input = input("Nhập từ (hoặc 'done'): ").strip()
        if user_input.lower() == 'done':
            break
        if user_input:
            parts = user_input.split('|')
            if len(parts) >= 2:
                word_data = {
                    'Word': parts[0].strip(),
                    'Pronunciation': parts[1].strip() if len(parts) > 1 else '',
                    'Vietnamese': parts[2].strip() if len(parts) > 2 else '',
                    'Part_of_Speech': parts[3].strip() if len(parts) > 3 else 'adj',
                    'Example_Sentence': '',
                    'Fill_in_Blank_Question': '',
                    'Fill_in_Blank_Answer': ''
                }
                words.append(word_data)
                print(f"✅ Đã thêm: {word_data['Word']}")
            else:
                print("❌ Format không đúng. Thử lại!")
    
    if words:
        df = pd.DataFrame(words)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"input/quick_input_{timestamp}.csv"
        os.makedirs('input', exist_ok=True)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"✅ Đã lưu {len(words)} từ vào: {filename}")
        return filename
    return None

def main():
    """Menu chính"""
    print("🎯 ANKI TEMPLATE GENERATOR")
    print("=" * 40)
    print("1. Tạo template vocabulary mới")
    print("2. Tạo template exercises mới") 
    print("3. Tạo cả hai template")
    print("4. Quick input - Nhập nhanh từ vựng")
    print("5. Hiển thị hướng dẫn trích xuất từ ảnh")
    print("0. Thoát")
    
    choice = input("\nChọn chức năng (0-5): ").strip()
    
    # Tạo folder input nếu chưa có
    os.makedirs('input', exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    if choice == '1':
        # Tạo vocabulary template
        vocab_df = create_vocabulary_template()
        filename = f"input/vocabulary_template_{timestamp}.csv"
        vocab_df.to_csv(filename, index=False, encoding='utf-8')
        print(f"✅ Đã tạo template vocabulary: {filename}")
        print("📝 Hãy mở file và điền thông tin từ vựng")
        
    elif choice == '2':
        # Tạo exercise template
        exercise_df = create_exercise_template()
        filename = f"input/exercises_template_{timestamp}.csv"
        exercise_df.to_csv(filename, index=False, encoding='utf-8')
        print(f"✅ Đã tạo template exercises: {filename}")
        print("📝 Hãy mở file và điền thông tin bài tập")
        
    elif choice == '3':
        # Tạo cả hai
        vocab_df = create_vocabulary_template()
        exercise_df = create_exercise_template()
        
        vocab_file = f"input/vocabulary_template_{timestamp}.csv"
        exercise_file = f"input/exercises_template_{timestamp}.csv"
        
        vocab_df.to_csv(vocab_file, index=False, encoding='utf-8')
        exercise_df.to_csv(exercise_file, index=False, encoding='utf-8')
        
        print(f"✅ Đã tạo cả hai template:")
        print(f"   - Vocabulary: {vocab_file}")
        print(f"   - Exercises: {exercise_file}")
        print("📝 Hãy mở các file và điền thông tin")
        
    elif choice == '4':
        # Quick input
        filename = create_quick_input_from_word_list()
        if filename:
            print(f"\n🎉 Hoàn thành! Bây giờ bạn có thể chạy:")
            print(f"python enhanced_anki_generator.py")
        
    elif choice == '5':
        # Hiển thị hướng dẫn
        guide = extract_from_images_guide()
        guide_file = f"extract_guide_{timestamp}.txt"
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide)
        print(f"✅ Đã tạo hướng dẫn: {guide_file}")
        print("\n" + guide)
        
    elif choice == '0':
        print("👋 Tạm biệt!")
        return
        
    else:
        print("❌ Lựa chọn không hợp lệ!")
        return
    
    print(f"\n📁 Sau khi điền xong, chạy lệnh:")
    print(f"python enhanced_anki_generator.py")
    print(f"\n💡 TIP: Ngày mai chỉ cần:")
    print(f"1. Chụp ảnh từ vựng mới")
    print(f"2. Chạy lại script này tạo template")
    print(f"3. Điền thông tin từ ảnh vào file CSV")
    print(f"4. Chạy enhanced_anki_generator.py")

if __name__ == "__main__":
    main()