#!/usr/bin/env python3
"""
🎯 FEATURE 1: CSV → ANKI CARDS
Automated Anki card creation from CSV files using AnkiConnect with bulk operations

This script:
1. Detects new CSV files in input/
2. Downloads media (images, audio)
3. Creates decks automatically
4. Imports cards in bulk via AnkiConnect for performance
5. Falls back to individual adds on bulk errors (e.g., cloze failures)
6. Tracks processed files

Author: Assistant
Version: 3.1 (Bulk add + cloze-fallback fix)
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import argparse
from typing import List, Dict, Optional

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feature1_csv_to_anki.core.anki_connect import AnkiConnectClient
from feature1_csv_to_anki.core.card_generator import CardGenerator
from feature1_csv_to_anki.core.media_downloader import MediaDownloader
from feature1_csv_to_anki.core.deck_manager import DeckManager
from feature1_csv_to_anki.core.profile_manager import ProfileManager
from shared.config import Config
from shared.utils import setup_logging, colored_print


class CSVToAnkiProcessor:
    """Main processor for CSV to Anki conversion with bulk operations"""

    def __init__(self, profile: Optional[str] = None):
        self.config = Config()
        self.profile = profile
        self.anki_client = AnkiConnectClient()
        self.card_generator = CardGenerator()
        self.media_downloader = MediaDownloader()
        self.deck_manager = DeckManager(self.anki_client)
        self.profile_manager = ProfileManager(self.anki_client)

        # Paths
        self.input_dir = Path("input")
        self.logs_dir = Path("logs")
        self.processed_file = self.input_dir / ".processed"
        self.history_file = self.logs_dir / "import_history.json"

        # Create directories
        self.input_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # Load history
        self.import_history = self._load_history()

    def _load_history(self) -> Dict:
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"imports": []}

    def _save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.import_history, f, indent=2, ensure_ascii=False)

    def _get_processed_files(self) -> List[str]:
        if self.processed_file.exists():
            return [line.strip() for line in self.processed_file.read_text().splitlines()]
        return []

    def _mark_as_processed(self, filename: str):
        with open(self.processed_file, 'a') as f:
            f.write(f"{filename}\n")

    def detect_new_files(self) -> List[Path]:
        processed = set(self._get_processed_files())
        input_files = list(self.input_dir.glob("*.[cx]sv")) \
                      + list(self.input_dir.glob("*.xlsx")) \
                      + list(self.input_dir.glob("*.xls"))
        return [f for f in input_files if f.name not in processed and 'template' not in f.name.lower()]

    def check_anki_connection(self) -> bool:
        try:
            version = self.anki_client.invoke('version')
            colored_print(f"✅ AnkiConnect version: {version}", "green")
            return True
        except Exception as e:
            colored_print(f"❌ Cannot connect to Anki: {e}", "red")
            colored_print("Please ensure:", "yellow")
            colored_print("1. Anki is running", "yellow")
            colored_print("2. AnkiConnect add-on is installed (code: 2055492159)", "yellow")
            colored_print("3. AnkiConnect is configured on port 8765", "yellow")
            return False

    def select_profile(self) -> Optional[str]:
        if self.profile:
            return self.profile
        profiles = self.profile_manager.get_profiles()
        if not profiles:
            colored_print("No profiles found!", "red")
            return None
        colored_print("\n📝 Available Anki Profiles:", "cyan")
        for i, profile in enumerate(profiles, 1):
            print(f"{i}. {profile}")
        print("0. Import to all profiles")
        try:
            choice = int(input("\n👉 Select profile (0 for all): "))
            return None if choice == 0 else profiles[choice-1]
        except Exception:
            colored_print("Invalid input!", "red")
            return None

    def _bulk_add(self, notes: List[Dict], stat_key: str, result: Dict):
        """Bulk add notes via AnkiConnect; fallback to individual adds on failure"""
        if not notes:
            return
        try:
            payload = {'notes': notes}
            logging.debug("Cloze bulk payload: %s", json.dumps(payload, ensure_ascii=False))
            sample = notes[0]
            print("Sample note:", sample)
            added_ids = self.anki_client.add_notes(notes)
            result['stats'][stat_key] += len(added_ids)
            colored_print(f"✅ Bulk added {len(added_ids)} cards ({stat_key})", "green")
        except Exception as e:
            msg = str(e).lower()
            if 'duplicate' in msg:
                logging.warning(f"Skipped duplicate exercise card")
            else:
                logging.error(f"Failed to add cloze note: {e}")
                result['stats']['errors'].append(str(e))
                return
                logging.error(f"Bulk add error for {stat_key}: {e}. Falling back to individual adds.")
                for note in notes:
                    try:
                        self.anki_client.add_note(
                            deck_name=note['deckName'],
                            model_name=note['modelName'],
                            fields=note['fields'],
                            tags=note['tags']
                        )
                        result['stats'][stat_key] += 1
                    except Exception as ie:
                        logging.error(f"Failed to add card {note['fields']}: {ie}")
                        result['stats']['errors'].append(f"{stat_key}: {note['fields']}: {ie}")

    def process_csv_file(self, csv_file: Path, profile: Optional[str] = None) -> Dict:
        colored_print(f"\n📄 Processing: {csv_file.name}", "blue")
        result = {
            "file": csv_file.name,
            "timestamp": datetime.now().isoformat(),
            "profile": profile or "all",
            "stats": {**{k:0 for k in ['vocabulary_cards','cloze_cards','pronunciation_cards','exercise_cards','media_downloaded']}, 'errors': []}
        }
        try:
            if profile:
                self.profile_manager.switch_profile(profile)
            parsed = self.card_generator.parse_file(csv_file)
            vocab_data = parsed.get('vocabulary', [])
            ex_data = parsed.get('exercises', [])
            # media download
            for wd in vocab_data:
                try:
                    img = self.media_downloader.download_image(wd['word'], wd.get('part_of_speech'), wd.get('vietnamese'))
                    if img: wd['image'], result['stats']['media_downloaded'] = img, result['stats']['media_downloaded']+1
                    aud = self.media_downloader.download_audio(wd['word'], wd.get('pronunciation'))
                    if aud: wd['audio'], result['stats']['media_downloaded'] = aud, result['stats']['media_downloaded']+1
                except Exception as e:
                    logging.error(f"Media error {wd['word']}: {e}")
                    result['stats']['errors'].append(f"Media: {wd['word']}")
            # deck creation
            lesson = csv_file.stem.replace('_',' ').title()
            base = f"Vocabulary::{lesson}"
            decks = {
                'vocabulary': f"{base}::1 Vocabulary",
                'cloze':      f"{base}::2 Cloze",
                'pronunciation': f"{base}::3 Pronunciation",
                'exercise':  f"{base}::4 Exercises"
            }
            for d in decks.values():
                self.deck_manager.create_deck(d)
            # prepare bulk notes
            notes_vocab = [
                {'deckName': decks['vocabulary'], 'modelName': 'Basic', 'fields': c['fields'], 'tags': c['tags'],
                    'options': {
                        'allowDuplicate': True
                    }}
                for c in self.card_generator.create_vocabulary_cards(vocab_data)
            ]
            notes_cloze = [
                {'deckName': decks['cloze'], 'modelName': 'Cloze', 'fields': c['fields'], 'tags': c['tags'],
                    'options': {
                        'allowDuplicate': True
                    }}
                for c in self.card_generator.create_cloze_cards(vocab_data)
            ]
            notes_pron = [
                {'deckName': decks['pronunciation'], 'modelName': 'Basic', 'fields': c['fields'], 'tags': c['tags'],
                    'options': {
                        'allowDuplicate': True
                    }}
                for c in self.card_generator.create_pronunciation_cards(vocab_data)
            ]
            notes_ex  = [
                {'deckName': decks['exercise'], 'modelName': 'Basic', 'fields': c['fields'], 'tags': c['tags'],
                    'options': {
                        'allowDuplicate': True
                    }}
                for c in self.card_generator.create_exercise_cards(ex_data)
            ]
            # bulk add all types
            self._bulk_add(notes_vocab, 'vocabulary_cards', result)
            self._bulk_add(notes_cloze,  'cloze_cards',      result)
            self._bulk_add(notes_pron,   'pronunciation_cards', result)
            self._bulk_add(notes_ex,     'exercise_cards',   result)
            # mark, history, sync
            self._mark_as_processed(csv_file.name)
            self.import_history['imports'].append(result)
            self._save_history()
            self.anki_client.sync()
            colored_print(f"✅ Successfully processed {csv_file.name}", "green")
        except Exception as e:
            colored_print(f"❌ Error processing {csv_file.name}: {e}", "red")
            result['stats']['errors'].append(str(e))
        return result

    def show_summary(self, results: List[Dict]):
        """Show processing summary"""
        colored_print("\n" + "=" * 60, "blue")
        colored_print("📊 IMPORT SUMMARY", "blue")
        colored_print("=" * 60, "blue")

        total_vocab = sum(r['stats']['vocabulary_cards'] for r in results)
        total_cloze = sum(r['stats']['cloze_cards'] for r in results)
        total_pron = sum(r['stats']['pronunciation_cards'] for r in results)
        total_exercise = sum(r['stats']['exercise_cards'] for r in results)
        total_media = sum(r['stats']['media_downloaded'] for r in results)

        print(f"\n📁 Files processed: {len(results)}")
        print(f"🃏 Total cards created:")
        print(f"   - Vocabulary: {total_vocab}")
        print(f"   - Cloze: {total_cloze}")
        print(f"   - Pronunciation: {total_pron}")
        print(f"   - Exercises: {total_exercise}")
        print(f"   - Total: {total_vocab + total_cloze + total_pron + total_exercise}")
        print(f"🖼️ Media downloaded: {total_media}")

        # Show errors if any
        all_errors = []
        for r in results:
            if r['stats']['errors']:
                all_errors.extend(r['stats']['errors'])

        if all_errors:
            colored_print(f"\n⚠️ Errors encountered: {len(all_errors)}", "yellow")
            for error in all_errors[:5]:  # Show first 5 errors
                print(f"   - {error}")
            if len(all_errors) > 5:
                print(f"   ... and {len(all_errors) - 5} more")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="CSV to Anki - Automated card creation from CSV files"
    )
    parser.add_argument(
        '--profile', '-p',
        help='Anki profile to import to (default: prompt user)'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Process all CSV files, including previously processed ones'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    # Header
    colored_print("\n🚀 CSV TO ANKI - AUTOMATED IMPORT SYSTEM", "cyan")
    colored_print("=" * 50, "cyan")

    # Initialize processor
    processor = CSVToAnkiProcessor(profile=args.profile)

    # Check Anki connection
    if not processor.check_anki_connection():
        return 1

    # Detect files to process
    if args.all:
        csv_files = list(processor.input_dir.glob("*.csv"))
        csv_files = [f for f in csv_files if 'template' not in f.name.lower()]
    else:
        csv_files = processor.detect_new_files()

    if not csv_files:
        colored_print("\n📭 No new CSV files found in input/", "yellow")
        colored_print("Place your CSV files in the input/ folder and run again.", "yellow")
        return 0

    # Show files to process
    colored_print(f"\n📁 Found {len(csv_files)} file(s) to process:", "blue")
    for csv_file in csv_files:
        print(f"   - {csv_file.name}")

    # Select profile
    profile = processor.select_profile()

    # Process each file
    results = []
    for csv_file in csv_files:
        result = processor.process_csv_file(csv_file, profile)
        results.append(result)
        time.sleep(1)  # Small delay between files

    # Show summary
    processor.show_summary(results)

    colored_print("\n✨ All done! Happy studying! 🎓", "green")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        colored_print("\n\n👋 Operation cancelled by user", "yellow")
        sys.exit(1)
    except Exception as e:
        colored_print(f"\n❌ Unexpected error: {e}", "red")
        logging.exception("Unexpected error")
        sys.exit(1)