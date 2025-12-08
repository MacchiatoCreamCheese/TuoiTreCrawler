"""
Helper utilities for the TuoiTre crawler
General-purpose utility functions
"""

import re
import time
import random
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from urllib.parse import urlparse, urljoin
import unicodedata


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename for safe file system storage

    Args:
        filename: Original filename
        max_length: Maximum filename length

    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

    # Normalize unicode characters (important for Vietnamese text)
    filename = unicodedata.normalize('NFKD', filename)

    # Remove leading/trailing spaces and dots
    filename = filename.strip('. ')

    # Ensure filename is not empty
    if not filename:
        filename = 'unnamed'

    # Truncate if too long, preserving extension
    if len(filename) > max_length:
        name, ext = Path(filename).stem, Path(filename).suffix
        name = name[:max_length - len(ext)]
        filename = name + ext

    return filename


def generate_unique_id(url: str = None, prefix: str = '') -> str:
    """
    Generate unique ID for posts/comments

    Args:
        url: URL to use for ID generation
        prefix: Optional prefix for the ID

    Returns:
        Unique identifier string
    """
    if url:
        # Use URL hash for deterministic IDs
        hash_obj = hashlib.md5(url.encode('utf-8'))
        unique_id = hash_obj.hexdigest()[:12]
    else:
        # Use timestamp + random for unique IDs
        timestamp = str(int(time.time() * 1000))
        random_part = str(random.randint(1000, 9999))
        unique_id = f"{timestamp}_{random_part}"

    return f"{prefix}{unique_id}" if prefix else unique_id


def normalize_url(url: str, base_url: str = None) -> str:
    """
    Normalize and validate URL

    Args:
        url: URL to normalize
        base_url: Base URL for relative URLs

    Returns:
        Normalized absolute URL
    """
    if not url:
        return ''

    # Handle relative URLs
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)

    # Remove fragments
    url = url.split('#')[0]

    return url.strip()


def extract_domain(url: str) -> str:
    """
    Extract domain from URL

    Args:
        url: URL to parse

    Returns:
        Domain name
    """
    parsed = urlparse(url)
    return parsed.netloc


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid

    Args:
        url: URL to validate

    Returns:
        True if URL is valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def clean_text(text: str) -> str:
    """
    Clean and normalize text content

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    if not text:
        return ''

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove leading/trailing whitespace
    text = text.strip()

    # Normalize unicode
    text = unicodedata.normalize('NFKC', text)

    return text


def parse_vietnamese_date(date_string: str) -> Optional[datetime]:
    """
    Parse Vietnamese date strings to datetime object

    Args:
        date_string: Date string in Vietnamese format

    Returns:
        datetime object or None if parsing fails
    """
    if not date_string:
        return None

    # Common Vietnamese date patterns
    patterns = [
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
        r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
        r'(\d{4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
    ]

    for pattern in patterns:
        match = re.search(pattern, date_string)
        if match:
            try:
                groups = match.groups()
                if len(groups[0]) == 4:  # YYYY first
                    year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                else:  # DD first
                    day, month, year = int(groups[0]), int(groups[1]), int(groups[2])

                return datetime(year, month, day)
            except ValueError:
                continue

    return None


def format_timestamp(dt: datetime = None) -> str:
    """
    Format timestamp in ISO 8601 format

    Args:
        dt: datetime object (uses current time if None)

    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()

    return dt.isoformat()


def create_slug(text: str, max_length: int = 50) -> str:
    """
    Create URL-friendly slug from text

    Args:
        text: Text to convert to slug
        max_length: Maximum slug length

    Returns:
        Slug string
    """
    # Convert to lowercase
    slug = text.lower()

    # Replace Vietnamese characters with ASCII equivalents
    vietnamese_map = {
        'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ắ': 'a', 'ằ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ấ': 'a', 'ầ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ế': 'e', 'ề': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ố': 'o', 'ồ': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ớ': 'o', 'ờ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ứ': 'u', 'ừ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        'đ': 'd'
    }

    for viet, ascii_char in vietnamese_map.items():
        slug = slug.replace(viet, ascii_char)

    # Replace non-alphanumeric with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    # Truncate to max length
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit('-', 1)[0]

    return slug


def get_file_extension(url: str) -> str:
    """
    Get file extension from URL

    Args:
        url: URL to parse

    Returns:
        File extension (without dot)
    """
    parsed = urlparse(url)
    path = parsed.path
    ext = Path(path).suffix.lstrip('.')

    # Handle query parameters
    if '?' in ext:
        ext = ext.split('?')[0]

    return ext.lower()


def estimate_media_type(url: str) -> str:
    """
    Estimate media type from URL

    Args:
        url: Media URL

    Returns:
        Media type ('image', 'audio', 'video', or 'unknown')
    """
    ext = get_file_extension(url)

    image_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico'}
    audio_exts = {'mp3', 'wav', 'ogg', 'm4a', 'aac', 'flac'}
    video_exts = {'mp4', 'webm', 'avi', 'mov', 'flv', 'mkv', 'wmv'}

    if ext in image_exts:
        return 'image'
    elif ext in audio_exts:
        return 'audio'
    elif ext in video_exts:
        return 'video'
    else:
        return 'unknown'


def calculate_delay(min_delay: float, max_delay: float) -> float:
    """
    Calculate random delay for rate limiting

    Args:
        min_delay: Minimum delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Random delay between min and max
    """
    return random.uniform(min_delay, max_delay)


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to maximum length

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to append if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two dictionaries, with dict2 values taking precedence

    Args:
        dict1: First dictionary
        dict2: Second dictionary

    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    result.update(dict2)
    return result


def safe_get(dictionary: Dict, *keys, default=None) -> Any:
    """
    Safely get nested dictionary value

    Args:
        dictionary: Dictionary to search
        *keys: Chain of keys to follow
        default: Default value if key not found

    Returns:
        Value or default
    """
    current = dictionary
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return default
        else:
            return default
    return current if current is not None else default
