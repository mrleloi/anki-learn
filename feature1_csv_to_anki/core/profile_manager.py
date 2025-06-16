#!/usr/bin/env python3
"""
Profile Manager
Manages Anki profiles for multi-profile support

Author: Assistant
Version: 3.0
"""

import logging
from typing import List, Optional, Dict


class ProfileManager:
    """Manage Anki profiles"""

    def __init__(self, anki_client):
        self.anki_client = anki_client
        self.logger = logging.getLogger(__name__)
        self._current_profile = None

    def get_profiles(self) -> List[str]:
        """
        Get list of available profiles

        Returns:
            List of profile names
        """
        try:
            profiles = self.anki_client.get_profiles()
            self.logger.info(f"Found {len(profiles)} profiles")
            return profiles
        except Exception as e:
            self.logger.error(f"Failed to get profiles: {e}")
            return []

    def get_current_profile(self) -> Optional[str]:
        """
        Get currently loaded profile

        Returns:
            Current profile name or None
        """
        return self._current_profile

    def switch_profile(self, profile_name: str) -> bool:
        """
        Switch to a different profile

        Args:
            profile_name: Name of profile to switch to

        Returns:
            True if successful
        """
        try:
            # Check if profile exists
            profiles = self.get_profiles()
            if profile_name not in profiles:
                self.logger.error(f"Profile '{profile_name}' not found")
                return False

            # Load profile
            result = self.anki_client.load_profile(profile_name)

            if result:
                self._current_profile = profile_name
                self.logger.info(f"Switched to profile: {profile_name}")
                return True
            else:
                self.logger.error(f"Failed to switch to profile: {profile_name}")
                return False

        except Exception as e:
            self.logger.error(f"Error switching profile: {e}")
            return False

    def create_profile(self, profile_name: str) -> bool:
        """
        Create a new profile (if supported by AnkiConnect)

        Args:
            profile_name: Name for the new profile

        Returns:
            True if successful
        """
        # Note: AnkiConnect may not support profile creation
        # This is a placeholder for potential future functionality
        self.logger.warning("Profile creation not implemented in AnkiConnect")
        return False

    def get_profile_statistics(self, profile_name: Optional[str] = None) -> Dict:
        """
        Get statistics for a profile

        Args:
            profile_name: Profile to get stats for (None for current)

        Returns:
            Dictionary with profile statistics
        """
        if profile_name and profile_name != self._current_profile:
            # Switch to profile temporarily
            original_profile = self._current_profile
            if not self.switch_profile(profile_name):
                return {}

        try:
            # Get collection stats
            stats_html = self.anki_client.get_collection_stats_html()

            # Get deck count
            decks = self.anki_client.deck_names()

            # Get total cards
            all_cards = self.anki_client.find_cards("")

            stats = {
                'profile': profile_name or self._current_profile,
                'total_decks': len(decks),
                'total_cards': len(all_cards),
                'vocabulary_decks': len([d for d in decks if d.startswith("Vocabulary::")])
            }

            return stats

        except Exception as e:
            self.logger.error(f"Failed to get profile statistics: {e}")
            return {}

        finally:
            # Switch back to original profile if needed
            if profile_name and profile_name != self._current_profile and 'original_profile' in locals():
                self.switch_profile(original_profile)

    def export_profile_data(self, profile_name: str, export_path: str) -> bool:
        """
        Export all data from a profile

        Args:
            profile_name: Profile to export
            export_path: Path to save export

        Returns:
            True if successful
        """
        # Switch to profile
        original_profile = self._current_profile
        if not self.switch_profile(profile_name):
            return False

        try:
            # Export entire collection
            self.anki_client.export_package("*", export_path, include_scheduling=True)
            self.logger.info(f"Exported profile {profile_name} to {export_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export profile: {e}")
            return False

        finally:
            # Switch back
            if original_profile:
                self.switch_profile(original_profile)

    def sync_profile(self, profile_name: Optional[str] = None) -> bool:
        """
        Sync a profile with AnkiWeb

        Args:
            profile_name: Profile to sync (None for current)

        Returns:
            True if successful
        """
        if profile_name and profile_name != self._current_profile:
            if not self.switch_profile(profile_name):
                return False

        try:
            self.anki_client.sync()
            self.logger.info(f"Synced profile: {profile_name or self._current_profile}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to sync profile: {e}")
            return False

    def find_profile_with_deck(self, deck_name: str) -> Optional[str]:
        """
        Find which profile contains a specific deck

        Args:
            deck_name: Name of deck to search for

        Returns:
            Profile name or None
        """
        profiles = self.get_profiles()
        original_profile = self._current_profile

        for profile in profiles:
            if self.switch_profile(profile):
                try:
                    decks = self.anki_client.deck_names()
                    if deck_name in decks:
                        return profile
                except:
                    pass

        # Switch back
        if original_profile:
            self.switch_profile(original_profile)

        return None

    def import_to_all_profiles(self, import_function, *args, **kwargs) -> Dict[str, bool]:
        """
        Execute an import function on all profiles

        Args:
            import_function: Function to execute on each profile
            *args, **kwargs: Arguments for the function

        Returns:
            Dictionary mapping profile name to success status
        """
        profiles = self.get_profiles()
        results = {}
        original_profile = self._current_profile

        for profile in profiles:
            self.logger.info(f"Processing profile: {profile}")

            if self.switch_profile(profile):
                try:
                    # Execute the import function
                    success = import_function(*args, **kwargs)
                    results[profile] = success

                    # Sync after import
                    if success:
                        self.sync_profile()

                except Exception as e:
                    self.logger.error(f"Error in profile {profile}: {e}")
                    results[profile] = False
            else:
                results[profile] = False

        # Switch back to original profile
        if original_profile:
            self.switch_profile(original_profile)

        return results