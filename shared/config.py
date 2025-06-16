#!/usr/bin/env python3
"""
Shared Configuration
Global configuration for the Anki Vocabulary System

Author: Assistant
Version: 3.0
"""

import os
import json
from pathlib import Path
from typing import Dict, Any


class Config:
    """Global configuration manager"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")

        # Return default configuration
        return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "anki": {
                "host": "localhost",
                "port": 8765,
                "api_version": 6
            },
            "media": {
                "pixabay_api_key": os.environ.get('PIXABAY_API_KEY', ''),
                "pexels_api_key": os.environ.get('PEXELS_API_KEY', ''),
                "unsplash_api_key": os.environ.get('UNSPLASH_API_KEY', ''),
                "download_timeout": 15,
                "max_image_size": 1024 * 1024 * 2,  # 2MB
                "fallback_image_size": (400, 300),
                "audio_speed": "slow"  # slow or normal
            },
            "decks": {
                "base_name": "Vocabulary",
                "structure": {
                    "vocabulary": "1 Vocabulary",
                    "cloze": "2 Cloze",
                    "pronunciation": "3 Pronunciation",
                    "exercise": "4 Exercises"
                },
                "options": {
                    "vocabulary": {
                        "new_per_day": 20,
                        "learning_steps": [1, 10],
                        "graduating_interval": 1,
                        "easy_interval": 4,
                        "starting_ease": 2500,
                        "maximum_interval": 36500,
                        "review_per_day": 200
                    },
                    "cloze": {
                        "new_per_day": 15,
                        "learning_steps": [10, 25],
                        "graduating_interval": 2,
                        "easy_interval": 5,
                        "starting_ease": 2000,
                        "maximum_interval": 36500,
                        "review_per_day": 150
                    },
                    "pronunciation": {
                        "new_per_day": 10,
                        "learning_steps": [1, 5],
                        "graduating_interval": 1,
                        "easy_interval": 4,
                        "starting_ease": 2500,
                        "maximum_interval": 36500,
                        "review_per_day": 100
                    },
                    "exercise": {
                        "new_per_day": 10,
                        "learning_steps": [10, 30],
                        "graduating_interval": 3,
                        "easy_interval": 7,
                        "starting_ease": 1500,
                        "maximum_interval": 36500,
                        "review_per_day": 100
                    }
                }
            },
            "processing": {
                "batch_size": 50,
                "rate_limit_delay": 0.5,
                "auto_backup": True,
                "backup_before_import": True,
                "skip_duplicates": True,
                "case_sensitive": False
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "anki_vocabulary.log",
                "max_size": 10 * 1024 * 1024,  # 10MB
                "backup_count": 5
            },
            "ui": {
                "use_colors": True,
                "clear_screen": True,
                "confirm_actions": True,
                "show_progress": True
            }
        }

    def save(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation

        Args:
            key_path: Dot-separated path (e.g., "anki.port")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """
        Set configuration value using dot notation

        Args:
            key_path: Dot-separated path (e.g., "anki.port")
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config

        # Navigate to the parent
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set the value
        config[keys[-1]] = value

    def get_anki_url(self) -> str:
        """Get AnkiConnect URL"""
        host = self.get('anki.host', 'localhost')
        port = self.get('anki.port', 8765)
        return f"http://{host}:{port}"

    def get_deck_options(self, deck_type: str) -> Dict[str, Any]:
        """Get deck options for a specific deck type"""
        return self.get(f'decks.options.{deck_type}', {})

    def get_media_api_key(self, service: str) -> str:
        """Get API key for media service"""
        return self.get(f'media.{service}_api_key', '')

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return self.get(f'features.{feature}', False)

    def update_from_env(self):
        """Update configuration from environment variables"""
        # Update API keys
        for service in ['pixabay', 'pexels', 'unsplash']:
            env_key = f'{service.upper()}_API_KEY'
            if env_key in os.environ:
                self.set(f'media.{service}_api_key', os.environ[env_key])

        # Update Anki connection
        if 'ANKI_HOST' in os.environ:
            self.set('anki.host', os.environ['ANKI_HOST'])
        if 'ANKI_PORT' in os.environ:
            self.set('anki.port', int(os.environ['ANKI_PORT']))

    def validate(self) -> bool:
        """Validate configuration"""
        # Check required fields
        required = [
            'anki.host',
            'anki.port',
            'decks.base_name'
        ]

        for field in required:
            if not self.get(field):
                print(f"Missing required config: {field}")
                return False

        # Check port is valid
        port = self.get('anki.port')
        if not isinstance(port, int) or port < 1 or port > 65535:
            print(f"Invalid port: {port}")
            return False

        return True