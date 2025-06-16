#!/usr/bin/env python3
"""
Shared Utilities
Common utility functions for the Anki Vocabulary System

Author: Assistant
Version: 3.0
"""

import os
import sys
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, List, Dict

# Try to import colorama for colored output
try:
    from colorama import init, Fore, Back, Style

    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False


def colored_print(text: str, color: str = None, style: str = None):
    """
    Print colored text if colors are available

    Args:
        text: Text to print
        color: Color name (red, green, blue, yellow, cyan, magenta)
        style: Style (bright, dim)
    """
    if not COLORS_AVAILABLE or not color:
        print(text)
        return

    color_map = {
        'red': Fore.RED,
        'green': Fore.GREEN,
        'blue': Fore.BLUE,
        'yellow': Fore.YELLOW,
        'cyan': Fore.CYAN,
        'magenta': Fore.MAGENTA,
        'white': Fore.WHITE,
        'black': Fore.BLACK
    }

    style_map = {
        'bright': Style.BRIGHT,
        'dim': Style.DIM,
        'normal': Style.NORMAL
    }

    color_code = color_map.get(color.lower(), '')
    style_code = style_map.get(style.lower() if style else '', '')

    print(f"{style_code}{color_code}{text}{Style.RESET_ALL}")


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None,
                  max_size: int = 10 * 1024 * 1024, backup_count: int = 5) -> logging.Logger:
    """
    Setup logging configuration

    Args:
        level: Logging level
        log_file: Path to log file (optional)
        max_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep

    Returns:
        Root logger
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        try:
            # Create log directory if needed
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        except Exception as e:
            print(f"Failed to setup file logging: {e}")

    return root_logger


def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def confirm_action(prompt: str, default: bool = False) -> bool:
    """
    Ask user for confirmation

    Args:
        prompt: Confirmation prompt
        default: Default value if user just presses Enter

    Returns:
        True if confirmed
    """
    default_str = "[Y/n]" if default else "[y/N]"
    response = input(f"{prompt} {default_str}: ").strip().lower()

    if not response:
        return default

    return response in ['y', 'yes', 'true', '1']


def format_time_delta(seconds: float) -> str:
    """
    Format time delta in human-readable format

    Args:
        seconds: Time in seconds

    Returns:
        Formatted string (e.g., "2h 30m 15s")
    """
    if seconds < 1:
        return f"{seconds:.1f}s"

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} PB"


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    Sanitize filename by replacing invalid characters

    Args:
        filename: Original filename
        replacement: Character to replace invalid chars with

    Returns:
        Sanitized filename
    """
    import re

    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, replacement, filename)

    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip('. ')

    # Limit length
    max_length = 255
    if len(sanitized) > max_length:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:max_length - len(ext)] + ext

    return sanitized


def create_backup(file_path: str, backup_dir: str = "backups") -> Optional[str]:
    """
    Create a backup of a file

    Args:
        file_path: Path to file to backup
        backup_dir: Directory to store backups

    Returns:
        Path to backup file or None
    """
    try:
        source = Path(file_path)
        if not source.exists():
            return None

        # Create backup directory
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)

        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source.stem}_{timestamp}{source.suffix}"
        backup_file = backup_path / backup_name

        # Copy file
        import shutil
        shutil.copy2(source, backup_file)

        return str(backup_file)

    except Exception as e:
        logging.error(f"Failed to create backup: {e}")
        return None


def load_json_file(file_path: str) -> Optional[Dict]:
    """
    Load JSON file safely

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data or None
    """
    try:
        import json
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load JSON from {file_path}: {e}")
        return None


def save_json_file(data: Any, file_path: str, pretty: bool = True) -> bool:
    """
    Save data to JSON file

    Args:
        data: Data to save
        file_path: Path to save to
        pretty: Whether to pretty-print JSON

    Returns:
        True if successful
    """
    try:
        import json

        # Create directory if needed
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)

        return True

    except Exception as e:
        logging.error(f"Failed to save JSON to {file_path}: {e}")
        return False


def get_file_hash(file_path: str, algorithm: str = 'md5') -> Optional[str]:
    """
    Calculate file hash

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha1, sha256)

    Returns:
        Hex digest or None
    """
    try:
        import hashlib

        hash_func = getattr(hashlib, algorithm)()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)

        return hash_func.hexdigest()

    except Exception as e:
        logging.error(f"Failed to calculate hash: {e}")
        return None


def batch_process(items: List[Any], process_func, batch_size: int = 50,
                  show_progress: bool = True) -> List[Any]:
    """
    Process items in batches

    Args:
        items: List of items to process
        process_func: Function to process each item
        batch_size: Size of each batch
        show_progress: Whether to show progress

    Returns:
        List of results
    """
    results = []
    total = len(items)

    for i in range(0, total, batch_size):
        batch = items[i:i + batch_size]

        if show_progress:
            progress = (i + len(batch)) / total * 100
            print(f"Progress: {progress:.1f}% ({i + len(batch)}/{total})", end='\r')

        for item in batch:
            try:
                result = process_func(item)
                results.append(result)
            except Exception as e:
                logging.error(f"Error processing item: {e}")
                results.append(None)

    if show_progress:
        print()  # New line after progress

    return results


def create_progress_bar(current: int, total: int, width: int = 50) -> str:
    """
    Create a text progress bar

    Args:
        current: Current value
        total: Total value
        width: Width of progress bar

    Returns:
        Progress bar string
    """
    if total == 0:
        return "[" + "=" * width + "]"

    progress = current / total
    filled = int(width * progress)

    bar = "[" + "=" * filled + "-" * (width - filled) + "]"
    percentage = f" {progress * 100:.1f}%"

    return bar + percentage