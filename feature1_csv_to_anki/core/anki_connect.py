#!/usr/bin/env python3
"""
AnkiConnect Client
Handles all communication with Anki via AnkiConnect add-on

Author: Assistant
Version: 3.0
"""

import json
import urllib.request
import urllib.error
import time
from typing import Any, Dict, List, Optional, Union
import logging


class AnkiConnectError(Exception):
    """Custom exception for AnkiConnect errors"""
    pass


class AnkiConnectClient:
    """Client for interacting with AnkiConnect API"""

    def __init__(self, url: str = 'http://localhost:8765', version: int = 6):
        self.url = url
        self.version = version
        self.logger = logging.getLogger(__name__)

    def invoke(self, action: str, **params) -> Any:
        """
        Invoke an AnkiConnect action

        Args:
            action: The action to perform
            **params: Parameters for the action

        Returns:
            The result of the action

        Raises:
            AnkiConnectError: If the action fails
        """
        request_json = json.dumps({
            'action': action,
            'version': self.version,
            'params': params
        }).encode('utf-8')

        try:
            response = urllib.request.urlopen(
                urllib.request.Request(
                    self.url,
                    request_json,
                    {'Content-Type': 'application/json'}
                ),
                timeout=10
            )

            response_data = json.loads(response.read().decode('utf-8'))

            if response_data.get('error'):
                logging.error("AnkiConnect trả về lỗi chi tiết: %s", response_data)

            if len(response_data) != 2:
                raise AnkiConnectError('Response has unexpected number of fields')
            if 'error' not in response_data:
                raise AnkiConnectError('Response missing error field')
            if 'result' not in response_data:
                raise AnkiConnectError('Response missing result field')
            if response_data['error'] is not None:
                raise AnkiConnectError(response_data['error'])

            return response_data['result']

        except urllib.error.URLError as e:
            raise AnkiConnectError(f"Cannot connect to Anki: {e}")
        except json.JSONDecodeError as e:
            raise AnkiConnectError(f"Invalid JSON response: {e}")

    # === Profile Management ===

    def get_profiles(self) -> List[str]:
        """Get list of available profiles"""
        return self.invoke('getProfiles')

    def load_profile(self, name: str) -> bool:
        """Load a specific profile"""
        return self.invoke('loadProfile', name=name)

    # === Deck Management ===

    def deck_names(self) -> List[str]:
        """Get all deck names"""
        return self.invoke('deckNames')

    def deck_names_and_ids(self) -> Dict[str, int]:
        """Get deck names and their IDs"""
        return self.invoke('deckNamesAndIds')

    def create_deck(self, deck: str) -> int:
        """Create a new deck"""
        return self.invoke('createDeck', deck=deck)

    def delete_decks(self, decks: List[str], cards_too: bool = True):
        """Delete decks"""
        self.invoke('deleteDecks', decks=decks, cardsToo=cards_too)

    def get_deck_config(self, deck: str) -> Dict:
        """Get deck configuration"""
        return self.invoke('getDeckConfig', deck=deck)

    def save_deck_config(self, config: Dict) -> bool:
        """Save deck configuration"""
        return self.invoke('saveDeckConfig', config=config)

    def set_deck_config_id(self, decks: List[str], config_id: int) -> bool:
        """Set deck config ID"""
        return self.invoke('setDeckConfigId', decks=decks, configId=config_id)

    # === Model Management ===

    def model_names(self) -> List[str]:
        """Get all model names"""
        return self.invoke('modelNames')

    def model_names_and_ids(self) -> Dict[str, int]:
        """Get model names and their IDs"""
        return self.invoke('modelNamesAndIds')

    def model_field_names(self, model_name: str) -> List[str]:
        """Get field names for a model"""
        return self.invoke('modelFieldNames', modelName=model_name)

    def create_model(self, model_name: str, fields: List[str],
                     css: str = "", card_templates: List[Dict] = None) -> Dict:
        """Create a new model"""
        if card_templates is None:
            card_templates = [{
                'Name': 'Card 1',
                'Front': '{{' + fields[0] + '}}',
                'Back': '{{FrontSide}}<hr id="answer">{{' + fields[1] + '}}'
            }]

        return self.invoke(
            'createModel',
            modelName=model_name,
            inOrderFields=fields,
            css=css,
            cardTemplates=card_templates
        )

    # === Note Management ===

    def add_note(self, deck_name: str, model_name: str,
                 fields: Dict[str, str], tags: List[str] = None,
                 allow_duplicate: bool = False) -> int:
        """
        Add a new note

        Args:
            deck_name: Name of the deck
            model_name: Name of the model
            fields: Dictionary of field names to values
            tags: List of tags
            allow_duplicate: Whether to allow duplicate notes

        Returns:
            Note ID
        """
        if tags is None:
            tags = []

        note = {
            'deckName': deck_name,
            'modelName': model_name,
            'fields': fields,
            'tags': tags,
            'options': {
                'allowDuplicate': allow_duplicate
            }
        }

        return self.invoke('addNote', note=note)

    def add_notes(self, notes: List[Dict]) -> List[int]:
        """Add multiple notes"""
        return self.invoke('addNotes', notes=notes)

    def update_note_fields(self, note_id: int, fields: Dict[str, str]):
        """Update fields of an existing note"""
        note = {
            'id': note_id,
            'fields': fields
        }
        self.invoke('updateNoteFields', note=note)

    def delete_notes(self, notes: List[int]):
        """Delete notes by ID"""
        self.invoke('deleteNotes', notes=notes)

    def find_notes(self, query: str) -> List[int]:
        """Find notes matching a query"""
        return self.invoke('findNotes', query=query)

    def notes_info(self, notes: List[int]) -> List[Dict]:
        """Get detailed info for notes"""
        return self.invoke('notesInfo', notes=notes)

    # === Card Management ===

    def find_cards(self, query: str) -> List[int]:
        """Find cards matching a query"""
        return self.invoke('findCards', query=query)

    def cards_info(self, cards: List[int]) -> List[Dict]:
        """Get detailed info for cards"""
        return self.invoke('cardsInfo', cards=cards)

    def cards_mod_time(self, cards: List[int]) -> List[int]:
        """Get modification time for cards"""
        return self.invoke('cardsModTime', cards=cards)

    def set_ease_factor(self, cards: List[int], ease_factor: int):
        """Set ease factor for cards"""
        self.invoke('setEaseFactors', cards=cards, easeFactors=[ease_factor] * len(cards))

    def suspend_cards(self, cards: List[int]):
        """Suspend cards"""
        self.invoke('suspend', cards=cards)

    def unsuspend_cards(self, cards: List[int]):
        """Unsuspend cards"""
        self.invoke('unsuspend', cards=cards)

    def are_suspended(self, cards: List[int]) -> List[bool]:
        """Check if cards are suspended"""
        return self.invoke('areSuspended', cards=cards)

    # === Media Management ===

    def store_media_file(self, filename: str, data: bytes) -> str:
        """
        Store a media file in Anki

        Args:
            filename: Name of the file
            data: File data as bytes

        Returns:
            Filename of stored file
        """
        import base64
        data_b64 = base64.b64encode(data).decode('utf-8')
        return self.invoke('storeMediaFile', filename=filename, data=data_b64)

    def retrieve_media_file(self, filename: str) -> bytes:
        """Retrieve a media file from Anki"""
        import base64
        data_b64 = self.invoke('retrieveMediaFile', filename=filename)
        if data_b64:
            return base64.b64decode(data_b64)
        return b''

    def delete_media_file(self, filename: str):
        """Delete a media file"""
        self.invoke('deleteMediaFile', filename=filename)

    def get_media_files_names(self, pattern: str = "*") -> List[str]:
        """Get list of media files"""
        return self.invoke('getMediaFilesNames', pattern=pattern)

    # === Collection Management ===

    def sync(self):
        """Sync collection with AnkiWeb"""
        self.invoke('sync')

    def get_collection_stats_html(self) -> str:
        """Get collection statistics as HTML"""
        return self.invoke('getCollectionStatsHTML')

    def export_package(self, deck: str, path: str,
                       include_scheduling: bool = False):
        """Export deck as .apkg file"""
        self.invoke(
            'exportPackage',
            deck=deck,
            path=path,
            includeSched=include_scheduling
        )

    def import_package(self, path: str):
        """Import .apkg file"""
        self.invoke('importPackage', path=path)

    # === Miscellaneous ===

    def request_permission(self) -> str:
        """Request permission to use AnkiConnect"""
        return self.invoke('requestPermission')

    def version(self) -> int:
        """Get AnkiConnect version"""
        return self.invoke('version')

    def gui_browse(self, query: str) -> List[int]:
        """Open browser with search query"""
        return self.invoke('guiBrowse', query=query)

    def gui_add_cards(self, note: Dict = None):
        """Open add cards dialog"""
        params = {}
        if note:
            params['note'] = note
        return self.invoke('guiAddCards', **params)

    def gui_deck_browser(self):
        """Open deck browser"""
        self.invoke('guiDeckBrowser')

    def gui_deck_overview(self, name: str):
        """Open deck overview"""
        self.invoke('guiDeckOverview', name=name)

    # === Helper Methods ===

    def can_add_notes(self, notes: List[Dict]) -> List[bool]:
        """Check if notes can be added (no duplicates)"""
        return self.invoke('canAddNotes', notes=notes)

    def add_tags(self, notes: List[int], tags: str):
        """Add tags to notes"""
        self.invoke('addTags', notes=notes, tags=tags)

    def remove_tags(self, notes: List[int], tags: str):
        """Remove tags from notes"""
        self.invoke('removeTags', notes=notes, tags=tags)

    def get_tags(self) -> List[str]:
        """Get all tags in collection"""
        return self.invoke('getTags')

    def clear_unused_tags(self):
        """Clear unused tags"""
        self.invoke('clearUnusedTags')

    def replace_tags(self, notes: List[int], tag_to_replace: str,
                     replace_with_tag: str):
        """Replace tags in notes"""
        self.invoke(
            'replaceTags',
            notes=notes,
            tag_to_replace=tag_to_replace,
            replace_with_tag=replace_with_tag
        )

    def replace_tags_in_all_notes(self, tag_to_replace: str,
                                  replace_with_tag: str):
        """Replace tags in all notes"""
        self.invoke(
            'replaceTagsInAllNotes',
            tag_to_replace=tag_to_replace,
            replace_with_tag=replace_with_tag
        )

    def set_note_tags(self, note: int, tags: List[str]):
        """Set tags for a specific note"""
        self.invoke('setNoteTags', note=note, tags=tags)

    # === Batch Operations ===

    def multi(self, actions: List[Dict]) -> List[Any]:
        """Execute multiple actions in one request"""
        return self.invoke('multi', actions=actions)

    def create_deck_with_notes(self, deck_name: str, notes: List[Dict]) -> Dict:
        """
        Create a deck and add notes in one operation

        Args:
            deck_name: Name of the deck to create
            notes: List of notes to add

        Returns:
            Dictionary with deck_id and note_ids
        """
        # Create deck
        deck_id = self.create_deck(deck_name)

        # Add deck name to all notes
        for note in notes:
            note['deckName'] = deck_name

        # Add notes
        note_ids = self.add_notes(notes)

        return {
            'deck_id': deck_id,
            'deck_name': deck_name,
            'note_ids': note_ids,
            'notes_added': len([nid for nid in note_ids if nid])
        }

    def find_and_update_notes(self, query: str,
                              updates: Dict[str, str]) -> int:
        """
        Find notes and update their fields

        Args:
            query: Search query
            updates: Dictionary of field updates

        Returns:
            Number of notes updated
        """
        note_ids = self.find_notes(query)

        for note_id in note_ids:
            self.update_note_fields(note_id, updates)

        return len(note_ids)

    def backup_deck(self, deck_name: str, backup_path: str) -> bool:
        """
        Backup a deck to file

        Args:
            deck_name: Name of deck to backup
            backup_path: Path to save backup

        Returns:
            True if successful
        """
        try:
            self.export_package(deck_name, backup_path, include_scheduling=True)
            return True
        except Exception as e:
            self.logger.error(f"Failed to backup deck {deck_name}: {e}")
            return False

    def get_deck_stats(self, deck_name: str) -> Dict:
        """
        Get statistics for a deck

        Args:
            deck_name: Name of the deck

        Returns:
            Dictionary with deck statistics
        """
        # Find cards in deck
        query = f'deck:"{deck_name}"'
        card_ids = self.find_cards(query)

        if not card_ids:
            return {
                'deck_name': deck_name,
                'total_cards': 0,
                'new_cards': 0,
                'learning_cards': 0,
                'review_cards': 0,
                'suspended_cards': 0
            }

        # Get card info
        cards_info = self.cards_info(card_ids)

        # Calculate statistics
        stats = {
            'deck_name': deck_name,
            'total_cards': len(card_ids),
            'new_cards': 0,
            'learning_cards': 0,
            'review_cards': 0,
            'suspended_cards': 0
        }

        for card in cards_info:
            if card['queue'] == 0:
                stats['new_cards'] += 1
            elif card['queue'] == 1 or card['queue'] == 3:
                stats['learning_cards'] += 1
            elif card['queue'] == 2:
                stats['review_cards'] += 1
            elif card['queue'] == -1:
                stats['suspended_cards'] += 1

        return stats

    def check_media_exists(self, filename: str) -> bool:
        """Check if a media file exists in collection"""
        try:
            media_files = self.get_media_files_names(filename)
            return filename in media_files
        except:
            return False

    def store_media_from_path(self, file_path: str) -> Optional[str]:
        """
        Store a media file from local path

        Args:
            file_path: Path to the file

        Returns:
            Filename in Anki media folder or None
        """
        try:
            import os
            filename = os.path.basename(file_path)

            # Check if already exists
            if self.check_media_exists(filename):
                self.logger.info(f"Media file {filename} already exists")
                return filename

            # Read file
            with open(file_path, 'rb') as f:
                data = f.read()

            # Store in Anki
            stored_filename = self.store_media_file(filename, data)
            self.logger.info(f"Stored media file: {stored_filename}")

            return stored_filename

        except Exception as e:
            self.logger.error(f"Failed to store media file {file_path}: {e}")
            return None