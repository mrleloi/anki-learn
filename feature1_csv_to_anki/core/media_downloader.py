#!/usr/bin/env python3
"""
Media Downloader
Downloads images and audio for vocabulary words

Author: Assistant
Version: 3.0
"""

#!/usr/bin/env python3
"""
Media Downloader
Downloads images and audio for vocabulary words, with caching support

Author: Assistant
Version: 3.1 (with local media cache)
"""

import os
import requests
import json
import logging
import time
from pathlib import Path
from typing import Optional, Tuple, List
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
import io


class MediaDownloader:
    """Download and manage media files for Anki cards"""

    def __init__(self, anki_client=None):
        self.logger = logging.getLogger(__name__)
        self.anki_client = anki_client

        # API Keys
        self.pixabay_key = os.environ.get('PIXABAY_API_KEY', '50872335-2b97ba59b3d6f172e1a571e5b')
        self.pexels_key = os.environ.get('PEXELS_API_KEY', '')
        self.unsplash_key = os.environ.get('UNSPLASH_API_KEY', '')

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

    def download_image(self, word: str, part_of_speech: str = None,
                       vietnamese: str = None) -> Optional[str]:
        filename = f"{word.lower().replace(' ', '_')}.jpg"
        local_path = self.image_cache / filename

        if local_path.exists():
            self.logger.info(f"Using cached image: {local_path}")
            return str(local_path)

        if self.anki_client and self._check_media_exists(filename):
            self.logger.info(f"Image already in Anki: {filename}")
            return filename

        image_data = None
        image_data, _ = self._try_langeek(word)

        if not image_data:
            for term in self._get_search_terms(word, part_of_speech, vietnamese):
                if not image_data and self.pexels_key:
                    image_data = self._try_pexels(term)
                if not image_data and self.unsplash_key:
                    image_data = self._try_unsplash(term)
                if not image_data:
                    image_data = self._try_pixabay(term)
                if image_data:
                    break

        if not image_data:
            self.logger.warning(f"No image found for {word}, creating text image")
            image_data = self._create_text_image(word, vietnamese)

        if image_data:
            try:
                with open(local_path, 'wb') as f:
                    f.write(image_data)
                self.logger.info(f"Saved image locally: {local_path}")

                if self.anki_client:
                    stored_filename = self.anki_client.store_media_file(filename, image_data)
                    return stored_filename

                return str(local_path)

            except Exception as e:
                self.logger.error(f"Failed to save image {filename}: {e}")

        return None

    def download_audio(self, word: str, pronunciation: str = None) -> Optional[str]:
        filename = f"{word.lower().replace(' ', '_')}.mp3"
        local_path = self.audio_cache / filename

        if local_path.exists():
            self.logger.info(f"Using cached audio: {local_path}")
            return str(local_path)

        if self.anki_client and self._check_media_exists(filename):
            self.logger.info(f"Audio already in Anki: {filename}")
            return filename

        try:
            tts = gTTS(text=word, lang='en', slow=True)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_data = audio_buffer.getvalue()

            with open(local_path, 'wb') as f:
                f.write(audio_data)
            self.logger.info(f"Saved audio locally: {local_path}")

            if self.anki_client:
                stored_filename = self.anki_client.store_media_file(filename, audio_data)
                return stored_filename

            return str(local_path)

        except Exception as e:
            self.logger.error(f"Failed to generate audio for {word}: {e}")
            return None


    def _check_media_exists(self, filename: str) -> bool:
        """Check if media file already exists in Anki"""
        try:
            return self.anki_client.check_media_exists(filename)
        except:
            return False

    def _respect_rate_limit(self, api_name: str):
        """Respect API rate limits"""
        if api_name in self.last_api_call:
            elapsed = time.time() - self.last_api_call[api_name]
            delay_needed = self.api_delays.get(api_name, 0.5)

            if elapsed < delay_needed:
                time.sleep(delay_needed - elapsed)

        self.last_api_call[api_name] = time.time()

    def _get_search_terms(self, word: str, part_of_speech: str = None,
                          vietnamese: str = None) -> List[str]:
        """Generate smart search terms based on word type"""
        terms = []

        if part_of_speech:
            pos = part_of_speech.lower()

            if pos in ['adj', 'adjective']:
                # For personality traits
                terms.extend([
                    f"{word} person face",
                    f"{word} personality trait",
                    f"person looking {word}",
                    f"{word} emotion expression"
                ])
            elif pos in ['noun', 'n']:
                terms.extend([
                    word,
                    f"{word} concept",
                    f"{word} illustration"
                ])
            elif pos in ['verb', 'v']:
                terms.extend([
                    f"person {word}",
                    f"{word} action",
                    f"people {word}"
                ])

        # Always add the word itself
        terms.append(word)

        return terms

    def _try_langeek(self, word: str) -> Tuple[Optional[bytes], Optional[dict]]:
        """Try to get image from Langeek API"""
        self._respect_rate_limit('langeek')

        url = f"https://api.langeek.co/v1/cs/en/word/?term={word}&filter=,inCategory,photo"
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()

                if data and len(data) > 0:
                    word_info = data[0]

                    # Extract photo URL
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
                            self.logger.info(f"Found image on Langeek for: {word}")
                            return img_response.content, word_info

        except Exception as e:
            self.logger.debug(f"Langeek API error for {word}: {e}")

        return None, None

    def _try_pexels(self, search_term: str) -> Optional[bytes]:
        """Try to get image from Pexels API"""
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
                        self.logger.info(f"Found image on Pexels for: {search_term}")
                        return img_response.content

        except Exception as e:
            self.logger.debug(f"Pexels API error: {e}")

        return None

    def _try_unsplash(self, search_term: str) -> Optional[bytes]:
        """Try to get image from Unsplash API"""
        if not self.unsplash_key:
            return None

        self._respect_rate_limit('unsplash')

        url = f"https://api.unsplash.com/search/photos"
        params = {
            'query': search_term,
            'per_page': 3,
            'client_id': self.unsplash_key
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()

                if data.get('results'):
                    photo = data['results'][0]
                    img_url = photo['urls']['small']

                    img_response = requests.get(img_url, timeout=15)
                    if img_response.status_code == 200:
                        self.logger.info(f"Found image on Unsplash for: {search_term}")
                        return img_response.content

        except Exception as e:
            self.logger.debug(f"Unsplash API error: {e}")

        return None

    def _try_pixabay(self, search_term: str) -> Optional[bytes]:
        """Try to get image from Pixabay API"""
        self._respect_rate_limit('pixabay')

        url = "https://pixabay.com/api/"
        params = {
            'key': self.pixabay_key,
            'q': search_term,
            'image_type': 'photo',
            'per_page': 3,
            'safesearch': 'true'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()

                if data.get('hits'):
                    image = data['hits'][0]
                    img_url = image['webformatURL']

                    img_response = requests.get(img_url, timeout=15)
                    if img_response.status_code == 200:
                        self.logger.info(f"Found image on Pixabay for: {search_term}")
                        return img_response.content

        except Exception as e:
            self.logger.debug(f"Pixabay API error: {e}")

        return None

    def _create_text_image(self, word: str, vietnamese: str = None) -> bytes:
        """Create a text-based image as fallback"""
        # Create image
        width, height = 400, 300
        img = Image.new('RGB', (width, height), color='#667eea')
        draw = ImageDraw.Draw(img)

        # Try to use a nice font, fallback to default
        try:
            font_large = ImageFont.truetype("arial.ttf", 48)
            font_small = ImageFont.truetype("arial.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Draw word
        word_upper = word.upper()
        bbox = draw.textbbox((0, 0), word_upper, font=font_large)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (width - text_width) // 2
        y = height // 3

        draw.text((x, y), word_upper, font=font_large, fill='white')

        # Draw Vietnamese meaning if available
        if vietnamese:
            viet_text = vietnamese[:30] + "..." if len(vietnamese) > 30 else vietnamese
            bbox = draw.textbbox((0, 0), viet_text, font=font_small)
            viet_width = bbox[2] - bbox[0]

            x_viet = (width - viet_width) // 2
            y_viet = y + text_height + 20

            draw.text((x_viet, y_viet), viet_text, font=font_small, fill='#FFD700')

        # Convert to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG', quality=85)

        return img_buffer.getvalue()

    def download_media_batch(self, words_data: List[dict]) -> dict:
        """
        Download media for multiple words in batch

        Args:
            words_data: List of word dictionaries

        Returns:
            Statistics about downloads
        """
        stats = {
            'images_downloaded': 0,
            'images_failed': 0,
            'audio_downloaded': 0,
            'audio_failed': 0,
            'total_time': 0
        }

        start_time = time.time()

        for word_data in words_data:
            word = word_data.get('word', '')

            # Download image
            try:
                image_file = self.download_image(
                    word,
                    word_data.get('part_of_speech'),
                    word_data.get('vietnamese')
                )
                if image_file:
                    word_data['image'] = image_file
                    stats['images_downloaded'] += 1
                else:
                    stats['images_failed'] += 1
            except Exception as e:
                self.logger.error(f"Error downloading image for {word}: {e}")
                stats['images_failed'] += 1

            # Download audio
            try:
                audio_file = self.download_audio(
                    word,
                    word_data.get('pronunciation')
                )
                if audio_file:
                    word_data['audio'] = audio_file
                    stats['audio_downloaded'] += 1
                else:
                    stats['audio_failed'] += 1
            except Exception as e:
                self.logger.error(f"Error downloading audio for {word}: {e}")
                stats['audio_failed'] += 1

        stats['total_time'] = time.time() - start_time

        self.logger.info(
            f"Media download complete: "
            f"{stats['images_downloaded']} images, "
            f"{stats['audio_downloaded']} audio files "
            f"in {stats['total_time']:.1f}s"
        )

        return stats