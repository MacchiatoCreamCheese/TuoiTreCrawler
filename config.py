"""
Configuration file for TuoiTre.vn web crawler
Contains category URLs, delay settings, user agent rotation, and other crawler settings
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

# Category URLs to crawl from tuoitre.vn
CATEGORY_URLS = {
    'thoi-su': 'https://tuoitre.vn/thoi-su.htm',  # Current Affairs
    'the-gioi': 'https://tuoitre.vn/the-gioi.htm',  # World News
    'kinh-doanh': 'https://tuoitre.vn/kinh-doanh.htm',  # Business
}

# URL filtering - paths to exclude from crawling
DISALLOWED_PATHS = [
    '/tim-kiem.htm',        # Search pages
    '/print/',              # Print versions
    '/ImageView.aspx',      # Image viewer pages
    '/ajax-box-mua-sam/',   # Shopping box AJAX pages
]

# Crawling settings
POSTS_PER_CATEGORY = 35  # Target at least 100+ posts total (35 * 3 = 105)
MIN_COMMENTS_REQUIRED = 20  # Minimum comments for at least one post
REQUEST_DELAY_MIN = 1  # Minimum delay between requests (seconds) - be respectful
REQUEST_DELAY_MAX = 2  # Maximum delay between requests (seconds) - be respectful
REQUEST_TIMEOUT = 30  # Request timeout in seconds
MAX_RETRIES = 3  # Maximum number of retries for failed requests

# User agent rotation list
USER_AGENTS = [
    'StudentCrawler/1.0 (Educational Project)',  # Primary User-Agent identifier
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
]

# Vietnamese encoding settings
DEFAULT_ENCODING = 'utf-8'
FALLBACK_ENCODINGS = ['utf-8', 'latin-1', 'cp1252']

# Data storage paths
DATA_DIR = BASE_DIR / 'data'
MEDIA_DIR = DATA_DIR / 'media'
LOGS_DIR = BASE_DIR / 'logs'
JSON_OUTPUT_DIR = DATA_DIR

# Media download settings
DOWNLOAD_IMAGES = True
DOWNLOAD_AUDIO = True
DOWNLOAD_VIDEO = True
MEDIA_TYPES = {
    'images': ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'],
    'audio': ['mp3', 'wav', 'ogg', 'm4a', 'aac'],
    'video': ['mp4', 'webm', 'avi', 'mov', 'flv']
}

# Media organization
ORGANIZE_MEDIA_BY_POST = True  # Create separate folders for each post's media
MAX_FILENAME_LENGTH = 255  # Maximum filename length for file system compatibility

# Logging settings
LOG_LEVEL = 'INFO'  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_FILE = LOGS_DIR / 'crawler.log'
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# Error handling settings
SKIP_ON_ERROR = True  # Continue crawling even if one post fails
SAVE_PARTIAL_DATA = True  # Save data even if some fields are missing
GRACEFUL_DEGRADATION = True  # Don't fail if optional data is missing

# Rate limiting
RESPECT_ROBOTS_TXT = True
CONCURRENT_REQUESTS = 1  # Number of concurrent requests (keep low to be polite)

# Output settings
JSON_INDENT = 2  # Pretty print JSON with 2-space indentation
INCLUDE_METADATA = True  # Include crawl timestamp and other metadata in JSON

# Comment scraping settings
MAX_COMMENT_DEPTH = 10  # Maximum depth for nested replies
LOAD_ALL_COMMENTS = True  # Attempt to load all comments including paginated ones

# Create necessary directories
def create_directories():
    """Create all necessary directories for the crawler"""
    directories = [DATA_DIR, MEDIA_DIR, LOGS_DIR, JSON_OUTPUT_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    # Create subdirectories for media types if organizing by type
    if not ORGANIZE_MEDIA_BY_POST:
        for media_type in MEDIA_TYPES.keys():
            (MEDIA_DIR / media_type).mkdir(parents=True, exist_ok=True)


def is_url_allowed(url: str) -> bool:
    """
    Validate URL against disallowed paths

    Args:
        url: URL to validate

    Returns:
        True if URL is allowed, False if it matches any disallowed path
    """
    if not url:
        return False

    # Check against disallowed paths
    for disallowed_path in DISALLOWED_PATHS:
        if disallowed_path in url:
            return False

    return True


if __name__ == '__main__':
    create_directories()
    print("Configuration loaded successfully")
    print(f"Base directory: {BASE_DIR}")
    print(f"Categories to crawl: {len(CATEGORY_URLS)}")
    print(f"Target posts per category: {POSTS_PER_CATEGORY}")
    print(f"Total expected posts: {len(CATEGORY_URLS) * POSTS_PER_CATEGORY}")
