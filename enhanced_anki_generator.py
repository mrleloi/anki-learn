import os
import pandas as pd
import requests
from gtts import gTTS
import json
import random
from datetime import datetime

# === CONFIG ===
PIXABAY_API_KEY = '50872335-2b97ba59b3d6f172e1a571e5b'  # API key của bạn
INPUT_FOLDER = 'input'
OUTPUT_FOLDER = 'output'
MEDIA_FOLDER = os.path.join(OUTPUT_FOLDER, 'media')
ANKI_FOLDER = os.path.join(OUTPUT_FOLDER, 'anki_import')

# === SETUP ===
os.makedirs(INPUT_FOLDER, exist_ok=True)  
os.makedirs(MEDIA_FOLDER, exist_ok=True)
os.makedirs(ANKI_FOLDER, exist_ok=True)

# === ENHANCED FUNCTIONS ===
def download_image(word, part_of_speech=None, vietnamese=None):
    """Download hình ảnh thông minh - Ưu tiên Langeek API"""
    image_path = os.path.join(MEDIA_FOLDER, f'{word}.jpg')
    if os.path.exists(image_path):
        print(f"🟡 Đã có ảnh: {word}")
        return f'{word}.jpg'
    
    print(f"🔍 Tìm ảnh cho: {word} ({part_of_speech})...")
    
    # 1. LANGEEK API - Ưu tiên cao nhất (có ảnh + định nghĩa chuẩn)
    image_file, word_data = try_langeek_api(word)
    if image_file:
        return image_file, word_data  # Trả về cả ảnh và data để enrichment
    
    # 2. PEXELS - Backup cho ảnh chất lượng cao
    search_terms = get_smart_search_terms(word, part_of_speech, vietnamese)
    for term in search_terms:
        image_file = try_pexels(word, term)
        if image_file:
            return image_file, None
    
    # 3. UNSPLASH - Backup artistic
    for term in search_terms:
        image_file = try_unsplash(word, term)
        if image_file:
            return image_file, None
    
    # 4. PIXABAY - Fallback
    for term in search_terms:
        image_file = try_pixabay(word, term)
        if image_file:
            return image_file, None
    
    # 5. TEXT IMAGE - Last resort
    print(f"⚠️  Không tìm thấy ảnh online, tạo ảnh text...")
    return create_fallback_image(word, vietnamese), None

def try_langeek_api(word):
    """Thử tải ảnh và thông tin từ Langeek API - Nguồn tốt nhất"""
    image_path = os.path.join(MEDIA_FOLDER, f'{word}.jpg')
    
    # Langeek API endpoint
    url = f"https://api.langeek.co/v1/cs/en/word/?term={word}&filter=,inCategory,photo"
    
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://dictionary.langeek.co',
        'Referer': 'https://dictionary.langeek.co/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            if data and len(data) > 0:
                word_info = data[0]
                
                # Lấy ảnh từ translation đầu tiên có ảnh
                photo_url = None
                enhanced_data = {
                    'definitions': [],
                    'examples': [],
                    'synonyms': [],
                    'part_of_speech': None
                }
                
                # Tìm ảnh và thu thập thông tin
                if 'translations' in word_info:
                    for pos, translations in word_info['translations'].items():
                        enhanced_data['part_of_speech'] = pos
                        for translation in translations:
                            # Thu thập định nghĩa
                            if 'translation' in translation:
                                enhanced_data['definitions'].append(translation['translation'])
                            
                            # Lấy ảnh đầu tiên tìm thấy
                            if not photo_url and translation.get('wordPhoto') and translation['wordPhoto'].get('photo'):
                                photo_url = translation['wordPhoto']['photo']
                
                # Download ảnh nếu có
                if photo_url:
                    img_response = requests.get(photo_url, timeout=15)
                    if img_response.status_code == 200:
                        with open(image_path, 'wb') as f:
                            f.write(img_response.content)
                        
                        print(f'✅ Langeek: {word} + enhanced data')
                        return f'{word}.jpg', enhanced_data
                
                print(f'📝 Langeek: {word} - có data nhưng không có ảnh')
                return None, enhanced_data
                
    except Exception as e:
        print(f'⚠️  Langeek API error for {word}: {str(e)[:50]}...')
    
    return None, None

def get_langeek_examples(word):
    """Lấy example sentences từ Langeek"""
    try:
        # Truy cập trang word detail để lấy examples
        word_url = f"https://dictionary.langeek.co/en/word/search?term={word}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
        }
        
        response = requests.get(word_url, headers=headers, timeout=10)
        if response.status_code == 200:
            # Parse HTML để tìm examples (cần thêm BeautifulSoup)
            # Tạm thời return empty, có thể implement sau
            return []
            
    except Exception as e:
        pass
    
    return []

