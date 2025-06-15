#!/usr/bin/env python3
"""
ANKI DATA EXPORTER & AI PRACTICE GENERATOR - CLEAN VERSION
Version: 3.0 - No F-string Triple Quote Issues

Setup: Đặt file learning.txt cùng folder và chạy
"""

import pandas as pd
import json
import os
from datetime import datetime
import re

class AnkiLearningAnalyzer:
    def __init__(self, exports_folder='anki_exports'):
        """Initialize với folder chứa các file export theo level"""
        self.exports_folder = exports_folder
        self.proficiency_data = {
            'mastered': [],
            'familiar': [],
            'learning': [],
            'difficult': []
        }
        
    def setup_folder_structure(self):
        """Tạo folder structure và hướng dẫn"""
        os.makedirs(self.exports_folder, exist_ok=True)
        
        guide_content = """
# HƯỚNG DẪN EXPORT ANKI THEO MỨC ĐỘ HỌC

## BƯỚC 1: MỞ ANKI BROWSE
Tools → Browse (Ctrl+B)

## BƯỚC 2: FILTER VÀ EXPORT TỪNG NHÓM

### 🏆 MASTERED WORDS (Đã thành thạo):
Filter: rated:30 prop:ease>250
→ Export → Notes in Plain Text → Lưu: mastered.txt

### 😊 FAMILIAR WORDS (Quen thuộc):  
Filter: rated:30 prop:ease>200 prop:ease<250
→ Export → Notes in Plain Text → Lưu: familiar.txt

### 📚 LEARNING WORDS (Đang học):
Filter: is:review prop:ivl<21
→ Export → Notes in Plain Text → Lưu: learning.txt

### 😰 DIFFICULT WORDS (Khó):
Filter: rated:30 prop:ease<200
→ Export → Notes in Plain Text → Lưu: difficult.txt

## BƯỚC 3: CHẠY SCRIPT
python anki_data_exporter_clean.py
"""
        
        guide_path = os.path.join(self.exports_folder, 'EXPORT_GUIDE.txt')
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print(f"📁 Đã tạo folder: {self.exports_folder}/")
        print(f"📖 Đọc hướng dẫn tại: {guide_path}")
    
    def find_export_files(self):
        """Tìm các file export trong folder"""
        expected_files = {
            'mastered': 'mastered.txt',
            'familiar': 'familiar.txt', 
            'learning': 'learning.txt',
            'difficult': 'difficult.txt'
        }
        
        found_files = {}
        missing_files = []
        
        for level, filename in expected_files.items():
            filepath = os.path.join(self.exports_folder, filename)
            if os.path.exists(filepath):
                found_files[level] = filepath
                print(f"✅ Tìm thấy: {filename}")
            else:
                missing_files.append(filename)
                print(f"⚠️  Không có: {filename}")
        
        if not found_files:
            print(f"❌ Không tìm thấy file export nào trong {self.exports_folder}/")
            return None
            
        if missing_files:
            print(f"📝 Các file thiếu: {', '.join(missing_files)}")
        
        return found_files
    
    def parse_export_file(self, filepath, level):
        """Parse file export mới - chỉ lấy word đầu mỗi line"""
        print(f"\n📖 Đang đọc {level}: {os.path.basename(filepath)}")
        
        words_data = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip header lines và empty lines
                if (line.startswith('#') or 
                    not line or 
                    line_num == 1):  # Skip first line if it's header
                    continue
                
                # Split by tab và lấy thông tin
                parts = line.split('\t')
                if len(parts) >= 2:
                    # Word là phần đầu tiên
                    word_part = parts[0].strip()
                    meaning_part = parts[1].strip() if len(parts) > 1 else ""
                    
                    # Extract word (bỏ các ký tự không cần thiết)
                    word = self.extract_clean_word(word_part)
                    
                    # Extract meaning từ phần back
                    meaning = self.extract_simple_meaning(meaning_part)
                    
                    if word and meaning:
                        word_data = {
                            'word': word,
                            'meaning': meaning,
                            'level': level,
                            'tags': 'adj character-traits',  # Default tags
                            'part_of_speech': 'adjective'
                        }
                        words_data.append(word_data)
                        print(f"   📝 {word}: {meaning[:30]}...")
            
            print(f"   ✅ Trích xuất {len(words_data)} từ")
            
        except Exception as e:
            print(f"   ❌ Lỗi đọc file: {e}")
            print(f"   🔍 Debug: File size: {os.path.getsize(filepath)} bytes")
        
        return words_data
    
    def extract_clean_word(self, word_part):
        """Trích xuất word từ phần đầu line"""
        # Word thường là từ đầu tiên trước khoảng trắng hoặc tab
        word = word_part.split()[0] if word_part.split() else ""
        
        # Clean word: chỉ giữ chữ cái và dấu gạch ngang
        clean_word = re.sub(r'[^\w-]', '', word).lower().strip()
        
        # Validate word
        if (len(clean_word) >= 2 and 
            clean_word.replace('-', '').isalpha() and
            clean_word not in ['the', 'and', 'for', 'are', 'but', 'not']):
            return clean_word
        
        return None
    
    def extract_simple_meaning(self, meaning_part):
        """Trích xuất meaning đơn giản từ phần back"""
        if not meaning_part:
            return "Unknown meaning"
        
        # Tìm nghĩa tiếng Việt (thường ở đầu phần back)
        # Pattern: "thân thiện" hoặc "rộng lượng hào phóng"
        vietnamese_words = []
        words = meaning_part.split()
        
        # Lấy các từ tiếng Việt ở đầu (trước khi gặp từ tiếng Anh)
        for word in words:
            # Check if word contains Vietnamese characters or is short Vietnamese word
            if (len(word) >= 2 and 
                not re.match(r'^[a-zA-Z/\(\)]+$', word) and  # Not English/pronunciation
                not word.startswith('•') and  # Not bullet points
                not word.startswith('📖')):  # Not emoji
                vietnamese_words.append(word)
            elif vietnamese_words:  # Stop when we hit English after Vietnamese
                break
        
        if vietnamese_words:
            return ' '.join(vietnamese_words[:5])  # Max 5 words
        
        # Fallback: take first meaningful part
        clean_text = meaning_part.replace('📖', '').replace('•', '').strip()
        if len(clean_text) > 3:
            return clean_text[:50]
        
        return "Unknown meaning"
    
    def extract_word_info(self, parts, level):
        """Trích xuất word và meaning từ export line"""
        front = parts[0] if len(parts) > 0 else ""
        back = parts[1] if len(parts) > 1 else ""
        tags = parts[2] if len(parts) > 2 else ""
        
        word = self.extract_word_from_html(front)
        meaning = self.extract_meaning_from_html(back)
        
        if word and meaning:
            return {
                'word': word,
                'meaning': meaning,
                'level': level,
                'tags': tags,
                'part_of_speech': self.extract_pos_from_tags(tags)
            }
        
        return None
    
    def extract_word_from_html(self, html_content):
        """Trích xuất từ vựng từ HTML content"""
        # Pattern để tìm word trong class word-main
        word_patterns = [
            r'<div class="word-main">([^<]+)</div>',
            r'<div class=""word-main"">([^<]+)</div>',  # Double quotes
            r'word-main[^>]*>([^<]+)<',
            r'<div[^>]*word-main[^>]*>([^<]+)</div>'
        ]
        
        for pattern in word_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                word = match.group(1).strip().lower()
                if len(word) >= 2 and word.replace('-', '').isalpha():
                    return word
        
        # Fallback: extract first word from clean text
        clean_text = re.sub(r'<[^>]+>', ' ', html_content)
        words = clean_text.split()
        for word in words:
            clean_word = re.sub(r'[^\w-]', '', word).lower()
            if (len(clean_word) >= 3 and 
                clean_word.replace('-', '').isalpha() and
                clean_word not in ['the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'div', 'class']):
                return clean_word
        
        return None
    
    def extract_meaning_from_html(self, html_content):
        """Trích xuất nghĩa từ HTML back content"""
        # Pattern để tìm nghĩa tiếng Việt
        meaning_patterns = [
            r'<div class="vietnamese-meaning">([^<]+)</div>',
            r'<div class=""vietnamese-meaning"">([^<]+)</div>',  # Double quotes
            r'vietnamese-meaning[^>]*>([^<]+)<',
            r'<div[^>]*vietnamese-meaning[^>]*>([^<]+)</div>'
        ]
        
        for pattern in meaning_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                meaning = match.group(1).strip()
                if len(meaning) > 2:
                    return meaning
        
        # Fallback: tìm definitions từ Langeek
        langeek_pattern = r'<div class="definition-item">• ([^<]+)</div>'
        langeek_matches = re.findall(langeek_pattern, html_content, re.IGNORECASE)
        if langeek_matches:
            return langeek_matches[0]  # Lấy definition đầu tiên
        
        # Fallback cuối: clean text và lấy câu dài nhất
        clean_text = re.sub(r'<[^>]+>', ' ', html_content)
        clean_text = ' '.join(clean_text.split())
        
        if len(clean_text.strip()) > 5:
            return clean_text.strip()[:150]
        
        return "Unknown meaning"
    
    def extract_pos_from_tags(self, tags):
        """Trích xuất part of speech từ tags"""
        if not tags:
            return 'unknown'
            
        pos_patterns = {
            'adjective': ['adj', 'adjective'],
            'noun': ['noun', 'n'],
            'verb': ['verb', 'v'],
            'adverb': ['adv', 'adverb']
        }
        
        tags_lower = tags.lower()
        for pos, patterns in pos_patterns.items():
            if any(pattern in tags_lower for pattern in patterns):
                return pos
        
        return 'unknown'
    
    def process_all_files(self):
        """Xử lý tất cả export files"""
        print("🔍 Tìm kiếm export files...")
        
        export_files = self.find_export_files()
        if not export_files:
            return False
        
        print(f"\n📊 Xử lý {len(export_files)} files...")
        
        total_words = 0
        for level, filepath in export_files.items():
            words_data = self.parse_export_file(filepath, level)
            self.proficiency_data[level] = words_data
            total_words += len(words_data)
        
        print(f"\n✅ Tổng cộng: {total_words} từ vựng")
        print("📈 Phân bố theo level:")
        for level, words in self.proficiency_data.items():
            if words:
                print(f"   {level.title()}: {len(words)} từ")
        
        return True
    
    def generate_prompts(self):
        """Tạo AI prompts đơn giản"""
        prompts = {}
        
        # ChatGPT Voice prompt for learning words
        if self.proficiency_data['learning']:
            learning_words = [w['word'] for w in self.proficiency_data['learning'][:15]]
            
            chatgpt_prompt = "# CHATGPT VOICE PRACTICE - LEARNING WORDS\n\n"
            chatgpt_prompt += f"TARGET WORDS: {', '.join(learning_words)}\n\n"
            chatgpt_prompt += "Setup: Switch to ChatGPT Voice Mode and say:\n"
            chatgpt_prompt += "'I'm Vietnamese learning English. Help me practice these personality words in conversation.'\n\n"
            chatgpt_prompt += "Practice Methods:\n"
            chatgpt_prompt += "- Start with simple questions about each word\n"
            chatgpt_prompt += "- Create example sentences together\n"
            chatgpt_prompt += "- Practice pronunciation\n"
            chatgpt_prompt += "- Use words in roleplay scenarios\n"
            
            prompts['chatgpt_voice_learning'] = chatgpt_prompt
        
        # Claude Writing prompt for learning words
        if self.proficiency_data['learning']:
            learning_words = [w['word'] for w in self.proficiency_data['learning'][:15]]
            word_meanings = {}
            for word_data in self.proficiency_data['learning']:
                word_meanings[word_data['word']] = word_data['meaning']
            
            claude_prompt = "# CLAUDE WRITING PRACTICE - LEARNING WORDS\n\n"
            claude_prompt += f"TARGET WORDS: {', '.join(learning_words)}\n\n"
            claude_prompt += "WORD MEANINGS:\n"
            for word, meaning in word_meanings.items():
                claude_prompt += f"- {word}: {meaning}\n"
            claude_prompt += "\nSetup: Copy this prompt to Claude and say:\n"
            claude_prompt += "'Help me practice these personality words through writing exercises.'\n\n"
            claude_prompt += "Practice Methods:\n"
            claude_prompt += "- Write simple sentences using each word\n"
            claude_prompt += "- Create character descriptions\n"
            claude_prompt += "- Write short stories with these personalities\n"
            claude_prompt += "- Get feedback on word usage\n"
            
            prompts['claude_writing_learning'] = claude_prompt
        
        # Study Plan
        total_words = sum(len(words) for words in self.proficiency_data.values())
        
        study_plan = "# PERSONALIZED STUDY PLAN\n\n"
        study_plan += f"Total words analyzed: {total_words}\n"
        study_plan += f"- Mastered: {len(self.proficiency_data['mastered'])} words\n"
        study_plan += f"- Familiar: {len(self.proficiency_data['familiar'])} words\n"
        study_plan += f"- Learning: {len(self.proficiency_data['learning'])} words\n"
        study_plan += f"- Difficult: {len(self.proficiency_data['difficult'])} words\n\n"
        study_plan += "WEEKLY SCHEDULE:\n"
        study_plan += "- Monday: ChatGPT Voice practice (15 min)\n"
        study_plan += "- Tuesday: Claude Writing practice (20 min)\n"
        study_plan += "- Wednesday: Review and repeat difficult words\n"
        study_plan += "- Thursday: Mixed practice with both AI tools\n"
        study_plan += "- Friday: Self-assessment and planning\n\n"
        study_plan += "Remember: Consistency is key! Practice a little every day.\n"
        
        prompts['study_plan'] = study_plan
        
        return prompts
    
    def save_results(self, output_folder='ai_practice_data'):
        """Lưu kết quả"""
        os.makedirs(output_folder, exist_ok=True)
        
        # Save vocabulary analysis
        analysis_data = {
            'total_words': sum(len(words) for words in self.proficiency_data.values()),
            'proficiency_breakdown': {k: len(v) for k, v in self.proficiency_data.items()},
            'detailed_vocabulary': self.proficiency_data,
            'analysis_date': datetime.now().isoformat()
        }
        
        with open(f'{output_folder}/vocabulary_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, indent=2, ensure_ascii=False)
        
        # Generate and save prompts
        prompts = self.generate_prompts()
        for prompt_type, prompt_content in prompts.items():
            with open(f'{output_folder}/{prompt_type}_prompt.txt', 'w', encoding='utf-8') as f:
                f.write(prompt_content)
        
        # Save word lists by level
        for level, words in self.proficiency_data.items():
            if words:
                word_list = []
                for word_data in words:
                    word_list.append(f"{word_data['word']}: {word_data['meaning']}")
                
                with open(f'{output_folder}/{level}_vocabulary.txt', 'w', encoding='utf-8') as f:
                    f.write('\n'.join(word_list))
        
        print(f"\n✅ Đã lưu kết quả tại: {output_folder}/")
        print(f"📁 Files được tạo:")
        print(f"   📊 vocabulary_analysis.json")
        print(f"   🎙️ chatgpt_voice_learning_prompt.txt")
        print(f"   ✍️ claude_writing_learning_prompt.txt")
        print(f"   📅 study_plan_prompt.txt")

def main():
    """Main function - Updated cho format export mới"""
    print("🎯 ANKI LEARNING PROGRESS TO AI PRACTICE CONVERTER")
    print("="*60)
    
    try:
        analyzer = AnkiLearningAnalyzer()
        
        # Setup folder structure
        analyzer.setup_folder_structure()
        
        # Check for test files trong current directory
        test_files = [
            "learning.txt", 
            "Selected Notes.txt",
            "mastered.txt", 
            "familiar.txt", 
            "difficult.txt"
        ]
        
        found_test_files = []
        for test_file in test_files:
            if os.path.exists(test_file):
                found_test_files.append(test_file)
                print(f"🔍 Tìm thấy file: {test_file}")
        
        if found_test_files:
            print(f"\n📁 Copying {len(found_test_files)} file(s) vào folder exports...")
            import shutil
            
            for test_file in found_test_files:
                # Determine level từ filename
                if 'master' in test_file.lower():
                    target_name = 'mastered.txt'
                elif 'familiar' in test_file.lower():
                    target_name = 'familiar.txt'
                elif 'difficult' in test_file.lower() or 'hard' in test_file.lower():
                    target_name = 'difficult.txt'
                else:
                    target_name = 'learning.txt'  # Default
                
                target_path = os.path.join(analyzer.exports_folder, target_name)
                shutil.copy2(test_file, target_path)
                print(f"   ✅ {test_file} → {target_name}")
        
        # Process files
        success = analyzer.process_all_files()
        if not success:
            print(f"\n💡 Vui lòng:")
            print(f"   1. Đặt file export từ Anki vào folder hiện tại")
            print(f"   2. Hoặc vào folder {analyzer.exports_folder}/")
            print(f"   3. Chạy lại script")
            return
        
        # Generate prompts and save
        analyzer.save_results()
        
        print(f"\n🎉 HOÀN THÀNH PHÂN TÍCH!")
        
        # Show specific prompts based on what was found
        if analyzer.proficiency_data['learning']:
            print(f"\n🎙️ CHATGPT VOICE PRACTICE:")
            print(f"   Copy 'chatgpt_voice_learning_prompt.txt' vào ChatGPT Voice Mode")
            
            print(f"\n✍️ CLAUDE WRITING PRACTICE:")
            print(f"   Copy 'claude_writing_learning_prompt.txt' vào Claude")
        
        # Show word preview
        for level, words in analyzer.proficiency_data.items():
            if words:
                word_list = [w['word'] for w in words[:5]]
                print(f"\n📝 {level.title()} words: {', '.join(word_list)}")
                if len(words) > 5:
                    print(f"    ... và {len(words) - 5} từ khác")
        
        print(f"\n📅 Đọc 'study_plan_prompt.txt' để có kế hoạch học tập!")
        
    except Exception as e:
        print(f"\n❌ LỖI: {e}")
        import traceback
        traceback.print_exc()
        
        # Debug info
        print(f"\n🔍 DEBUG INFO:")
        print(f"   Current directory: {os.getcwd()}")
        print(f"   Files in current dir: {[f for f in os.listdir('.') if f.endswith('.txt')]}")
    
    finally:
        input("\n⏸️  Nhấn Enter để thoát...")

if __name__ == "__main__":
    main()
