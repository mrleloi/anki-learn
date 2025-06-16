# 📚 Feature 1: CSV to Anki Cards

Automated Anki card creation from CSV files using AnkiConnect.

## 🎯 Overview

This feature automatically:
- Detects new CSV files in the `input/` folder
- Downloads relevant images and audio for each word
- Creates 4 types of Anki cards (Vocabulary, Cloze, Pronunciation, Exercise)
- Organizes cards into a structured deck hierarchy
- Tracks processed files to avoid duplicates
- Supports multiple Anki profiles

## 🚀 Quick Start

### 1. Prerequisites

- **Anki Desktop** must be running
- **AnkiConnect** add-on installed (Tools → Add-ons → Get Add-ons → Code: `2055492159`)
- Python 3.7+ with required packages: `pip install -r requirements.txt`

### 2. Prepare CSV Files

Use the provided templates or ask ChatGPT/Claude to create CSV files:

```
Word,Pronunciation,Vietnamese,Part_of_Speech,Example_Sentence,Fill_in_Blank_Question,Fill_in_Blank_Answer
friendly,/ˈfrendli/,thân thiện,adj,She is very friendly to everyone.,She is very _______ to everyone.,friendly
```

### 3. Run the Script

```bash
cd feature1_csv_to_anki
python run.py
```

Options:
- `--profile PROFILE_NAME`: Import to specific profile
- `--all`: Process all CSV files (including previously processed)
- `--verbose`: Show detailed logging

## 📋 CSV Format

### Required Columns:
- **Word**: The English word
- **Vietnamese**: Vietnamese translation
- **Part_of_Speech**: adj, noun, verb, adv

### Optional Columns:
- **Pronunciation**: IPA pronunciation
- **Example_Sentence**: Example usage
- **Fill_in_Blank_Question**: Question with `_______` for the answer
- **Fill_in_Blank_Answer**: Answer for the blank (defaults to Word)

## 🎴 Generated Deck Structure

```
Vocabulary::
└── [Lesson Name]::
    ├── 1 Vocabulary     (Word → Meaning cards)
    ├── 2 Cloze         (Fill-in-the-blank cards)
    ├── 3 Pronunciation (Audio practice cards)
    └── 4 Exercises     (Additional exercises)
```

## 🤖 AI Prompt Templates

### ChatGPT Prompt:
```
Create a CSV file for these vocabulary words with columns:
Word, Pronunciation, Vietnamese, Part_of_Speech, Example_Sentence, Fill_in_Blank_Question, Fill_in_Blank_Answer

Words: [your word list]
```

### Claude Prompt:
```
Generate a vocabulary CSV file for Anki import. Include IPA pronunciation, Vietnamese meanings, and create fill-in-the-blank exercises. Format as CSV with proper escaping.

Words to include: [your word list]
```

## 📁 File Structure

```
feature1_csv_to_anki/
├── input/              # Place CSV files here
│   └── .processed      # Tracks processed files
├── logs/               # Processing logs
├── templates/          # CSV templates & AI prompts
└── core/               # Core modules
```

## ⚙️ Configuration

Edit `config.json` to customize:
- Deck naming patterns
- Cards per day limits
- API keys for image sources
- Learning steps and intervals

## 🔧 Troubleshooting

### AnkiConnect Error
- Ensure Anki is running
- Check AnkiConnect is installed and enabled
- Verify port 8765 is not blocked

### No Images Found
- Add API keys to environment variables:
  - `PIXABAY_API_KEY`
  - `PEXELS_API_KEY`
  - `UNSPLASH_API_KEY`

### Duplicate Cards
- Delete `.processed` file to reprocess
- Use `--all` flag to force reprocessing

## 📊 Import Statistics

After processing, you'll see:
- Total cards created per type
- Media files downloaded
- Any errors encountered
- Time taken

## 🎯 Best Practices

1. **Batch Processing**: Process 50-100 words at a time
2. **Consistent Formatting**: Use the same CSV structure
3. **Review Order**: Start with Vocabulary deck, then Cloze
4. **Daily Limits**: Adjust new cards/day in Anki settings
5. **Regular Backups**: Script auto-backs up before major operations

## 🆘 Support

- Check logs in `logs/` folder for detailed errors
- Ensure all dependencies are installed
- Verify CSV encoding is UTF-8
- Test with a small CSV file first