def create_enhanced_vocabulary_card(row, image_file, audio_file, langeek_data=None):
    """Tạo thẻ từ vựng với thông tin được enhancement từ Langeek"""
    word = row['Word']
    pronunciation = row['Pronunciation'] if pd.notna(row['Pronunciation']) else ''
    vietnamese = row['Vietnamese'] if pd.notna(row['Vietnamese']) else ''
    pos = row['Part_of_Speech'] if pd.notna(row['Part_of_Speech']) else ''
    example = row['Example_Sentence'] if pd.notna(row['Example_Sentence']) else ''
    
    # Sử dụng data từ Langeek nếu có
    enhanced_definitions = []
    enhanced_examples = []
    
    if langeek_data:
        enhanced_definitions = langeek_data.get('definitions', [])
        enhanced_examples = langeek_data.get('examples', [])
        if not pos and langeek_data.get('part_of_speech'):
            pos = langeek_data['part_of_speech']
    
    # Front side - Clean and focused
    front = f"""
<div class="vocab-front">
    <div class="word-main">{word}</div>
    <div class="pronunciation">{pronunciation}</div>
    <div class="part-speech">({pos})</div>
    {f'<div class="image-container"><img src="{image_file}" class="word-image" /></div>' if image_file else ''}
    <div class="audio-section">
        {f'[sound:{audio_file}]' if audio_file else ''}
        <div class="audio-hint">🔊 Click to hear pronunciation</div>
    </div>
    <div class="recall-hint">💭 What does this word mean?</div>
</div>

<style>
.vocab-front {{
    font-family: 'Segoe UI', Arial, sans-serif;
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
}}

.word-main {{
    font-size: 32px;
    font-weight: bold;
    margin-bottom: 10px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    letter-spacing: 1px;
}}

.pronunciation {{
    font-size: 18px;
    font-style: italic;
    margin-bottom: 8px;
    opacity: 0.9;
}}

.part-speech {{
    font-size: 14px;
    margin-bottom: 20px;
    opacity: 0.8;
}}

.image-container {{
    margin: 20px 0;
}}

.word-image {{
    max-width: 220px;
    max-height: 160px;
    border-radius: 12px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    border: 3px solid rgba(255,255,255,0.8);
}}

.audio-section {{
    margin: 15px 0;
}}

.audio-hint {{
    font-size: 12px;
    opacity: 0.7;
    margin-top: 5px;
}}

.recall-hint {{
    font-size: 14px;
    margin-top: 20px;
    padding: 10px;
    background: rgba(255,255,255,0.2);
    border-radius: 8px;
    border-left: 4px solid #FFD700;
}}
</style>
    """
    
    # Back side - Enhanced với Langeek data
    definitions_html = ""
    if enhanced_definitions:
        definitions_html = f"""
        <div class="langeek-definitions">
            <div class="section-title">📖 Definitions (Langeek):</div>
            {"".join([f'<div class="definition-item">• {definition}</div>' for definition in enhanced_definitions[:3]])}
        </div>
        """
    
    main_definition = vietnamese
    if enhanced_definitions and not vietnamese:
        main_definition = enhanced_definitions[0]
    
    back = f"""
<div class="vocab-back">
    <div class="answer-section">
        <div class="vietnamese-meaning">{main_definition}</div>
        <div class="word-repeat">{word}</div>
        <div class="pronunciation-repeat">{pronunciation}</div>
    </div>
    
    {definitions_html}
    
    {f'''<div class="example-section">
        <div class="section-title">📝 Example:</div>
        <div class="example-text">{example}</div>
    </div>''' if example else ''}
    
    <div class="memory-tips">
        <div class="section-title">🧠 Memory Tips:</div>
        <div class="tip-item">• Use this word in 3 sentences today</div>
        <div class="tip-item">• Connect to someone you know with this trait</div>
        <div class="tip-item">• Visualize the image when saying the word</div>
    </div>
    
    <div class="difficulty-rating">
        <div class="section-title">⭐ Rate this card:</div>
        <div class="rating-hint">Again (red) | Hard (orange) | Good (green) | Easy (blue)</div>
    </div>
</div>

<style>
.vocab-back {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
}}

.answer-section {{
    text-align: center;
    margin-bottom: 25px;
    padding: 20px;
    background: rgba(255,255,255,0.15);
    border-radius: 12px;
    border: 2px solid rgba(255,255,255,0.3);
}}

.vietnamese-meaning {{
    font-size: 28px;
    font-weight: bold;
    color: #FFD700;
    margin-bottom: 10px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}}

.word-repeat {{
    font-size: 22px;
    font-weight: bold;
    margin-bottom: 5px;
}}

.pronunciation-repeat {{
    font-size: 16px;
    font-style: italic;
    opacity: 0.9;
}}

.langeek-definitions {{
    margin: 20px 0;
    padding: 15px;
    background: rgba(255,255,255,0.1);
    border-radius: 10px;
    border-left: 4px solid #00CED1;
}}

.definition-item {{
    font-size: 14px;
    margin: 5px 0;
    opacity: 0.95;
    line-height: 1.4;
}}

.example-section {{
    margin: 20px 0;
    padding: 15px;
    background: rgba(255,255,255,0.1);
    border-radius: 10px;
    border-left: 4px solid #4CAF50;
}}

.memory-tips {{
    margin: 20px 0;
    padding: 15px;
    background: rgba(255,255,255,0.1);
    border-radius: 10px;
    border-left: 4px solid #FF9800;
}}

.difficulty-rating {{
    margin-top: 20px;
    padding: 15px;
    background: rgba(255,255,255,0.1);
    border-radius: 10px;
    text-align: center;
}}

.section-title {{
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 10px;
    color: #FFD700;
}}

.example-text {{
    font-style: italic;
    font-size: 16px;
    line-height: 1.5;
}}

.tip-item {{
    font-size: 14px;
    margin: 5px 0;
    opacity: 0.9;
}}

.rating-hint {{
    font-size: 12px;
    opacity: 0.7;
    margin-top: 5px;
}}
</style>
    """
    
    return [front.strip(), back.strip(), f'vocabulary {pos} character-traits enhanced']

def get_smart_search_terms(word, part_of_speech, vietnamese):
    """Tạo search terms thông minh theo từ loại"""
    search_terms = []
    
    if part_of_speech:
        pos = part_of_speech.lower().strip()
        
        if pos in ['adj', 'adjective']:
            # Adjectives - personality traits
            search_terms = [
                f"{word} person expression",
                f"{word} facial emotion", 
                f"person looking {word}",
                f"{word} face portrait",
                f"{word} personality",
                word
            ]
            
        elif pos in ['noun', 'n']:
            # Nouns - concepts or objects
            search_terms = [
                f"{word} concept illustration",
                word,
                f"{word} symbol",
                f"{word} representation"
            ]
            
        elif pos in ['verb', 'v']:
            # Verbs - actions
            search_terms = [
                f"person {word}",
                f"people {word}",
                f"{word} action",
                word
            ]
            
        elif pos in ['adv', 'adverb']:
            # Adverbs - behaviors
            search_terms = [
                f"person behaving {word}",
                f"{word} manner",
                word
            ]
    else:
        search_terms = [word]
    
    # Thêm Vietnamese context nếu có
    if vietnamese:
        viet_main = vietnamese.split(',')[0].strip().split(' ')[0]
        if len(viet_main) > 2:
            search_terms.insert(1, f"{word} {viet_main}")
    
    return search_terms

def try_pexels(word, search_term):
    """Thử tải ảnh từ Pexels - Ưu tiên cao nhất"""
    image_path = os.path.join(MEDIA_FOLDER, f'{word}.jpg')
    
    # Pexels API key - THAY ĐỔI NÀY
    PEXELS_API_KEY = "563492ad6f917000010000014c33b45043204e8ebb5ed8c3ba57c56b"  # Demo key, hãy thay bằng key của bạn
    
    headers = {'Authorization': PEXELS_API_KEY}
    url = f"https://api.pexels.com/v1/search?query={search_term.replace(' ', '+')}&orientation=landscape&size=medium&per_page=5"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('photos'):
                # Lấy ảnh đầu tiên (chất lượng tốt nhất)
                best_photo = data['photos'][0]
                img_url = best_photo['src']['medium']
                
                img_data = requests.get(img_url, timeout=15).content
                with open(image_path, 'wb') as f:
                    f.write(img_data)
                    
                print(f'✅ Pexels: {word} (từ khóa: {search_term})')
                return f'{word}.jpg'
    except Exception as e:
        pass
    return None

