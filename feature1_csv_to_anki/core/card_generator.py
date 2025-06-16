#!/usr/bin/env python3
"""
Card Generator - Fixed CSS in f-string issue
Generates different types of Anki cards from CSV data

Author: Assistant
Version: 3.3 (Fixed CSS syntax error)
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any
from html import escape


class CardGenerator:
    """Generate Anki cards from vocabulary data"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def parse_file(self, file_path: Path) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse CSV or Excel file and extract vocabulary and exercise data
        Returns a dict with 'vocabulary' and 'exercises'
        """
        result = {'vocabulary': [], 'exercises': []}
        file_ext = file_path.suffix.lower()
        try:
            if file_ext in ['.xlsx', '.xls']:
                excel = pd.ExcelFile(file_path)
                for sheet in excel.sheet_names:
                    df = pd.read_excel(excel, sheet_name=sheet)
                    if 'Word' in df.columns:
                        result['vocabulary'].extend(self._parse_vocabulary_df(df))
                    elif 'Question' in df.columns and 'Answer' in df.columns:
                        result['exercises'].extend(self._parse_exercise_df(df))
            else:
                df = pd.read_csv(file_path, encoding='utf-8')
                if 'Word' in df.columns:
                    result['vocabulary'] = self._parse_vocabulary_df(df)
                elif 'Question' in df.columns and 'Answer' in df.columns:
                    result['exercises'] = self._parse_exercise_df(df)
            self.logger.info(f"Parsed {len(result['vocabulary'])} vocab and {len(result['exercises'])} exercises.")
            return result
        except Exception as e:
            self.logger.error(f"Error parsing {file_path.name}: {e}")
            raise

    def _parse_vocabulary_df(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        words = []
        for _, row in df.iterrows():
            if pd.isna(row.get('Word')):
                continue
            wd = {
                'word': str(row['Word']).strip(),
                'pronunciation': str(row.get('Pronunciation', '')).strip(),
                'vietnamese': str(row.get('Vietnamese', '')).strip(),
                'part_of_speech': str(row.get('Part_of_Speech', '')).strip(),
                'example_sentence': str(row.get('Example_Sentence', '')).strip(),
                'fill_in_blank_question': str(row.get('Fill_in_Blank_Question', '')).strip(),
                'fill_in_blank_answer': str(row.get('Fill_in_Blank_Answer', '')).strip(),
                'image': None,
                'audio': None
            }
            words.append(wd)
        return words

    def _parse_exercise_df(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        exs = []
        for _, row in df.iterrows():
            if pd.isna(row.get('Question')) or pd.isna(row.get('Answer')):
                continue
            ex = {
                'question': str(row['Question']).strip(),
                'answer': str(row['Answer']).strip(),
                'type': str(row.get('Type', 'general')).strip(),
                'difficulty': str(row.get('Difficulty', 'medium')).strip(),
                'context': str(row.get('Context', '')).strip()
            }
            exs.append(ex)
        return exs

    def create_vocabulary_cards(self, words_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cards = []
        for wd in words_data:
            front = self._create_vocabulary_front(wd)
            back = self._create_vocabulary_back(wd)
            cards.append({'fields': {'Front': front, 'Back': back}, 'tags': ['vocabulary', wd['part_of_speech']]})
        return cards

    def create_cloze_cards(self, words_data):
        cards = []
        for wd in words_data:
            q = wd['fill_in_blank_question']
            if not q:
                continue
            cloze = self._create_cloze_text(wd)
            extra = self._create_cloze_extra(wd)
            cards.append({
                'fields': {
                    'Text': cloze,
                    'Back Extra': extra
                },
                'tags': ['cloze', wd['part_of_speech']]
            })
        return cards

    def create_pronunciation_cards(self, words_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cards = []
        for wd in words_data:
            if not wd['pronunciation'] and not wd['audio']:
                continue
            front = self._create_pronunciation_front(wd)
            back = self._create_pronunciation_back(wd)
            cards.append({'fields': {'Front': front, 'Back': back}, 'tags': ['pronunciation', wd['part_of_speech']]})
        return cards

    def create_exercise_cards(self, exs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cards = []
        for ex in exs:
            front = self._create_exercise_front(ex)
            back = self._create_exercise_back(ex)
            cards.append({'fields': {'Front': front, 'Back': back}, 'tags': ['exercise', ex['type'], ex['difficulty']]})
        return cards

    # --- HTML/CSS builders ---

    def _create_vocabulary_front(self, wd: Dict[str, Any]) -> str:
        w = escape(wd['word'])
        p = escape(wd['pronunciation'])
        pos = escape(wd['part_of_speech'])
        img = wd.get('image', '')
        aud = wd.get('audio', '')
        
        # Extract just the filename from paths
        if img and ('\\' in img or '/' in img):
            img = img.split('\\')[-1].split('/')[-1]
        if aud and ('\\' in aud or '/' in aud):
            aud = aud.split('\\')[-1].split('/')[-1]
        
        # Tạo HTML content trước
        pronunciation_html = f'<div class="pronunciation">{p}</div>' if p else ''
        pos_html = f'<div class="part-of-speech">({pos})</div>' if pos else ''
        img_html = f'<img src="{img}" class="word-image">' if img else ''
        audio_html = f'[sound:{aud}]' if aud else ''
        
        # CSS được tách biệt, không trong f-string
        css_styles = """
