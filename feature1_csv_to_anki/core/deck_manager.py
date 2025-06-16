#!/usr/bin/env python3
"""
Deck Manager
Manages Anki deck creation and organization

Author: Assistant
Version: 3.0
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime


class DeckManager:
    """Manage Anki decks and their configurations"""

    def __init__(self, anki_client):
        self.anki_client = anki_client
        self.logger = logging.getLogger(__name__)

    def create_deck(self, deck_name: str) -> int:
        """
        Create a deck if it doesn't exist

        Args:
            deck_name: Name of the deck (can use :: for subdeck)

        Returns:
            Deck ID
        """
        try:
            deck_id = self.anki_client.create_deck(deck_name)
            self.logger.info(f"Created/verified deck: {deck_name} (ID: {deck_id})")
            return deck_id
        except Exception as e:
            self.logger.error(f"Failed to create deck {deck_name}: {e}")
            raise

    def create_deck_structure(self, lesson_name: str) -> Dict[str, int]:
        """
        Create standard deck structure for a lesson

        Args:
            lesson_name: Name of the lesson

        Returns:
            Dictionary mapping deck type to deck ID
        """
        base_deck = f"Vocabulary::{lesson_name}"

        deck_structure = {
            'base': base_deck,
            'vocabulary': f"{base_deck}::1 Vocabulary",
            'cloze': f"{base_deck}::2 Cloze",
            'pronunciation': f"{base_deck}::3 Pronunciation",
            'exercise': f"{base_deck}::4 Exercises"
        }

        deck_ids = {}

        # Create all decks
        for deck_type, deck_name in deck_structure.items():
            try:
                deck_id = self.create_deck(deck_name)
                deck_ids[deck_type] = deck_id
            except Exception as e:
                self.logger.error(f"Failed to create {deck_type} deck: {e}")

        return deck_ids

    def setup_deck_options(self, deck_name: str, deck_type: str):
        """
        Configure deck options based on deck type

        Args:
            deck_name: Name of the deck
            deck_type: Type of deck (vocabulary, cloze, etc.)
        """
        try:
            # Get current config
            config = self.anki_client.get_deck_config(deck_name)

            # Modify based on deck type
            if deck_type == 'vocabulary':
                config['new']['perDay'] = 20
                config['new']['delays'] = [1, 10]
                config['new']['initialFactor'] = 2500
                config['rev']['perDay'] = 200
                config['rev']['ease4'] = 1.3
                config['rev']['ivlFct'] = 1.0

            elif deck_type == 'cloze':
                config['new']['perDay'] = 15
                config['new']['delays'] = [10, 25]
                config['new']['initialFactor'] = 2000
                config['rev']['perDay'] = 150
                config['rev']['ease4'] = 1.3
                config['rev']['ivlFct'] = 0.9

            elif deck_type == 'pronunciation':
                config['new']['perDay'] = 10
                config['new']['delays'] = [1, 5]
                config['new']['initialFactor'] = 2500
                config['rev']['perDay'] = 100

            elif deck_type == 'exercise':
                config['new']['perDay'] = 10
                config['new']['delays'] = [10, 30]
                config['new']['initialFactor'] = 1500
                config['rev']['perDay'] = 100
                config['rev']['ivlFct'] = 0.8

            # Save config
            self.anki_client.save_deck_config(config)
            self.logger.info(f"Configured deck options for {deck_name} ({deck_type})")

        except Exception as e:
            self.logger.warning(f"Failed to configure deck {deck_name}: {e}")

    def get_deck_statistics(self, deck_name: str) -> Dict:
        """
        Get statistics for a deck

        Args:
            deck_name: Name of the deck

        Returns:
            Dictionary with deck statistics
        """
        try:
            stats = self.anki_client.get_deck_stats(deck_name)
            return stats
        except Exception as e:
            self.logger.error(f"Failed to get stats for {deck_name}: {e}")
            return {}

    def list_vocabulary_decks(self) -> List[str]:
        """
        List all vocabulary-related decks

        Returns:
            List of deck names
        """
        try:
            all_decks = self.anki_client.deck_names()
            vocab_decks = [d for d in all_decks if d.startswith("Vocabulary::")]
            return sorted(vocab_decks)
        except Exception as e:
            self.logger.error(f"Failed to list decks: {e}")
            return []

    def get_deck_tree(self) -> Dict:
        """
        Get hierarchical structure of vocabulary decks

        Returns:
            Nested dictionary representing deck hierarchy
        """
        vocab_decks = self.list_vocabulary_decks()
        tree = {}

        for deck in vocab_decks:
            parts = deck.split("::")
            current = tree

            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]

        return tree

    def backup_deck(self, deck_name: str, backup_dir: str = "backups") -> bool:
        """
        Backup a deck to file

        Args:
            deck_name: Name of deck to backup
            backup_dir: Directory to save backup

        Returns:
            True if successful
        """
        import os
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = deck_name.replace("::", "_").replace(" ", "_")
        backup_path = os.path.join(backup_dir, f"{safe_name}_{timestamp}.apkg")

        try:
            self.anki_client.export_package(deck_name, backup_path, include_scheduling=True)
            self.logger.info(f"Backed up {deck_name} to {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to backup {deck_name}: {e}")
            return False

    def merge_decks(self, source_deck: str, target_deck: str) -> bool:
        """
        Merge cards from source deck into target deck

        Args:
            source_deck: Deck to move cards from
            target_deck: Deck to move cards to

        Returns:
            True if successful
        """
        try:
            # Find all cards in source deck
            query = f'deck:"{source_deck}"'
            card_ids = self.anki_client.find_cards(query)

            if not card_ids:
                self.logger.info(f"No cards found in {source_deck}")
                return True

            # Get note IDs
            cards_info = self.anki_client.cards_info(card_ids)
            note_ids = list(set(card['note'] for card in cards_info))

            # Move notes to target deck
            for note_id in note_ids:
                # Get note info
                note_info = self.anki_client.notes_info([note_id])[0]

                # Update deck
                fields = {field: value['value'] for field, value in note_info['fields'].items()}
                self.anki_client.update_note_fields(note_id, {'Deck': target_deck})

            self.logger.info(f"Moved {len(note_ids)} notes from {source_deck} to {target_deck}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to merge decks: {e}")
            return False

    def delete_empty_decks(self) -> int:
        """
        Delete all empty decks

        Returns:
            Number of decks deleted
        """
        deleted = 0

        try:
            vocab_decks = self.list_vocabulary_decks()

            for deck in vocab_decks:
                stats = self.get_deck_statistics(deck)

                if stats.get('total_cards', 0) == 0:
                    try:
                        self.anki_client.delete_decks([deck], cards_too=False)
                        self.logger.info(f"Deleted empty deck: {deck}")
                        deleted += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to delete {deck}: {e}")

            return deleted

        except Exception as e:
            self.logger.error(f"Failed to delete empty decks: {e}")
            return 0

    def reorganize_by_date(self) -> bool:
        """
        Reorganize decks by creation date

        Returns:
            True if successful
        """
        try:
            # Get all vocabulary lessons
            vocab_decks = self.list_vocabulary_decks()
            lessons = {}

            # Group by lesson
            for deck in vocab_decks:
                if "::" in deck:
                    parts = deck.split("::")
                    if len(parts) >= 2:
                        lesson = parts[1]
                        if lesson not in lessons:
                            lessons[lesson] = []
                        lessons[lesson].append(deck)

            # Create date-based structure
            today = datetime.now()
            year_month = today.strftime("%Y-%m")

            for lesson, decks in lessons.items():
                # Create new structure
                new_base = f"Vocabulary::{year_month}::{lesson}"

                # Move each subdeck
                for old_deck in decks:
                    if "::" in old_deck:
                        subdeck = old_deck.split("::")[-1]
                        new_deck = f"{new_base}::{subdeck}"

                        # Create new deck
                        self.create_deck(new_deck)

                        # Move cards
                        self.merge_decks(old_deck, new_deck)

            # Clean up empty decks
            self.delete_empty_decks()

            self.logger.info("Reorganized decks by date")
            return True

        except Exception as e:
            self.logger.error(f"Failed to reorganize decks: {e}")
            return False