def try_unsplash(word, search_term):
    """Thử tải ảnh từ Unsplash - Backup"""
    image_path = os.path.join(MEDIA_FOLDER, f'{word}.jpg')
    
    # Unsplash Access Key - THAY ĐỔI NÀY
    UNSPLASH_ACCESS_KEY = "YOUR_UNSPLASH_ACCESS_KEY"  # Lấy miễn phí tại https://unsplash.com/developers
    
    if UNSPLASH_ACCESS_KEY == "YOUR_UNSPLASH_ACCESS_KEY":
        return None  # Skip nếu chưa setup
    
    url = f"https://api.unsplash.com/search/photos?query={search_term.replace(' ', '+')}&orientation=landscape&per_page=5&client_id={UNSPLASH_ACCESS_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('results'):
                best_photo = data['results'][0]
                img_url = best_photo['urls']['regular']
                
                img_data = requests.get(img_url, timeout=15).content
                with open(image_path, 'wb') as f:
                    f.write(img_data)
                    
                print(f'✅ Unsplash: {word} (từ khóa: {search_term})')
                return f'{word}.jpg'
    except Exception as e:
        pass
    return None

def try_pixabay(word, search_term):
    """Thử tải ảnh từ Pixabay - Fallback"""
    image_path = os.path.join(MEDIA_FOLDER, f'{word}.jpg')
    
    # Pixabay với category people cho personality traits
    url = f'https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={search_term.replace(" ", "+")}&image_type=photo&orientation=horizontal&category=people&min_width=640&min_height=480&safesearch=true&per_page=5'
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('hits'):
                # Ưu tiên ảnh có nhiều views
                best_image = max(data['hits'], key=lambda x: x.get('views', 0))
                img_url = best_image['webformatURL']
                
                img_data = requests.get(img_url, timeout=15).content
                with open(image_path, 'wb') as f:
                    f.write(img_data)
                    
                print(f'✅ Pixabay: {word} (từ khóa: {search_term})')
                return f'{word}.jpg'
    except Exception as e:
        pass
    return None

def create_fallback_image(word, vietnamese=None):
    """Tạo ảnh text fallback nếu không tìm thấy ảnh"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap
        
        # Tạo ảnh với text
        img = Image.new('RGB', (400, 300), color='#667eea')
        draw = ImageDraw.Draw(img)
        
        # Thử load font, fallback về default nếu không có
        try:
            font_large = ImageFont.truetype("arial.ttf", 40)
            font_small = ImageFont.truetype("arial.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Vẽ từ chính
        text_bbox = draw.textbbox((0, 0), word.upper(), font=font_large)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (400 - text_width) // 2
        y = 100
        draw.text((x, y), word.upper(), font=font_large, fill='white')
        
        # Vẽ nghĩa tiếng Việt nếu có
        if vietnamese:
            viet_text = vietnamese[:30] + "..." if len(vietnamese) > 30 else vietnamese
            viet_bbox = draw.textbbox((0, 0), viet_text, font=font_small)
            viet_width = viet_bbox[2] - viet_bbox[0]
            
            x_viet = (400 - viet_width) // 2
            draw.text((x_viet, y + 60), viet_text, font=font_small, fill='#FFD700')
        
        # Lưu ảnh
        image_path = os.path.join(MEDIA_FOLDER, f'{word}.jpg')
        img.save(image_path, 'JPEG', quality=85)
        print(f'🎨 Tạo ảnh text: {word}')
        return f'{word}.jpg'
        
    except ImportError:
        print(f'⚠️  Cần cài PIL để tạo ảnh text: pip install Pillow')
        return None
    except Exception as e:
        print(f'❌ Lỗi tạo ảnh text cho {word}: {e}')
        return None

def download_audio(word, pronunciation=None):
    """Download audio phát âm với nhiều giọng"""
    audio_path = os.path.join(MEDIA_FOLDER, f'{word}.mp3')
    if os.path.exists(audio_path):
        print(f"🟡 Đã có audio: {word}")
        return f'{word}.mp3'
    
    try:
        # Tạo text phát âm rõ ràng hơn
        text_to_speak = f"{word}. {word}."  # Lặp lại 2 lần
        
        tts = gTTS(text=text_to_speak, lang='en', tld='com', slow=False)
        tts.save(audio_path)
        print(f'✅ Tải audio: {word}')
        return f'{word}.mp3'
    except Exception as e:
        print(f'❌ Lỗi audio {word}: {e}')
        return None

def create_vocabulary_card(row, image_file, audio_file):
    """Tạo thẻ từ vựng chính với thiết kế tối ưu cho học"""
    word = row['Word']
    pronunciation = row['Pronunciation'] if pd.notna(row['Pronunciation']) else ''
    vietnamese = row['Vietnamese'] if pd.notna(row['Vietnamese']) else ''
    pos = row['Part_of_Speech'] if pd.notna(row['Part_of_Speech']) else ''
    example = row['Example_Sentence'] if pd.notna(row['Example_Sentence']) else ''
    
    # Front side - Chỉ từ + phát âm + ảnh để test recall
    front = f"""
<div class="vocab-front">
    <div class="word-main">{word}</div>
    <div class="pronunciation">{pronunciation}</div>
    <div class="part-speech">({pos})</div>
    {f'<div class="image-container"><img src="{image_file}" class="word-image" /></div>' if image_file else ''}
    <div class="audio-section">
        {f'[sound:{audio_file}]' if audio_file else ''}
        <div class="audio-hint">🔊 Click to hear pronunciation</div>
    </div>
    <div class="recall-hint">💭 What does this word mean?</div>
</div>

<style>
.vocab-front {{
    font-family: 'Segoe UI', Arial, sans-serif;
    text-align: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
}}

.word-main {{
    font-size: 32px;
    font-weight: bold;
    margin-bottom: 10px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    letter-spacing: 1px;
}}

.pronunciation {{
    font-size: 18px;
    font-style: italic;
    margin-bottom: 8px;
    opacity: 0.9;
}}

.part-speech {{
    font-size: 14px;
    margin-bottom: 20px;
    opacity: 0.8;
}}

.image-container {{
    margin: 20px 0;
}}

.word-image {{
    max-width: 220px;
    max-height: 160px;
    border-radius: 12px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    border: 3px solid rgba(255,255,255,0.8);
}}

.audio-section {{
    margin: 15px 0;
}}

.audio-hint {{
    font-size: 12px;
    opacity: 0.7;
    margin-top: 5px;
}}

.recall-hint {{
    font-size: 14px;
    margin-top: 20px;
    padding: 10px;
    background: rgba(255,255,255,0.2);
    border-radius: 8px;
    border-left: 4px solid #FFD700;
}}
</style>
    """
    
    # Back side - Đáp án đầy đủ với mnemonic tips
    back = f"""