<style>
.vocab-card {
  font-family: Arial, sans-serif;
  text-align: center;
  padding: 20px;
}
.word-main {
  font-size: 32px;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 10px;
}
.pronunciation {
  font-size: 18px;
  color: #7f8c8d;
  font-style: italic;
}
.part-of-speech {
  font-size: 14px;
  color: #95a5a6;
  margin: 5px 0;
}
.word-image {
  max-width: 250px;
  max-height: 200px;
  margin: 15px auto;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.prompt {
  margin-top: 20px;
  font-size: 16px;
  color: #3498db;
  font-style: italic;
}
</style>
"""
        
        html = f"""
<div class="vocab-card front">
  <div class="word-main">{w}</div>
  {pronunciation_html}
  {pos_html}
  {img_html}
  {audio_html}
  <div class="prompt">What does this word mean?</div>
</div>
{css_styles}"""
        
        return html

    def _create_vocabulary_back(self, wd: Dict[str, Any]) -> str:
        w = escape(wd['word'])
        vn = escape(wd['vietnamese'])
        ex = escape(wd['example_sentence'])
        
        example_html = f'<div class="example"><strong>Example:</strong> {ex}</div>' if ex else ''
        
        css_styles = """
<style>
.meaning {
  font-size: 28px;
  font-weight: bold;
  color: #27ae60;
  margin-bottom: 15px;
}
.word-repeat {
  font-size: 24px;
  color: #2c3e50;
  margin-bottom: 20px;
}
.example {
  font-size: 16px;
  color: #34495e;
  margin: 20px 0;
  padding: 15px;
  background: #ecf0f1;
  border-radius: 5px;
  text-align: left;
}
.memory-tips {
  margin-top: 25px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: left;
}
.tip-title {
  font-weight: bold;
  color: #e67e22;
  margin-bottom: 10px;
}
.memory-tips ul {
  margin: 5px 0;
  padding-left: 20px;
}
.memory-tips li {
  margin: 5px 0;
  color: #7f8c8d;
}
</style>
"""
        
        html = f"""
<div class="vocab-card back">
  <div class="meaning">{vn}</div>
  <div class="word-repeat">{w}</div>
  {example_html}
  <div class="memory-tips">
    <div class="tip-title">💡 Memory Tips:</div>
    <ul>
      <li>Use this word in a sentence today</li>
      <li>Think of someone who has this trait</li>
      <li>Create a mental image</li>
    </ul>
  </div>
</div>
{css_styles}"""
        return html

    def _create_cloze_text(self, wd: Dict[str, Any]) -> str:
        q = wd['fill_in_blank_question']
        ans = wd['fill_in_blank_answer'] or wd['word']
        vn = escape(wd['vietnamese'])
        
        # FIXED: Use double curly braces in the string, NOT in f-string
        # This creates {{c1::answer}} in the final output
        cloze = q.replace('_______', '{{c1::' + ans + '}}')
        
        css_styles = """
<style>
.cloze-card {
  font-family: Arial, sans-serif;
  padding: 20px;
  text-align: center;
}
.question {
  font-size: 20px;
  line-height: 1.6;
  color: #2c3e50;
  margin-bottom: 20px;
}
.hint {
  font-size: 16px;
  color: #7f8c8d;
  font-style: italic;
  margin-top: 15px;
  padding: 10px;
  background: #ecf0f1;
  border-radius: 5px;
  text-align: left;
}
</style>
"""
        
        html = f"""
<div class="cloze-card">
  <div class="question">{cloze}</div>
  <div class="hint">Vietnamese: {vn}</div>
</div>
{css_styles}"""
        return html

    def _create_cloze_extra(self, wd: Dict[str, Any]) -> str:
        w = escape(wd['word'])
        p = escape(wd['pronunciation'])
        info = f"<strong>Word:</strong> {w}" + (f"<br><strong>Pronunciation:</strong> {p}" if p else '')
        return f'<div class="extra-info">{info}</div>'

    def _create_pronunciation_front(self, wd: Dict[str, Any]) -> str:
        aud = wd.get('audio', '')
        
        # Extract just the filename from path
        if aud and ('\\' in aud or '/' in aud):
            aud = aud.split('\\')[-1].split('/')[-1]
        
        audio_html = f'[sound:{aud}]' if aud else ''
        
        css_styles = """
<style>
.pronunciation-card {
  font-family: Arial, sans-serif;
  padding: 20px;
  text-align: center;
}
.instruction {
  font-size: 20px;
  color: #3498db;
  margin-bottom: 20px;
  font-weight: bold;
}
.task {
  margin-top: 30px;
  text-align: left;
  display: inline-block;
}
.task ol {
  font-size: 16px;
  color: #34495e;
}
.task li {
  margin: 10px 0;
}
</style>
"""
        
        html = f"""
<div class="pronunciation-card front">
  <div class="instruction">🎧 Listen and pronounce this word</div>
  {audio_html}
  <div class="task">
    <ol>
      <li>Listen to the audio</li>
      <li>Repeat 3 times</li>
      <li>Check your pronunciation</li>
    </ol>
  </div>
</div>
{css_styles}"""
        return html

    def _create_pronunciation_back(self, wd: Dict[str, Any]) -> str:
        w = escape(wd['word'])
        p = escape(wd['pronunciation'])
        vn = escape(wd['vietnamese'])
        
        css_styles = """
<style>
.word {
  font-size: 32px;
  font-weight: bold;
  color: #2c3e50;
  margin-bottom: 10px;
}
.pronunciation {
  font-size: 20px;
  color: #e74c3c;
  font-style: italic;
  margin-bottom: 10px;
}
.meaning {
  font-size: 18px;
  color: #27ae60;
  margin-bottom: 20px;
}
.tips {
  margin-top: 25px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: left;
  display: inline-block;
}
.tips ul {
  margin: 10px 0;
  padding-left: 20px;
}
</style>
"""
        
        html = f"""
<div class="pronunciation-card back">
  <div class="word">{w}</div>
  <div class="pronunciation">{p}</div>
  <div class="meaning">{vn}</div>
  <div class="tips">
    <strong>Pronunciation Tips:</strong>
    <ul>
      <li>Break it down: {p}</li>
      <li>Practice slowly first</li>
      <li>Record yourself</li>
    </ul>
  </div>
</div>
{css_styles}"""
        return html

    def _create_exercise_front(self, ex: Dict[str, Any]) -> str:
        q = escape(ex.get('question', ''))
        et = escape(ex.get('type', 'general'))
        diff = escape(ex.get('difficulty', 'medium'))
        
        if et == 'dialogue':
            q = q.replace('A:', '<strong>A:</strong>').replace('B:', '<br><strong>B:</strong>')
        
        css_styles = """
<style>
.exercise-card {
  font-family: Arial, sans-serif;
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}
.type {
  font-size: 14px;
  color: #3498db;
  font-weight: bold;
}
.difficulty {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: bold;
}
.difficulty.easy { background: #2ecc71; color: white; }
.difficulty.medium { background: #f39c12; color: white; }
.difficulty.hard { background: #e74c3c; color: white; }
.question {
  font-size: 18px;
  line-height: 1.6;
  color: #2c3e50;
  margin: 20px 0;
}
.prompt {
  margin-top: 30px;
  font-style: italic;
  color: #7f8c8d;
}
</style>
"""
        
        html = f"""
<div class="exercise-card front">
  <div class="header">
    <span class="type">{et.title()}</span>
    <span class="difficulty {diff}">{diff.upper()}</span>
  </div>
  <div class="question">{q}</div>
  <div class="prompt">Think of the answer...</div>
</div>
{css_styles}"""
        return html

    def _create_exercise_back(self, ex: Dict[str, Any]) -> str:
        ans = escape(ex.get('answer', ''))
        q = escape(ex.get('question', ''))
        ctx = escape(ex.get('context', ''))
        
        complete = q.replace('_______', f'<span class="answer">{ans}</span>')
        context_html = f'<div class="context">Context: {ctx}</div>' if ctx else ''
        
        css_styles = """
<style>
.answer-section {
  margin-bottom: 20px;
}
.label {
  font-size: 14px;
  color: #7f8c8d;
  margin-bottom: 5px;
}
.answer-text {
  font-size: 28px;
  font-weight: bold;
  color: #27ae60;
}
.complete {
  margin: 20px 0;
}
.complete-text {
  font-size: 18px;
  line-height: 1.6;
  color: #34495e;
}
.answer {
  color: #e74c3c;
  font-weight: bold;
}
.context {
  margin-top: 20px;
  font-size: 14px;
  color: #95a5a6;
  font-style: italic;
}
</style>
"""
        
        html = f"""
<div class="exercise-card back">
  <div class="answer-section">
    <div class="label">Answer:</div>
    <div class="answer-text">{ans}</div>
  </div>
  <div class="complete">
    <div class="label">Complete sentence:</div>
    <div class="complete-text">{complete}</div>
  </div>
  {context_html}
</div>
{css_styles}"""
        return html