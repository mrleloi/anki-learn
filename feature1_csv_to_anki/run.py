#!/usr/bin/env python3
"""
🎯 MULTI-PROFILE CSV TO ANKI SYSTEM
Enhanced system that properly handles multiple Anki profiles

FIXES:
- Dynamic profile detection for media directory
- Profile-specific cache and processing
- Proper initialization flow: Connect → Select Profile → Detect Media → Process
- Multiple profile support with per-profile tracking

Author: Assistant
Version: 5.0 (Multi-profile support)
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import argparse
from typing import List, Dict, Optional, Tuple

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from feature1_csv_to_anki.core.anki_connect import AnkiConnectClient
from feature1_csv_to_anki.core.card_generator import CardGenerator
from shared.config import Config
from shared.utils import setup_logging, colored_print


class ProfileAwareMediaCache:
    """Media cache aware của multiple profiles"""
    
    def __init__(self, cache_file: Path = None, anki_client=None):
        self.cache_file = cache_file or Path("media_cache/media_registry.json")
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache_data = self._load_cache()
        self.anki_client = anki_client
        self.current_profile = None
        self.anki_media_dir = None
        
    def _load_cache(self) -> Dict[str, any]:
        """Load cache from JSON file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Migrate to profile-aware format
                    if isinstance(data, dict) and 'profiles' not in data:
                        return {
                            'version': '2.0',
                            'last_updated': datetime.now().isoformat(),
                            'profiles': {
                                'User 1': {  # Default profile for old data
                                    'media': data.get('media', {}),
                                    'anki_media_dir': data.get('anki_media_dir')
                                }
                            }
                        }
                    return data
            except Exception as e:
                logging.warning(f"Failed to load cache: {e}")
        
        return {
            'version': '2.0',
            'last_updated': datetime.now().isoformat(),
            'profiles': {}
        }
    
    def _save_cache(self):
        """Save cache to JSON file"""
        self.cache_data['last_updated'] = datetime.now().isoformat()
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Failed to save cache: {e}")
    
    def set_current_profile(self, profile_name: str):
        """Set current active profile"""
        self.current_profile = profile_name
        
        # Initialize profile data if not exists
        if profile_name not in self.cache_data['profiles']:
            self.cache_data['profiles'][profile_name] = {
                'media': {},
                'anki_media_dir': None
            }
        
        # Detect media directory for this profile
        self.anki_media_dir = self._detect_anki_media_dir_for_profile(profile_name)
    
    def _detect_anki_media_dir_for_profile(self, profile_name: str) -> Optional[Path]:
        """Detect Anki media directory for specific profile"""
        profile_data = self.cache_data['profiles'].get(profile_name, {})
        
        # Try cached path first
        cached_dir = profile_data.get('anki_media_dir')
        if cached_dir and Path(cached_dir).exists():
            colored_print(f"✅ Using cached media directory for {profile_name}: {cached_dir}", "green")
            return Path(cached_dir)
        
        # Try to get current profile info from AnkiConnect
        if self.anki_client:
            try:
                # Get all profiles to validate
                profiles = self.anki_client.get_profiles()
                if profile_name not in profiles:
                    colored_print(f"⚠️ Profile '{profile_name}' not found in Anki", "yellow")
                    return None
            except:
                pass
        
        # Build possible paths for this profile
        possible_paths = self._build_profile_paths(profile_name)
        
        # Check each possible path
        for path in possible_paths:
            try:
                if path.exists() and path.is_dir():
                    # Additional validation
                    if self._validate_anki_media_dir(path, profile_name):
                        # Cache the found path
                        self.cache_data['profiles'][profile_name]['anki_media_dir'] = str(path)
                        self._save_cache()
                        colored_print(f"✅ Auto-detected media directory for {profile_name}: {path}", "green")
                        return path
            except Exception as e:
                logging.debug(f"Error checking path {path}: {e}")
        
        # If auto-detection fails, try user input
        return self._prompt_user_for_media_dir(profile_name)
    
    def _build_profile_paths(self, profile_name: str) -> List[Path]:
        """Build possible media directory paths for a profile"""
        possible_paths = []
        
        if os.name == 'nt':  # Windows
            appdata = os.environ.get('APPDATA', '')
            localappdata = os.environ.get('LOCALAPPDATA', '')
            username = os.environ.get('USERNAME', 'user')
            
            base_paths = []
            if appdata:
                base_paths.append(Path(appdata) / 'Anki2')
            if localappdata:
                base_paths.append(Path(localappdata) / 'Anki2')
            
            # Add common drive locations
            for drive in ['C:', 'D:']:
                base_paths.extend([
                    Path(f"{drive}/Users/{username}/AppData/Roaming/Anki2"),
                    Path(f"{drive}/Users/{username}/Documents/Anki2"),
                ])
        else:  # macOS/Linux
            home = Path.home()
            base_paths = [
                home / 'Library/Application Support/Anki2',  # macOS
                home / '.local/share/Anki2',  # Linux
                home / 'Documents/Anki2',
                home / '.anki2',  # Alternative Linux
                home / 'snap/anki-woodrow/common/Anki2',  # Snap
                home / '.var/app/net.ankiweb.Anki/data/Anki2',  # Flatpak
            ]
        
        # Build full paths for the profile
        for base_path in base_paths:
            possible_paths.append(base_path / profile_name / 'collection.media')
        
        return possible_paths
    
    def _validate_anki_media_dir(self, path: Path, profile_name: str) -> bool:
        """Validate if directory is correct media directory for profile"""
        try:
            # Check if it's inside an Anki2 structure
            if 'Anki2' not in str(path):
                return False
            
            # Check if the profile name matches
            if profile_name not in str(path):
                return False
            
            # Check if parent directory has collection files
            parent = path.parent
            anki_files = list(parent.glob('collection.*')) + list(parent.glob('*.anki2'))
            return len(anki_files) > 0
        except:
            return False
    
    def _prompt_user_for_media_dir(self, profile_name: str) -> Optional[Path]:
        """Prompt user for media directory if auto-detection fails"""
        colored_print(f"⚠️ Could not auto-detect media directory for profile '{profile_name}'", "yellow")
        colored_print("Common locations:", "yellow")
        
        if os.name == 'nt':
            username = os.environ.get('USERNAME', 'YourName')
            colored_print(f"  Windows: C:/Users/{username}/AppData/Roaming/Anki2/{profile_name}/collection.media", "yellow")
        else:
            colored_print(f"  macOS: ~/Library/Application Support/Anki2/{profile_name}/collection.media", "yellow")
            colored_print(f"  Linux: ~/.local/share/Anki2/{profile_name}/collection.media", "yellow")
        
        try:
            user_path = input(f"Enter media directory path for '{profile_name}' (or press Enter to skip): ").strip()
            if user_path:
                user_path = Path(user_path)
                if user_path.exists() and user_path.is_dir():
                    self.cache_data['profiles'][profile_name]['anki_media_dir'] = str(user_path)
                    self._save_cache()
                    colored_print(f"✅ Using user-specified directory for {profile_name}: {user_path}", "green")
                    return user_path
                else:
                    colored_print("❌ Path does not exist or is not a directory", "red")
        except KeyboardInterrupt:
            pass
        
        colored_print(f"⚠️ Will use AnkiConnect for media operations in profile '{profile_name}' (slower)", "yellow")
        return None
    
    def get_anki_path(self, filename: str) -> Optional[Path]:
        """Get full path to media file in current profile's Anki directory"""
        if self.anki_media_dir:
            return self.anki_media_dir / filename
        return None
    
    def is_in_cache(self, filename: str) -> bool:
        """Check if file is in cache for current profile"""
        if not self.current_profile:
            return False
        profile_data = self.cache_data['profiles'].get(self.current_profile, {})
        return filename in profile_data.get('media', {})
    
    def is_in_anki(self, filename: str) -> bool:
        """Check if file exists in current profile's Anki media directory"""
        anki_path = self.get_anki_path(filename)
        return anki_path and anki_path.exists()
    
    def add_to_cache(self, filename: str, metadata: Dict[str, any] = None):
        """Add file to cache registry for current profile"""
        if not self.current_profile:
            return
        
        if self.current_profile not in self.cache_data['profiles']:
            self.cache_data['profiles'][self.current_profile] = {'media': {}, 'anki_media_dir': None}
        
        self.cache_data['profiles'][self.current_profile]['media'][filename] = {
            'added_date': datetime.now().isoformat(),
            'metadata': metadata or {},
            'verified': True
        }
        self._save_cache()
    
    def remove_from_cache(self, filename: str):
        """Remove file from cache registry for current profile"""
        if not self.current_profile:
            return
        
        profile_data = self.cache_data['profiles'].get(self.current_profile, {})
        media_data = profile_data.get('media', {})
        
        if filename in media_data:
            del media_data[filename]
            self._save_cache()
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get cache statistics for current profile"""
        if not self.current_profile:
            return {'error': 'No profile selected'}
        
        profile_data = self.cache_data['profiles'].get(self.current_profile, {})
        media_data = profile_data.get('media', {})
        
        total_files = len(media_data)
        verified_files = sum(1 for f in media_data.values() if f.get('verified', False))
        
        return {
            'profile': self.current_profile,
            'total_files': total_files,
            'verified_files': verified_files,
            'anki_media_dir': str(self.anki_media_dir) if self.anki_media_dir else None,
            'last_updated': self.cache_data.get('last_updated')
        }


class ProfileAwareMediaDownloader:
    """Media downloader với profile awareness"""
    
    def __init__(self, anki_client=None, cache_file: Path = None):
        self.logger = logging.getLogger(__name__)
        self.anki_client = anki_client
        self.cache = ProfileAwareMediaCache(cache_file, anki_client)
        self.current_profile = None

        # API Keys
        self.pixabay_key = os.environ.get('PIXABAY_API_KEY', '50872335-2b97ba59b3d6f172e1a571e5b')
        self.pexels_key = os.environ.get('PEXELS_API_KEY', 'NcnIox2PfBjNR7R8cTqiPR5dG47uXdenfN8VZReGgPgIXlIVNxdGmj68')
        self.unsplash_key = os.environ.get('UNSPLASH_API_KEY', 'h9kVF9j3KpUYeHd_O1ywkNtappE2pyFebrZh-e2583s')

        # Rate limiting
        self.last_api_call = {}
        self.api_delays = {
            'pixabay': 0.5,
            'pexels': 0.5,
            'unsplash': 0.5,
            'langeek': 1.0
        }

        # Local cache directories
        self.image_cache = Path("media_cache/images")
        self.audio_cache = Path("media_cache/audio")
        self.image_cache.mkdir(parents=True, exist_ok=True)
        self.audio_cache.mkdir(parents=True, exist_ok=True)
    
    def set_profile(self, profile_name: str):
        """Set current profile for media operations"""
        self.current_profile = profile_name
        self.cache.set_current_profile(profile_name)
        colored_print(f"📝 Media downloader set to profile: {profile_name}", "cyan")

    def download_image(self, word: str, part_of_speech: str = None,
                       vietnamese: str = None, force_download: bool = False) -> Optional[str]:
        """Download image for current profile"""
        if not self.current_profile:
            self.logger.error("No profile set for media downloader")
            return None
            
        filename = f"{word.lower().replace(' ', '_')}.jpg"
        local_path = self.image_cache / filename

        # Smart cache check
        if not force_download:
            if self.cache.is_in_cache(filename):
                if self.cache.is_in_anki(filename):
                    self.logger.info(f"Image in cache and Anki [{self.current_profile}]: {filename}")
                    return filename
                else:
                    self.cache.remove_from_cache(filename)
                    self.logger.warning(f"Image was in cache but not in Anki [{self.current_profile}]: {filename}")

        # Check local cache for re-upload
        if local_path.exists() and not force_download:
            self.logger.info(f"Using cached image [{self.current_profile}]: {local_path}")
            if self._upload_to_anki(local_path, filename):
                metadata = {
                    'word': word,
                    'part_of_speech': part_of_speech,
                    'vietnamese': vietnamese,
                    'source': 'local_cache',
                    'profile': self.current_profile
                }
                self.cache.add_to_cache(filename, metadata)
                return filename

        # Download new image
        self.logger.info(f"Downloading new image [{self.current_profile}]: {word}")
        image_data, source = self._download_image_data(word, part_of_speech, vietnamese)

        if image_data:
            try:
                # Save to local cache
                with open(local_path, 'wb') as f:
                    f.write(image_data)
                self.logger.info(f"Saved image locally [{self.current_profile}]: {local_path}")

                # Upload to Anki
                if self._upload_to_anki(local_path, filename):
                    metadata = {
                        'word': word,
                        'part_of_speech': part_of_speech,
                        'vietnamese': vietnamese,
                        'source': source,
                        'profile': self.current_profile
                    }
                    self.cache.add_to_cache(filename, metadata)
                    return filename

            except Exception as e:
                self.logger.error(f"Failed to save image [{self.current_profile}] {filename}: {e}")

        return None

    def download_audio(self, word: str, pronunciation: str = None, 
                      force_download: bool = False) -> Optional[str]:
        """Download audio for current profile"""
        if not self.current_profile:
            self.logger.error("No profile set for media downloader")
            return None
            
        filename = f"{word.lower().replace(' ', '_')}.mp3"
        local_path = self.audio_cache / filename

        # Smart cache check
        if not force_download:
            if self.cache.is_in_cache(filename):
                if self.cache.is_in_anki(filename):
                    self.logger.info(f"Audio in cache and Anki [{self.current_profile}]: {filename}")
                    return filename
                else:
                    self.cache.remove_from_cache(filename)
                    self.logger.warning(f"Audio was in cache but not in Anki [{self.current_profile}]: {filename}")

        # Check local cache for re-upload
        if local_path.exists() and not force_download:
            self.logger.info(f"Using cached audio [{self.current_profile}]: {local_path}")
            if self._upload_to_anki(local_path, filename):
                metadata = {
                    'word': word,
                    'pronunciation': pronunciation,
                    'source': 'tts_generated',
                    'profile': self.current_profile
                }
                self.cache.add_to_cache(filename, metadata)
                return filename

        # Generate new audio
        self.logger.info(f"Generating new audio [{self.current_profile}]: {word}")
        try:
            from gtts import gTTS
            import io
            
            tts = gTTS(text=word, lang='en', slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_data = audio_buffer.getvalue()

            # Save to local cache
            with open(local_path, 'wb') as f:
                f.write(audio_data)
            self.logger.info(f"Saved audio locally [{self.current_profile}]: {local_path}")

            # Upload to Anki
            if self._upload_to_anki(local_path, filename):
                metadata = {
                    'word': word,
                    'pronunciation': pronunciation,
                    'source': 'tts_generated',
                    'profile': self.current_profile
                }
                self.cache.add_to_cache(filename, metadata)
                return filename

        except Exception as e:
            self.logger.error(f"Failed to generate audio [{self.current_profile}] for {word}: {e}")

        return None

    def _upload_to_anki(self, file_path: Path, filename: str) -> bool:
        """Upload file to current profile's Anki"""
        if not self.anki_client:
            # Direct copy to profile's media directory
            anki_path = self.cache.get_anki_path(filename)
            if anki_path:
                try:
                    import shutil
                    shutil.copy2(file_path, anki_path)
                    self.logger.info(f"Copied directly to Anki [{self.current_profile}]: {anki_path}")
                    return True
                except Exception as e:
                    self.logger.error(f"Failed to copy to Anki directory [{self.current_profile}]: {e}")
            return False

        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            self.anki_client.store_media_file(filename, file_data)
            self.logger.info(f"Uploaded to Anki via AnkiConnect [{self.current_profile}]: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to upload to Anki [{self.current_profile}]: {e}")
            return False

    # ... [Include all the _download_image_data, _try_* methods from previous version]
    def _download_image_data(self, word: str, part_of_speech: str = None, vietnamese: str = None):
        """Download image data from various sources"""
        import requests
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        # Try Langeek first
        image_data, _ = self._try_langeek(word)
        if image_data:
            return image_data, 'langeek'

        # Try other APIs
        for term in self._get_search_terms(word, part_of_speech, vietnamese):
            if self.pexels_key:
                image_data = self._try_pexels(term)
                if image_data:
                    return image_data, 'pexels'
            
            if self.unsplash_key:
                image_data = self._try_unsplash(term)
                if image_data:
                    return image_data, 'unsplash'
            
            image_data = self._try_pixabay(term)
            if image_data:
                return image_data, 'pixabay'

        # Fallback to text image
        self.logger.warning(f"No image found for {word}, creating text image")
        text_image = self._create_text_image(word, vietnamese)
        return text_image, 'text_generated'

    def _respect_rate_limit(self, api_name: str):
        if api_name in self.last_api_call:
            elapsed = time.time() - self.last_api_call[api_name]
            delay_needed = self.api_delays.get(api_name, 0.5)
            if elapsed < delay_needed:
                time.sleep(delay_needed - elapsed)
        self.last_api_call[api_name] = time.time()

    def _get_search_terms(self, word: str, part_of_speech: str = None, vietnamese: str = None) -> List[str]:
        terms = []
        if part_of_speech:
            pos = part_of_speech.lower()
            if pos in ['adj', 'adjective']:
                terms.extend([f"{word} person face", f"{word} personality trait"])
            elif pos in ['noun', 'n']:
                terms.extend([word, f"{word} concept"])
            elif pos in ['verb', 'v']:
                terms.extend([f"person {word}", f"{word} action"])
        terms.append(word)
        return terms

    def _try_langeek(self, word: str):
        import requests
        self._respect_rate_limit('langeek')
        url = f"https://api.langeek.co/v1/cs/en/word/?term={word}&filter=,inCategory,photo"
        headers = {'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    word_info = data[0]
                    photo_url = None
                    if 'translations' in word_info:
                        for pos, translations in word_info['translations'].items():
                            for translation in translations:
                                if translation.get('wordPhoto', {}).get('photo'):
                                    photo_url = translation['wordPhoto']['photo']
                                    break
                            if photo_url:
                                break
                    if photo_url:
                        img_response = requests.get(photo_url, timeout=15)
                        if img_response.status_code == 200:
                            return img_response.content, word_info
        except Exception as e:
            self.logger.debug(f"Langeek API error for {word}: {e}")
        return None, None

    def _try_pexels(self, search_term: str):
        import requests
        if not self.pexels_key:
            return None
        self._respect_rate_limit('pexels')
        headers = {'Authorization': self.pexels_key}
        url = f"https://api.pexels.com/v1/search?query={search_term}&per_page=3"
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('photos'):
                    photo = data['photos'][0]
                    img_url = photo['src']['medium']
                    img_response = requests.get(img_url, timeout=15)
                    if img_response.status_code == 200:
                        return img_response.content
        except Exception as e:
            self.logger.debug(f"Pexels API error: {e}")
        return None

    def _try_unsplash(self, search_term: str):
        import requests
        if not self.unsplash_key:
            return None
        self._respect_rate_limit('unsplash')
        url = f"https://api.unsplash.com/search/photos"
        params = {'query': search_term, 'per_page': 3, 'client_id': self.unsplash_key}
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    photo = data['results'][0]
                    img_url = photo['urls']['small']
                    img_response = requests.get(img_url, timeout=15)
                    if img_response.status_code == 200:
                        return img_response.content
        except Exception as e:
            self.logger.debug(f"Unsplash API error: {e}")
        return None

    def _try_pixabay(self, search_term: str):
        import requests
        self._respect_rate_limit('pixabay')
        url = "https://pixabay.com/api/"
        params = {'key': self.pixabay_key, 'q': search_term, 'image_type': 'photo', 'per_page': 3, 'safesearch': 'true'}
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('hits'):
                    image = data['hits'][0]
                    img_url = image['webformatURL']
                    img_response = requests.get(img_url, timeout=15)
                    if img_response.status_code == 200:
                        return img_response.content
        except Exception as e:
            self.logger.debug(f"Pixabay API error: {e}")
        return None

    def _create_text_image(self, word: str, vietnamese: str = None) -> bytes:
        from PIL import Image, ImageDraw, ImageFont
        import io
        
        width, height = 400, 300
        img = Image.new('RGB', (width, height), color='#667eea')
        draw = ImageDraw.Draw(img)
        try:
            font_large = ImageFont.truetype("arial.ttf", 48)
            font_small = ImageFont.truetype("arial.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        word_upper = word.upper()
        bbox = draw.textbbox((0, 0), word_upper, font=font_large)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = (width - text_width) // 2, height // 3
        draw.text((x, y), word_upper, font=font_large, fill='white')

        if vietnamese:
            viet_text = vietnamese[:30] + "..." if len(vietnamese) > 30 else vietnamese
            bbox = draw.textbbox((0, 0), viet_text, font=font_small)
            viet_width = bbox[2] - bbox[0]
            x_viet, y_viet = (width - viet_width) // 2, y + text_height + 20
            draw.text((x_viet, y_viet), viet_text, font=font_small, fill='#FFD700')

        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG', quality=85)
        return img_buffer.getvalue()


class DeckManager:
    """Simple deck manager"""
    def __init__(self, anki_client):
        self.anki_client = anki_client
        self.logger = logging.getLogger(__name__)
    
    def create_deck(self, deck_name: str) -> bool:
        try:
            existing_decks = self.anki_client.deck_names()
            if deck_name not in existing_decks:
                self.anki_client.create_deck(deck_name)
                self.logger.info(f"Created deck: {deck_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create deck {deck_name}: {e}")
            return False


class ProfileManager:
    """Enhanced profile manager"""
    def __init__(self, anki_client):
        self.anki_client = anki_client
        self.logger = logging.getLogger(__name__)
        self._current_profile = None
    
    def get_profiles(self) -> List[str]:
        try:
            profiles = self.anki_client.get_profiles()
            self.logger.info(f"Found {len(profiles)} profiles: {profiles}")
            return profiles
        except Exception as e:
            self.logger.error(f"Failed to get profiles: {e}")
            return []
    
    def get_current_profile(self) -> Optional[str]:
        return self._current_profile
    
    def switch_profile(self, profile_name: str) -> bool:
        try:
            profiles = self.get_profiles()
            if profile_name not in profiles:
                self.logger.error(f"Profile '{profile_name}' not found")
                return False

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


class MultiProfileCSVProcessor:
    """Main processor với full multi-profile support"""

    def __init__(self):
        self.config = Config()
        self.anki_client = AnkiConnectClient()
        self.card_generator = CardGenerator()
        self.profile_manager = ProfileManager(self.anki_client)
        self.deck_manager = DeckManager(self.anki_client)
        
        # Will be initialized after profile selection
        self.media_downloader = None
        self.current_profile = None
        self.cloze_model_name = "Cloze"

        # Paths
        self.input_dir = Path("input")
        self.logs_dir = Path("logs")
        
        # Profile-specific tracking
        self.processed_files = {}  # profile -> list of processed files
        self.import_history = {}   # profile -> import history

        # Create directories
        self.input_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

    def check_anki_connection(self) -> bool:
        """Check connection before profile operations"""
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

    def select_and_initialize_profile(self) -> Tuple[Optional[str], bool]:
        """Select profile and initialize all profile-dependent components"""
        colored_print("\n📝 Profile Selection", "cyan")
        colored_print("=" * 30, "cyan")
        
        profiles = self.profile_manager.get_profiles()
        if not profiles:
            colored_print("❌ No profiles found!", "red")
            return None, False

        # Show available profiles
        colored_print("\nAvailable Anki Profiles:", "blue")
        for i, profile in enumerate(profiles, 1):
            print(f"  {i}. {profile}")

        # Get user choice
        try:
            choice = input(f"\n👉 Select profile (1-{len(profiles)}): ").strip()
            if not choice.isdigit() or int(choice) < 1 or int(choice) > len(profiles):
                colored_print("❌ Invalid selection!", "red")
                return None, False
            
            selected_profile = profiles[int(choice) - 1]
            
        except KeyboardInterrupt:
            colored_print("\n👋 Selection cancelled", "yellow")
            return None, False
        except Exception as e:
            colored_print(f"❌ Error in selection: {e}", "red")
            return None, False

        # Switch to selected profile
        colored_print(f"\n🔄 Switching to profile: {selected_profile}", "cyan")
        if not self.profile_manager.switch_profile(selected_profile):
            colored_print(f"❌ Failed to switch to profile: {selected_profile}", "red")
            return None, False

        self.current_profile = selected_profile
        colored_print(f"✅ Successfully switched to profile: {selected_profile}", "green")

        # Initialize profile-dependent components
        return self._initialize_profile_components(selected_profile)

    def _initialize_profile_components(self, profile_name: str) -> Tuple[str, bool]:
        """Initialize all components that depend on profile"""
        colored_print(f"\n🔧 Initializing components for profile: {profile_name}", "cyan")
        
        try:
            # Initialize media downloader with profile awareness
            self.media_downloader = ProfileAwareMediaDownloader(
                self.anki_client, 
                cache_file=self.logs_dir / f"media_cache_{profile_name.replace(' ', '_')}.json"
            )
            self.media_downloader.set_profile(profile_name)
            
            # Load profile-specific processed files
            self._load_profile_data(profile_name)
            
            # Ensure required models exist
            if not self._ensure_cloze_model_exists():
                colored_print("⚠️ Warning: Cloze model check failed", "yellow")
            
            # Show profile info
            self._show_profile_info(profile_name)
            
            colored_print(f"✅ Profile '{profile_name}' ready for processing", "green")
            return profile_name, True
            
        except Exception as e:
            colored_print(f"❌ Failed to initialize profile components: {e}", "red")
            return profile_name, False

    def _load_profile_data(self, profile_name: str):
        """Load profile-specific processed files and history"""
        safe_profile_name = profile_name.replace(' ', '_').replace('/', '_')
        
        # Load processed files for this profile
        processed_file = self.input_dir / f".processed_{safe_profile_name}"
        if processed_file.exists():
            self.processed_files[profile_name] = [
                line.strip() for line in processed_file.read_text().splitlines()
            ]
        else:
            self.processed_files[profile_name] = []
        
        # Load import history for this profile
        history_file = self.logs_dir / f"import_history_{safe_profile_name}.json"
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                self.import_history[profile_name] = json.load(f)
        else:
            self.import_history[profile_name] = {"imports": []}

    def _save_profile_data(self, profile_name: str):
        """Save profile-specific data"""
        safe_profile_name = profile_name.replace(' ', '_').replace('/', '_')
        
        # Save processed files
        processed_file = self.input_dir / f".processed_{safe_profile_name}"
        with open(processed_file, 'w') as f:
            for filename in self.processed_files.get(profile_name, []):
                f.write(f"{filename}\n")
        
        # Save import history
        history_file = self.logs_dir / f"import_history_{safe_profile_name}.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.import_history.get(profile_name, {"imports": []}), 
                     f, indent=2, ensure_ascii=False)

    def _show_profile_info(self, profile_name: str):
        """Show information about current profile"""
        try:
            # Get basic profile stats
            decks = self.anki_client.deck_names()
            vocab_decks = [d for d in decks if d.startswith("Vocabulary::")]
            
            # Get media cache stats
            cache_stats = self.media_downloader.cache.get_cache_stats()
            
            # Get processed files count
            processed_count = len(self.processed_files.get(profile_name, []))
            
            colored_print(f"\n📊 Profile Information: {profile_name}", "blue")
            print(f"  📚 Total decks: {len(decks)}")
            print(f"  📖 Vocabulary decks: {len(vocab_decks)}")
            print(f"  📁 Processed CSV files: {processed_count}")
            print(f"  🖼️ Cached media files: {cache_stats.get('total_files', 0)}")
            
            media_dir = cache_stats.get('anki_media_dir')
            if media_dir:
                print(f"  📂 Media directory: {media_dir}")
            else:
                print(f"  📂 Media directory: Using AnkiConnect (slower)")
                
        except Exception as e:
            self.logger.error(f"Error showing profile info: {e}")

    def detect_new_files_for_profile(self, profile_name: str) -> List[Path]:
        """Detect new CSV files for specific profile"""
        processed = set(self.processed_files.get(profile_name, []))
        input_files = list(self.input_dir.glob("*.[cx]sv")) \
                      + list(self.input_dir.glob("*.xlsx")) \
                      + list(self.input_dir.glob("*.xls"))
        
        new_files = [f for f in input_files 
                    if f.name not in processed 
                    and 'template' not in f.name.lower()]
        
        return new_files

    def _ensure_cloze_model_exists(self) -> bool:
        """Ensure Cloze model exists in current profile"""
        try:
            models = self.anki_client.model_names()
            
            # Check for cloze models
            cloze_model_names = ["Cloze", "Cloze (old)", "Cloze (type-in)"]
            cloze_model = None
            
            for model in models:
                if any(cloze_name in model for cloze_name in cloze_model_names):
                    cloze_model = model
                    break
                    
            if not cloze_model:
                # Create new cloze model
                colored_print(f"⚠️ Creating 'Vocabulary Cloze' model in profile: {self.current_profile}", "yellow")
                self.anki_client.create_model(
                    model_name="Vocabulary Cloze",
                    fields=["Text", "Back Extra"],
                    css="""
.card {
    font-family: arial;
    font-size: 20px;
    text-align: center;
    color: black;
    background-color: white;
}
.cloze {
    font-weight: bold;
    color: blue;
}""",
                    card_templates=[{
                        'Name': 'Cloze Card',
                        'Front': '{{cloze:Text}}',
                        'Back': '{{cloze:Text}}<br>{{Back Extra}}'
                    }]
                )
                self.cloze_model_name = "Vocabulary Cloze"
                colored_print("✅ Cloze model created successfully", "green")
            else:
                self.cloze_model_name = cloze_model
                colored_print(f"✅ Using existing cloze model: {cloze_model}", "green")
                
            return True
        except Exception as e:
            colored_print(f"❌ Failed to check/create Cloze model: {e}", "red")
            return False

    def _mark_as_processed(self, filename: str, profile_name: str):
        """Mark file as processed for specific profile"""
        if profile_name not in self.processed_files:
            self.processed_files[profile_name] = []
        
        if filename not in self.processed_files[profile_name]:
            self.processed_files[profile_name].append(filename)
        
        self._save_profile_data(profile_name)

    def _bulk_add(self, notes: List[Dict], stat_key: str, result: Dict):
        """Bulk add notes with error handling"""
        if not notes:
            return
            
        try:
            added_ids = self.anki_client.add_notes(notes)
            successful = len([nid for nid in added_ids if nid])
            result['stats'][stat_key] += successful
            
            failed = len(notes) - successful
            if failed > 0:
                logging.warning(f"Failed to add {failed} {stat_key}")
                
            colored_print(f"✅ Bulk added {successful} cards ({stat_key})", "green")
        except Exception as e:
            logging.error(f"Bulk add error for {stat_key}: {e}. Falling back to individual adds.")
            # Fallback to individual adds
            for note in notes:
                try:
                    note_id = self.anki_client.add_note(
                        deck_name=note['deckName'],
                        model_name=note['modelName'],
                        fields=note['fields'],
                        tags=note.get('tags', []),
                        allow_duplicate=note.get('options', {}).get('allowDuplicate', False)
                    )
                    if note_id:
                        result['stats'][stat_key] += 1
                except Exception as ie:
                    msg = str(ie).lower()
                    if 'duplicate' in msg:
                        logging.debug(f"Skipped duplicate {stat_key}")
                    else:
                        logging.error(f"Failed to add card: {ie}")
                        result['stats']['errors'].append(f"{stat_key}: {str(ie)[:100]}")

    def process_csv_file(self, csv_file: Path) -> Dict:
        """Process CSV file in current profile"""
        if not self.current_profile:
            raise Exception("No profile selected")
            
        colored_print(f"\n📄 Processing: {csv_file.name} → Profile: {self.current_profile}", "blue")
        
        result = {
            "file": csv_file.name,
            "profile": self.current_profile,
            "timestamp": datetime.now().isoformat(),
            "stats": {
                'vocabulary_cards': 0,
                'cloze_cards': 0,
                'pronunciation_cards': 0,
                'exercise_cards': 0,
                'media_downloaded': 0,
                'errors': []
            }
        }
        
        try:
            # Parse CSV
            parsed = self.card_generator.parse_file(csv_file)
            vocab_data = parsed.get('vocabulary', [])
            ex_data = parsed.get('exercises', [])
            
            if not vocab_data and not ex_data:
                colored_print("⚠️ No valid data found in CSV", "yellow")
                return result
            
            # Download media
            colored_print("📥 Downloading media files...", "cyan")
            for wd in vocab_data:
                try:
                    img = self.media_downloader.download_image(
                        wd['word'], wd.get('part_of_speech'), wd.get('vietnamese')
                    )
                    if img: 
                        wd['image'] = img
                        result['stats']['media_downloaded'] += 1
                        
                    aud = self.media_downloader.download_audio(
                        wd['word'], wd.get('pronunciation')
                    )
                    if aud: 
                        wd['audio'] = aud
                        result['stats']['media_downloaded'] += 1
                except Exception as e:
                    logging.error(f"Media error for {wd['word']}: {e}")
                    result['stats']['errors'].append(f"Media: {wd['word']}")
                    
            # Create decks
            lesson = csv_file.stem.replace('_', ' ').title()
            base = f"Vocabulary::{lesson}"
            decks = {
                'vocabulary': f"{base}::1 Vocabulary",
                'cloze': f"{base}::2 Cloze",
                'pronunciation': f"{base}::3 Pronunciation",
                'exercise': f"{base}::4 Exercises"
            }
            
            colored_print("📚 Creating decks...", "cyan")
            for deck_name in decks.values():
                self.deck_manager.create_deck(deck_name)
                
            # Prepare cards
            colored_print("🃏 Preparing cards...", "cyan")
            cards_vocab = self.card_generator.create_vocabulary_cards(vocab_data)
            cards_cloze = self.card_generator.create_cloze_cards(vocab_data)
            cards_pron = self.card_generator.create_pronunciation_cards(vocab_data)
            cards_ex = self.card_generator.create_exercise_cards(ex_data)
            
            # Convert to Anki notes format
            notes_vocab = [
                {
                    'deckName': decks['vocabulary'],
                    'modelName': 'Basic',
                    'fields': c['fields'],
                    'tags': c['tags'],
                    'options': {'allowDuplicate': True}
                }
                for c in cards_vocab
            ]
            
            notes_cloze = [
                {
                    'deckName': decks['cloze'],
                    'modelName': self.cloze_model_name,
                    'fields': c['fields'],
                    'tags': c['tags'],
                    'options': {'allowDuplicate': True}
                }
                for c in cards_cloze
            ]
            
            notes_pron = [
                {
                    'deckName': decks['pronunciation'],
                    'modelName': 'Basic',
                    'fields': c['fields'],
                    'tags': c['tags'],
                    'options': {'allowDuplicate': True}
                }
                for c in cards_pron
            ]
            
            notes_ex = [
                {
                    'deckName': decks['exercise'],
                    'modelName': 'Basic',
                    'fields': c['fields'],
                    'tags': c['tags'],
                    'options': {'allowDuplicate': True}
                }
                for c in cards_ex
            ]
            
            # Bulk add all card types
            colored_print("⚡ Adding cards to Anki...", "cyan")
            self._bulk_add(notes_vocab, 'vocabulary_cards', result)
            self._bulk_add(notes_cloze, 'cloze_cards', result)
            self._bulk_add(notes_pron, 'pronunciation_cards', result)
            self._bulk_add(notes_ex, 'exercise_cards', result)
            
            # Mark as processed and save history
            self._mark_as_processed(csv_file.name, self.current_profile)
            
            if self.current_profile not in self.import_history:
                self.import_history[self.current_profile] = {"imports": []}
            self.import_history[self.current_profile]['imports'].append(result)
            self._save_profile_data(self.current_profile)
            
            # Sync if cards were added
            total_cards = sum([
                result['stats']['vocabulary_cards'],
                result['stats']['cloze_cards'],
                result['stats']['pronunciation_cards'],
                result['stats']['exercise_cards']
            ])
            
            if total_cards > 0:
                try:
                    colored_print("🔄 Syncing with AnkiWeb...", "cyan")
                    self.anki_client.sync()
                    colored_print("✅ Synced with AnkiWeb", "green")
                except Exception as e:
                    logging.warning(f"Sync failed: {e}")
                    
            colored_print(f"✅ Successfully processed {csv_file.name} in profile {self.current_profile}", "green")
            
        except Exception as e:
            colored_print(f"❌ Error processing {csv_file.name}: {e}", "red")
            result['stats']['errors'].append(str(e))
            logging.exception("CSV processing error")
        
        return result

    def show_summary(self, results: List[Dict], profile_name: str):
        """Show processing summary for profile"""
        colored_print("\n" + "=" * 60, "blue")
        colored_print(f"📊 IMPORT SUMMARY - Profile: {profile_name}", "blue")
        colored_print("=" * 60, "blue")

        if not results:
            colored_print("No files were processed.", "yellow")
            return

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

        # Show cache stats
        try:
            cache_stats = self.media_downloader.cache.get_cache_stats()
            print(f"\n📂 Cache statistics:")
            print(f"   - Profile: {cache_stats.get('profile', 'Unknown')}")
            print(f"   - Cached files: {cache_stats.get('total_files', 0)}")
            media_dir = cache_stats.get('anki_media_dir')
            print(f"   - Media directory: {media_dir if media_dir else 'Using AnkiConnect'}")
        except Exception as e:
            logging.debug(f"Error getting cache stats: {e}")

        # Show errors
        all_errors = []
        for r in results:
            if r['stats']['errors']:
                all_errors.extend(r['stats']['errors'])

        if all_errors:
            colored_print(f"\n⚠️ Errors encountered: {len(all_errors)}", "yellow")
            for error in all_errors[:5]:
                print(f"   - {error}")
            if len(all_errors) > 5:
                print(f"   ... and {len(all_errors) - 5} more")


def main():
    """Main entry point với proper multi-profile flow"""
    parser = argparse.ArgumentParser(
        description="Multi-Profile CSV to Anki - Automated card creation with profile support"
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
    colored_print("\n🚀 MULTI-PROFILE CSV TO ANKI SYSTEM", "cyan")
    colored_print("=" * 50, "cyan")

    # Initialize processor
    processor = MultiProfileCSVProcessor()

    try:
        # Step 1: Check Anki connection
        colored_print("\n🔌 Checking Anki connection...", "cyan")
        if not processor.check_anki_connection():
            return 1

        # Step 2: Select and initialize profile (CRITICAL STEP)
        profile_name, success = processor.select_and_initialize_profile()
        if not success or not profile_name:
            colored_print("❌ Profile initialization failed", "red")
            return 1

        # Step 3: NOW detect files for the selected profile
        colored_print(f"\n📁 Detecting CSV files for profile: {profile_name}", "cyan")
        if args.all:
            csv_files = list(processor.input_dir.glob("*.csv")) + \
                       list(processor.input_dir.glob("*.xlsx")) + \
                       list(processor.input_dir.glob("*.xls"))
            csv_files = [f for f in csv_files if 'template' not in f.name.lower()]
        else:
            csv_files = processor.detect_new_files_for_profile(profile_name)

        if not csv_files:
            colored_print(f"\n📭 No new CSV files found for profile '{profile_name}'", "yellow")
            colored_print("Place your CSV files in the input/ folder and run again.", "yellow")
            return 0

        # Show files to process
        colored_print(f"\n📂 Found {len(csv_files)} file(s) to process in profile '{profile_name}':", "blue")
        for csv_file in csv_files:
            print(f"   - {csv_file.name}")

        # Confirm processing
        try:
            confirm = input(f"\n👉 Process {len(csv_files)} file(s) in profile '{profile_name}'? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                colored_print("Operation cancelled by user", "yellow")
                return 0
        except KeyboardInterrupt:
            colored_print("\n👋 Operation cancelled", "yellow")
            return 0

        # Step 4: Process each file
        colored_print(f"\n⚡ Processing files in profile: {profile_name}", "cyan")
        results = []
        for i, csv_file in enumerate(csv_files, 1):
            colored_print(f"\n[{i}/{len(csv_files)}] Processing file...", "blue")
            result = processor.process_csv_file(csv_file)
            results.append(result)
            time.sleep(1)  # Small delay between files

        # Step 5: Show summary
        processor.show_summary(results, profile_name)

        colored_print(f"\n✨ All done for profile '{profile_name}'! Happy studying! 🎓", "green")
        return 0

    except KeyboardInterrupt:
        colored_print("\n\n👋 Operation cancelled by user", "yellow")
        return 1
    except Exception as e:
        colored_print(f"\n❌ Unexpected error: {e}", "red")
        logging.exception("Unexpected error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