<div class="vocab-back">
    <div class="answer-section">
        <div class="vietnamese-meaning">{vietnamese}</div>
        <div class="word-repeat">{word}</div>
        <div class="pronunciation-repeat">{pronunciation}</div>
    </div>
    
    {f'''<div class="example-section">
        <div class="section-title">📝 Example:</div>
        <div class="example-text">{example}</div>
    </div>''' if example else ''}
    
    <div class="memory-tips">
        <div class="section-title">🧠 Memory Tips:</div>
        <div class="tip-item">• Use this word in 3 sentences today</div>
        <div class="tip-item">• Connect to someone you know with this trait</div>
        <div class="tip-item">• Visualize the image when saying the word</div>
    </div>
    
    <div class="difficulty-rating">
        <div class="section-title">⭐ Rate this card:</div>
        <div class="rating-hint">Again (red) | Hard (orange) | Good (green) | Easy (blue)</div>
    </div>
</div>

<style>
.vocab-back {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
}}

.answer-section {{
    text-align: center;
    margin-bottom: 25px;
    padding: 20px;
    background: rgba(255,255,255,0.15);
    border-radius: 12px;
    border: 2px solid rgba(255,255,255,0.3);
}}

.vietnamese-meaning {{
    font-size: 28px;
    font-weight: bold;
    color: #FFD700;
    margin-bottom: 10px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}}

.word-repeat {{
    font-size: 22px;
    font-weight: bold;
    margin-bottom: 5px;
}}

.pronunciation-repeat {{
    font-size: 16px;
    font-style: italic;
    opacity: 0.9;
}}

.example-section {{
    margin: 20px 0;
    padding: 15px;
    background: rgba(255,255,255,0.1);
    border-radius: 10px;
    border-left: 4px solid #4CAF50;
}}

.memory-tips {{
    margin: 20px 0;
    padding: 15px;
    background: rgba(255,255,255,0.1);
    border-radius: 10px;
    border-left: 4px solid #FF9800;
}}

.difficulty-rating {{
    margin-top: 20px;
    padding: 15px;
    background: rgba(255,255,255,0.1);
    border-radius: 10px;
    text-align: center;
}}

.section-title {{
    font-size: 16px;
    font-weight: bold;
    margin-bottom: 10px;
    color: #FFD700;
}}

.example-text {{
    font-style: italic;
    font-size: 16px;
    line-height: 1.5;
}}

.tip-item {{
    font-size: 14px;
    margin: 5px 0;
    opacity: 0.9;
}}

.rating-hint {{
    font-size: 12px;
    opacity: 0.7;
    margin-top: 5px;
}}
</style>
    """
    
    return [front.strip(), back.strip(), f'vocabulary {pos} character-traits']

def create_cloze_fill_blank_card(row):
    """Tạo thẻ Cloze với input tự động focus và kiểm tra đáp án"""
    if pd.isna(row.get('Fill_in_Blank_Question')):
        return None
        
    question = row['Fill_in_Blank_Question']
    answer = row['Fill_in_Blank_Answer'] if pd.notna(row.get('Fill_in_Blank_Answer')) else row['Word']
    word = row['Word']
    vietnamese = row['Vietnamese'] if pd.notna(row['Vietnamese']) else ''
    
    # Cloze card format - Anki sẽ tự động tạo input field
    cloze_text = question.replace('_______', f'{{{{c1::{answer}::Type the word}}}}')
    
    # Enhanced cloze with styling and hints
    front = f"""
<div class="cloze-container">
    <div class="instruction">💡 Type the missing word and press Enter</div>
    <div class="question-text">{cloze_text}</div>
    <div class="context-hint">
        <div class="hint-title">🧩 Context clues:</div>
        <div class="hint-text">Think about personality traits...</div>
        <div class="vietnamese-hint">Nghĩa tiếng Việt: {vietnamese}</div>
    </div>
</div>

<style>
.cloze-container {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    color: #2c3e50;
}}

.instruction {{
    text-align: center;
    font-size: 16px;
    font-weight: bold;
    color: #e74c3c;
    margin-bottom: 20px;
    padding: 10px;
    background: rgba(255,255,255,0.8);
    border-radius: 8px;
    border-left: 4px solid #e74c3c;
}}

.question-text {{
    font-size: 20px;
    line-height: 1.6;
    text-align: center;
    margin: 25px 0;
    padding: 20px;
    background: rgba(255,255,255,0.9);
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}

.context-hint {{
    margin-top: 20px;
    padding: 15px;
    background: rgba(255,255,255,0.7);
    border-radius: 10px;
    border-left: 4px solid #3498db;
}}

.hint-title {{
    font-weight: bold;
    color: #3498db;
    margin-bottom: 8px;
}}

.hint-text {{
    font-style: italic;
    margin-bottom: 5px;
}}

.vietnamese-hint {{
    font-size: 14px;
    color: #27ae60;
    font-weight: bold;
}}

/* Style for Anki's cloze input */
.cloze {{
    background: #fff3cd !important;
    border: 2px solid #ffc107 !important;
    border-radius: 5px !important;
    padding: 5px 10px !important;
    font-size: 18px !important;
    font-weight: bold !important;
    color: #856404 !important;
    min-width: 120px !important;
}}
</style>

<script>
// Auto-focus on input when card loads
setTimeout(function() {{
    var input = document.querySelector('input[type="text"]');
    if (input) {{
        input.focus();
        input.select();
    }}
}}, 100);

// Enter key handling for immediate feedback
document.addEventListener('keydown', function(e) {{
    if (e.key === 'Enter') {{
        var input = document.querySelector('input[type="text"]');
        if (input && input.value.trim()) {{
            // Anki will handle the answer checking
            setTimeout(function() {{
                if (input.value.toLowerCase().trim() === '{answer.lower()}') {{
                    input.style.background = '#d4edda';
                    input.style.borderColor = '#28a745';
                }} else {{
                    input.style.background = '#f8d7da'; 
                    input.style.borderColor = '#dc3545';
                }}
            }}, 100);
        }}
    }}
}});
</script>
    """
    
    return [front.strip(), '', f'fill-in-blank cloze character-traits']

def create_pronunciation_card(row, audio_file):
    """Tạo thẻ luyện phát âm với feedback"""
    if not audio_file or pd.isna(row.get('Pronunciation')):
        return None
        
    word = row['Word']
    pronunciation = row['Pronunciation']
    vietnamese = row['Vietnamese'] if pd.notna(row['Vietnamese']) else ''
    
    front = f"""
<div class="pronunciation-front">
    <div class="instruction">🎧 Listen and pronounce the word</div>
    <div class="audio-player">
        [sound:{audio_file}]
    </div>
    <div class="pronunciation-task">
        <div class="task-title">📢 Your task:</div>
        <div class="task-list">
            <div class="task-item">1. Listen to the audio</div>
            <div class="task-item">2. Repeat out loud 3 times</div>
            <div class="task-item">3. Check your pronunciation</div>
        </div>
    </div>
    <div class="hint-section">
        <div class="hint">💡 Try to mimic the rhythm and stress</div>
    </div>
</div>

<style>
.pronunciation-front {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    color: #2c3e50;
    text-align: center;
}}

.instruction {{
    font-size: 18px;
    font-weight: bold;
    color: #e67e22;
    margin-bottom: 20px;
    padding: 12px;
    background: rgba(255,255,255,0.8);
    border-radius: 8px;
    border-left: 4px solid #e67e22;
}}

.audio-player {{
    margin: 25px 0;
    padding: 20px;
    background: rgba(255,255,255,0.9);
    border-radius: 12px;
    font-size: 24px;
}}

.pronunciation-task {{
    margin: 20px 0;
    padding: 20px;
    background: rgba(255,255,255,0.8);
    border-radius: 10px;
    text-align: left;
}}

.task-title {{
    font-weight: bold;
    color: #8e44ad;
    margin-bottom: 12px;
    text-align: center;
}}

.task-item {{
    margin: 8px 0;
    padding: 8px;
    background: rgba(142, 68, 173, 0.1);
    border-radius: 5px;
    border-left: 3px solid #8e44ad;
}}

.hint-section {{
    margin-top: 20px;
}}

.hint {{
    font-style: italic;
    color: #7f8c8d;
    font-size: 14px;
}}
</style>
    """
    
    back = f"""
<div class="pronunciation-back">
    <div class="word-display">{word}</div>
    <div class="pronunciation-display">{pronunciation}</div>
    <div class="meaning-display">{vietnamese}</div>
    
    <div class="feedback-section">
        <div class="feedback-title">✅ Pronunciation Tips:</div>
        <div class="feedback-content">
            <div class="tip">• Break it down: {pronunciation}</div>
            <div class="tip">• Practice slowly first, then speed up</div>
            <div class="tip">• Record yourself and compare</div>
        </div>
    </div>
    
    <div class="self-assessment">
        <div class="assessment-title">🎯 Rate your pronunciation:</div>
        <div class="assessment-options">
            <span class="rate-option again">😰 Need more practice</span>
            <span class="rate-option hard">😐 Getting there</span>
            <span class="rate-option good">😊 Pretty good</span>
            <span class="rate-option easy">😎 Nailed it!</span>
        </div>
    </div>
</div>

<style>
.pronunciation-back {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    color: #2c3e50;
    text-align: center;
}}

.word-display {{
    font-size: 32px;
    font-weight: bold;
    color: #2980b9;
    margin-bottom: 10px;
}}

.pronunciation-display {{
    font-size: 20px;
    font-style: italic;
    color: #e67e22;
    margin-bottom: 8px;
}}

.meaning-display {{
    font-size: 18px;
    color: #27ae60;
    margin-bottom: 25px;
    font-weight: bold;
}}

.feedback-section {{
    margin: 20px 0;
    padding: 20px;
    background: rgba(255,255,255,0.8);
    border-radius: 10px;
    text-align: left;
}}

.feedback-title {{
    font-weight: bold;
    color: #27ae60;
    margin-bottom: 12px;
    text-align: center;
}}

.tip {{
    margin: 8px 0;
    padding: 8px;
    background: rgba(39, 174, 96, 0.1);
    border-radius: 5px;
    border-left: 3px solid #27ae60;
}}

.self-assessment {{
    margin-top: 20px;
    padding: 15px;
    background: rgba(255,255,255,0.9);
    border-radius: 10px;
}}

.assessment-title {{
    font-weight: bold;
    margin-bottom: 15px;
    color: #8e44ad;
}}

.assessment-options {{
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
}}

.rate-option {{
    padding: 8px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
    cursor: pointer;
}}

.rate-option.again {{ background: #ffebee; color: #c62828; }}
.rate-option.hard {{ background: #fff3e0; color: #ef6c00; }}
.rate-option.good {{ background: #e8f5e8; color: #2e7d32; }}
.rate-option.easy {{ background: #e3f2fd; color: #1565c0; }}
</style>
    """
    
    return [front.strip(), back.strip(), f'pronunciation audio character-traits']

def create_exercise_card(row):
    """Tạo thẻ bài tập từ file exercises.csv"""
    question = row['Question']
    answer = row['Answer']
    exercise_type = row['Type']
    difficulty = row['Difficulty']
    context = row['Context']
    
    if exercise_type == 'definition':
        front = f"""
        <div class="exercise-front definition">
            <div class="exercise-header">
                <span class="exercise-type">📖 Definition Exercise</span>
                <span class="difficulty {difficulty}">{difficulty.upper()}</span>
            </div>
            <div class="question-content">
                {question}
            </div>
            <div class="instruction">💭 Think of the personality trait that fits</div>
        </div>
        """
    else:  # dialogue
        front = f"""
        <div class="exercise-front dialogue">
            <div class="exercise-header">
                <span class="exercise-type">💬 Dialogue Exercise</span>
                <span class="difficulty {difficulty}">{difficulty.upper()}</span>
            </div>
            <div class="question-content">
                {question.replace('B:', '<br><br><strong>B:</strong>').replace('A:', '<strong>A:</strong>')}
            </div>
            <div class="instruction">💭 What word completes the dialogue?</div>
        </div>
        """
    
    back = f"""
    <div class="exercise-back">
        <div class="answer-reveal">
            <div class="answer-label">✅ Answer:</div>
            <div class="answer-text">{answer}</div>
        </div>
        <div class="complete-sentence">
            <div class="complete-label">📝 Complete sentence:</div>
            <div class="complete-text">
                {question.replace('_______', f'<span class="highlight">{answer}</span>').replace('B:', '<br><br><strong>B:</strong>').replace('A:', '<strong>A:</strong>')}
            </div>
        </div>
        <div class="context-info">
            <span class="context-label">Context:</span> {context}
        </div>
    </div>
    """
    
    return [front.strip(), back.strip(), f'exercise {exercise_type} {difficulty} {context.replace(" ", "-")}']

def process_vocabulary_file(file_path):
    """Xử lý file vocabulary với Langeek enhancement"""
    print(f"\n📚 Xử lý file từ vựng: {os.path.basename(file_path)}")
    
    vocabulary_notes = []
    cloze_notes = []
    pronunciation_notes = []
    
    try:
        df = pd.read_csv(file_path)
        print(f"📝 Tìm thấy {len(df)} từ vựng")
        
        for index, row in df.iterrows():
            word = str(row['Word']).strip().lower()
            part_of_speech = row['Part_of_Speech'] if pd.notna(row.get('Part_of_Speech')) else None
            vietnamese = row['Vietnamese'] if pd.notna(row.get('Vietnamese')) else None
            
            print(f"🔄 Xử lý từ: {word} ({part_of_speech})")
            
            # Download media với Langeek enhancement
            download_result = download_image(word, part_of_speech, vietnamese)
            
            # Handle different return formats
            if isinstance(download_result, tuple):
                image_file, langeek_data = download_result
            else:
                image_file, langeek_data = download_result, None
            
            # Nếu không tìm thấy ảnh, tạo ảnh text fallback
            if not image_file:
                image_file = create_fallback_image(word, vietnamese)
            
            audio_file = download_audio(word, row['Pronunciation'] if pd.notna(row.get('Pronunciation')) else None)
            
            # Tạo thẻ từ vựng enhanced
            if langeek_data:
                vocab_note = create_enhanced_vocabulary_card(row, image_file, audio_file, langeek_data)
            else:
                vocab_note = create_vocabulary_card(row, image_file, audio_file)
            vocabulary_notes.append(vocab_note)
            
            # Tạo thẻ cloze nếu có
            cloze_note = create_cloze_fill_blank_card(row)
            if cloze_note:
                cloze_notes.append(cloze_note)
            
            # Tạo thẻ phát âm
            pron_note = create_pronunciation_card(row, audio_file)
            if pron_note:
                pronunciation_notes.append(pron_note)
                
        print(f"✅ Hoàn thành xử lý file từ vựng")
        
    except Exception as e:
        print(f"❌ Lỗi xử lý file từ vựng: {e}")
    
    return vocabulary_notes, cloze_notes, pronunciation_notes

def process_exercise_file(file_path):
    """Xử lý file exercises"""
    print(f"\n📋 Xử lý file bài tập: {os.path.basename(file_path)}")
    
    exercise_notes = []
    
    try:
        df = pd.read_csv(file_path)
        print(f"📝 Tìm thấy {len(df)} bài tập")
        
        for index, row in df.iterrows():
            exercise_note = create_exercise_card(row)
            exercise_notes.append(exercise_note)
            
        print(f"✅ Hoàn thành xử lý file bài tập")
        
    except Exception as e:
        print(f"❌ Lỗi xử lý file bài tập: {e}")
    
    return exercise_notes

def save_anki_file(notes, filename, description):
    """Lưu file Anki với format đơn giản"""
    if not notes:
        print(f"❌ Không có thẻ {description} để tạo!")
        return None
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    full_filename = f'{filename}_{timestamp}.txt'
    output_path = os.path.join(ANKI_FOLDER, full_filename)
    
    # Tạo DataFrame và lưu file
    df = pd.DataFrame(notes, columns=['Front', 'Back', 'Tags'])
    df.to_csv(output_path, sep='\t', index=False, encoding='utf-8')
    
    print(f"✅ Tạo file {description}: {output_path} ({len(notes)} thẻ)")
    return output_path

def create_anki_best_practices_guide(lesson_name):
    """Tạo hướng dẫn best practices học Anki"""
    guide_content = f"""
# 🎓 ANKI BEST PRACTICES - HỌC TỪ VỰNG HIỆU QUẢ NHẤT

## 🎯 CHIẾN LƯỢC HỌC 2 DECK RIÊNG BIỆT

### 📚 DECK 1: VOCABULARY (Từ vựng chính)
**Mục tiêu**: Nhận biết từ → nghĩa (Passive recognition)
**Cách học**:
- ⏰ **Thời gian**: Sáng sớm (7-9h) khi đầu óc tỉnh táo
- 🎯 **New cards/day**: 15-20 từ mới
- 🔄 **Learning steps**: 1m 10m 1d (review nhanh)
- 📖 **Chiến thuật**: 
  * Đọc to từ + nghĩa
  * Liên tưởng với hình ảnh
  * Tạo câu ví dụ trong đầu

### 🧩 DECK 2: CLOZE/FILL-IN-BLANK  
**Mục tiêu**: Sử dụng từ trong ngữ cảnh (Active recall)
**Cách học**:
- ⏰ **Thời gian**: Chiều tối (6-8h) sau khi đã học vocabulary
- 🎯 **New cards/day**: 10-15 thẻ (khó hơn vocabulary)
- 🔄 **Learning steps**: 10m 1d 3d (cần thời gian suy nghĩ)
- 📖 **Chiến thuật**:
  * Đọc cả câu trước khi điền
  * Suy nghĩ logic ngữ cảnh
  * Nói to câu hoàn chỉnh sau khi điền

## 📈 QUY TRÌNH HỌC TỐI ƯU (ĐƯỢC KHOA HỌC CHỨNG MINH)

### 🌅 BUỔI SÁNG (15-20 phút)
1. **Review vocabulary cũ** (5-10 phút)
2. **Học từ mới** (10-15 phút):
   - Xem từ + nghe audio 3 lần
   - Đọc to: "Friendly means thân thiện"
   - Nhìn ảnh và tạo liên tưởng
   - Rate: Again nếu không nhớ, Good nếu nhớ

### 🌆 BUỔI TỐI (15-20 phút)  
1. **Review cloze cũ** (5-10 phút)
2. **Học cloze mới** (10-15 phút):
   - Đọc câu hỏi chậm rãi
   - Suy nghĩ ngữ cảnh và gợi ý
   - Gõ đáp án vào input field
   - Đọc to câu hoàn chỉnh

### 📊 CHẾ ĐỘ ĐÁNH GIÁ THẺ:

**Vocabulary Deck:**
- ✅ **Easy (4 days)**: Biết ngay nghĩa + phát âm đúng
- ✅ **Good (1 day)**: Biết nghĩa nhưng hơi do dự
- ⚠️ **Hard (10m)**: Nhớ mơ hồ, cần gợi ý hình ảnh
- ❌ **Again (1m)**: Không nhớ hoặc nhớ sai

**Cloze Deck:**
- ✅ **Easy (4 days)**: Điền đúng ngay, tự tin 100%
- ✅ **Good (1 day)**: Điền đúng nhưng cần suy nghĩ
- ⚠️ **Hard (10m)**: Biết từ nhưng không chắc ngữ cảnh
- ❌ **Again (1m)**: Điền sai hoặc không biết

## 🧠 TECHNIQUES NÂNG CAO (PRO TIPS)

### 1. 🎭 **MEMORY PALACE METHOD**
- Tưởng tượng nhà của bạn
- Đặt mỗi từ vào một phòng cụ thể
- Ví dụ: "Generous" → Phòng khách (nơi đón khách hào phóng)

### 2. 🔗 **WORD ASSOCIATION CHAINS**
- Friendly → Friend → Friendship → Social
- Tạo chuỗi liên kết giữa các từ đã học

### 3. 🎪 **STORY METHOD**
- Tạo câu chuyện với 5-10 từ mới
- "The **generous** and **friendly** girl was very **reliable**..."

### 4. 🎵 **RHYTHM & RHYME**
- Tạo vần điệu: "Friendly, gently, recently"
- Hát theo giai điệu quen thuộc

### 5. 📱 **REAL-WORLD APPLICATION**
- Mô tả bạn bè bằng từ vừa học
- Post status Facebook bằng tiếng Anh
- Comment YouTube videos với từ mới

## ⚙️ CÀI ĐẶT ANKI TỐI ƯU

### 📚 Vocabulary Deck Settings:
```
New Cards:
- Learning steps: 1m 10m 1d
- Graduating interval: 1 day  
- Easy interval: 4 days
- New cards/day: 20
- Maximum reviews/day: 200

Reviews:
- Maximum interval: 36500 days
- Hard interval: 1.2
- Easy bonus: 1.3
- Interval modifier: 100%
```

### 🧩 Cloze Deck Settings:
```
New Cards:
- Learning steps: 10m 1d 3d
- Graduating interval: 2 days
- Easy interval: 5 days  
- New cards/day: 15
- Maximum reviews/day: 150

Reviews:
- Maximum interval: 36500 days
- Hard interval: 1.2
- Easy bonus: 1.3
- Interval modifier: 90% (khó hơn vocabulary)
```

## 📊 TRACKING PROGRESS

### 🎯 KPIs quan trọng:
- **Retention rate**: >90% cho vocabulary, >85% cho cloze
- **Daily streak**: Mục tiêu 30 ngày liên tục
- **Cards/minute**: 6-8 thẻ vocabulary, 4-5 thẻ cloze
- **New words/week**: 100-140 từ

### 📈 Weekly Review:
- **Monday**: Check retention rates
- **Wednesday**: Adjust new cards/day nếu cần
- **Friday**: Review difficult cards
- **Sunday**: Plan next week's learning

## 🚫 NHỮNG SAI LẦM CẦN TRÁNH

### ❌ **Common Mistakes:**
1. **Học quá nhiều từ mới/ngày** → Overwhelm → Bỏ cuộc
2. **Rate "Easy" quá sớm** → Quên nhanh
3. **Skip audio** → Phát âm sai
4. **Không áp dụng thực tế** → Passive knowledge
5. **Học cả 2 deck cùng lúc** → Confusion

### ✅ **Best Practices:**
1. **Consistency > Intensity**: 20 phút/ngày > 2 tiếng/tuần
2. **Quality > Quantity**: Hiểu sâu 15 từ > Biết nông 50 từ
3. **Active recall**: Tự test không nhìn đáp án
4. **Spaced repetition**: Tin tưởng algorithm của Anki
5. **Real application**: Dùng từ trong cuộc sống thực

## 🎮 GAMIFICATION TECHNIQUES

### 🏆 **Achievement System:**
- 📅 **Week Warrior**: 7 ngày liên tục
- 🎯 **Accuracy Master**: 95% correct rate
- 🚀 **Speed Demon**: 8+ cards/minute
- 🧠 **Memory Champion**: 30+ day streak

### 🎁 **Reward System:**
- 1 tuần streak → Treat yourself ice cream
- 50 từ mới → Watch favorite movie
- 90% retention → Buy new book
- 1 tháng streak → Weekend trip

## 🔬 ADVANCED CUSTOMIZATION

### 📝 **Custom Fields thêm:**
- **Synonym**: Từ đồng nghĩa
- **Antonym**: Từ trái nghĩa  
- **Collocations**: Từ đi cùng
- **Personal Example**: Câu ví dụ riêng
- **Difficulty**: 1-5 stars
- **Last Mistake**: Ghi chú lỗi sai

### 🎨 **Advanced Card Types:**
- **Image Occlusion**: Che hình, đoán từ
- **Audio Recognition**: Nghe → viết từ
- **Reverse Cards**: Tiếng Việt → English
- **Sentence Mining**: Từ real content

## 📚 INTEGRATION WITH OTHER TOOLS

### 🔧 **Anki Add-ons khuyên dùng:**
- **Review Heatmap**: Track daily progress
- **Speed Focus Mode**: Tăng tốc độ review
- **Image Occlusion Enhanced**: Học bằng hình ảnh
- **AwesomeTTS**: Better text-to-speech

### 📱 **Companion Apps:**
- **AnkiDroid**: Học trên điện thoại
- **Forvo**: Pronunciation dictionary
- **Grammarly**: Check writing
- **HelloTalk**: Practice với native speakers

## 🎯 LONG-TERM SUCCESS STRATEGY

### 📅 **3-Month Plan:**
- **Month 1**: Foundation (300-400 words)
- **Month 2**: Expansion (600-800 words)  
- **Month 3**: Mastery (1000+ words)

### 🚀 **Graduation Criteria:**
- Có thể mô tả tính cách ai đó bằng 20+ từ
- Hiểu 90% personality-related content
- Tự tin dùng trong conversation

### 🎓 **Next Level:**
- Chuyển sang chủ đề khác (emotions, activities...)
- Học phrasal verbs với personality traits
- Practice real conversations với native speakers

---

## 💡 **TÓM TẮT GOLDEN RULES:**

1. **2 decks riêng biệt**: Vocabulary (sáng) + Cloze (tối)
2. **Consistency**: 20 phút/ngày > 2 tiếng/tuần  
3. **Active recall**: Không nhìn đáp án khi suy nghĩ
4. **Spaced repetition**: Trust Anki's algorithm
5. **Real application**: Dùng từ vựng trong cuộc sống
6. **Track progress**: Monitor retention rates
7. **Patience**: 3 tháng để thấy kết quả rõ rệt

**Remember**: Anki is not magic. It's a tool. YOUR consistency and effort make the magic happen! 🌟

---
📞 **Questions?** Re-read this guide and experiment with different techniques to find what works best for you!
"""
    
    guide_path = os.path.join(OUTPUT_FOLDER, f'{lesson_name}_anki_best_practices.txt')
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    print(f"✅ Tạo best practices guide: {guide_path}")

def main():
    """Hàm chính - Enhanced version 3"""
    print("🚀 ANKI GENERATOR V3 - PROFESSIONAL EDITION")
    print("=" * 60)
    
    # Kiểm tra thư mục input
    if not os.path.exists(INPUT_FOLDER):
        print(f"❌ Không tìm thấy thư mục {INPUT_FOLDER}")
        print(f"Vui lòng tạo thư mục '{INPUT_FOLDER}' và đặt file CSV vào đó")
        return
    
    # Tìm tất cả file CSV
    csv_files = [f for f in os.listdir(INPUT_FOLDER) if f.endswith('.csv')]
    
    if not csv_files:
        print(f"❌ Không tìm thấy file CSV nào trong {INPUT_FOLDER}")
        print("Vui lòng đặt các file CSV vào thư mục này:")
        print("  - vocabulary_list.csv (danh sách từ vựng)")
        print("  - exercises.csv (bài tập)")
        return
    
    print(f"📁 Tìm thấy {len(csv_files)} file CSV:")
    for file in csv_files:
        print(f"   - {file}")
    
    # Tạo tên bài học
    lesson_name = "character_traits"
    for file in csv_files:
        if 'vocabulary' in file.lower():
            lesson_name = os.path.splitext(file)[0].replace('_vocabulary', '').replace('vocabulary_', '')
            break
    
    print(f"\n📚 Tên bài học: {lesson_name}")
    
    # Khởi tạo các danh sách
    all_vocabulary_notes = []
    all_cloze_notes = []
    all_pronunciation_notes = []
    all_exercise_notes = []
    
    # Xử lý từng file
    for file in csv_files:
        file_path = os.path.join(INPUT_FOLDER, file)
        
        if 'exercise' in file.lower():
            exercise_notes = process_exercise_file(file_path)
            all_exercise_notes.extend(exercise_notes)
        else:
            vocab_notes, cloze_notes, pron_notes = process_vocabulary_file(file_path)
            all_vocabulary_notes.extend(vocab_notes)
            all_cloze_notes.extend(cloze_notes)
            all_pronunciation_notes.extend(pron_notes)
    
    # Tạo các file Anki riêng biệt
    print(f"\n📤 Tạo các file Anki...")
    
    # File 1: Vocabulary (học từ mới)
    vocab_file = save_anki_file(
        all_vocabulary_notes, 
        f'{lesson_name}_vocabulary', 
        'Vocabulary'
    )
    
    # File 2: Cloze/Fill-in-blank (luyện ngữ cảnh)
    cloze_file = save_anki_file(
        all_cloze_notes,
        f'{lesson_name}_cloze',
        'Cloze/Fill-in-blank'
    )
    
    # File 3: Pronunciation (luyện phát âm)
    pron_file = save_anki_file(
        all_pronunciation_notes,
        f'{lesson_name}_pronunciation', 
        'Pronunciation'
    )
    
    # File 4: Exercises (bài tập từ sách)
    if all_exercise_notes:
        exercise_file = save_anki_file(
            all_exercise_notes,
            f'{lesson_name}_exercises',
            'Exercises'
        )
    
    # Tạo hướng dẫn best practices
    create_anki_best_practices_guide(lesson_name)
    
    # Tạo summary report
    create_summary_report(lesson_name, all_vocabulary_notes, all_cloze_notes, all_pronunciation_notes, all_exercise_notes)
    
    # In kết quả
    print(f"\n" + "=" * 60)
    print(f"🎉 HOÀN THÀNH ANKI GENERATOR V3!")
    print(f"📊 THỐNG KÊ:")
    print(f"   - Thẻ từ vựng: {len(all_vocabulary_notes)}")
    print(f"   - Thẻ cloze/điền từ: {len(all_cloze_notes)}")
    print(f"   - Thẻ phát âm: {len(all_pronunciation_notes)}")
    print(f"   - Thẻ bài tập: {len(all_exercise_notes)}")
    print(f"   - Tổng cộng: {len(all_vocabulary_notes) + len(all_cloze_notes) + len(all_pronunciation_notes) + len(all_exercise_notes)} thẻ")
    
    print(f"\n📂 FILES ĐÃ TẠO:")
    print(f"   - 📚 Vocabulary: Import vào deck '{lesson_name.title()} - Vocabulary'")
    print(f"   - 🧩 Cloze: Import vào deck '{lesson_name.title()} - Cloze'")
    print(f"   - 🔊 Pronunciation: Import vào deck '{lesson_name.title()} - Pronunciation'")
    if all_exercise_notes:
        print(f"   - 📝 Exercises: Import vào deck '{lesson_name.title()} - Exercises'")
    print(f"   - 🎓 Best Practices Guide: {lesson_name}_anki_best_practices.txt")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"1. Copy media files từ {MEDIA_FOLDER}/ vào Anki collection.media/")
    print(f"2. Import từng file .txt vào deck riêng biệt")
    print(f"3. Đọc Best Practices Guide để học hiệu quả")
    print(f"4. Bắt đầu với Vocabulary deck trước!")
    
    print(f"\n🚀 Chúc bạn học tốt với hệ thống Anki chuyên nghiệp!")

def create_summary_report(lesson_name, vocab_notes, cloze_notes, pron_notes, exercise_notes):
    """Tạo báo cáo tổng kết"""
    total_notes = len(vocab_notes) + len(cloze_notes) + len(pron_notes) + len(exercise_notes)
    
    report = f"""
# 📊 ANKI GENERATION REPORT - {lesson_name.upper()}

## 📈 Statistics:
- **Vocabulary cards**: {len(vocab_notes)}
- **Cloze cards**: {len(cloze_notes)} 
- **Pronunciation cards**: {len(pron_notes)}
- **Exercise cards**: {len(exercise_notes)}
- **Total cards**: {total_notes}

## 📁 Files created:
1. `{lesson_name}_vocabulary_[timestamp].txt` - Main vocabulary learning
2. `{lesson_name}_cloze_[timestamp].txt` - Context practice  
3. `{lesson_name}_pronunciation_[timestamp].txt` - Audio practice
4. `{lesson_name}_exercises_[timestamp].txt` - Book exercises
5. `{lesson_name}_anki_best_practices.txt` - Learning guide

## 🎯 Import Instructions:
1. **Create separate decks** for each card type
2. **Copy media files** to Anki collection.media folder
3. **Import each .txt file** to its corresponding deck
4. **Enable HTML** when importing
5. **Start with vocabulary deck** first

## ⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    report_path = os.path.join(OUTPUT_FOLDER, f'{lesson_name}_generation_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✅ Tạo báo cáo: {report_path}")

if __name__ == "__main__":
    main()