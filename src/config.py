"""
Configuration file for TuoiTre.vn web crawler
Contains category URLs, delay settings, user agent rotation, and other crawler settings
"""

from pathlib import Path

# Base directory (project root)
BASE_DIR = Path(__file__).parent.parent

# Category URLs to crawl from tuoitre.vn
CATEGORY_URLS = {
    'thoi-su': 'https://tuoitre.vn/thoi-su.htm',  # Current Affairs
    'phap-luat': 'https://tuoitre.vn/phap-luat.htm',  # Law
    'nhip-song-tre': 'https://tuoitre.vn/nhip-song-tre.htm',  # Youth Life
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

# Data storage paths (outside src/)
DATA_DIR = BASE_DIR / 'data'
METADATA_DIR = DATA_DIR / 'metadata'  # For JSON metadata files
JSON_OUTPUT_DIR = METADATA_DIR

# Media storage paths (flat at project root per requirements)
AUDIO_DIR = BASE_DIR / 'audio'        # For audio files (./audio/<postId>.<ext>)
IMAGES_DIR = BASE_DIR / 'images'      # For image files (./images/<postId>/...)

# Legacy compatibility (media dir kept for possible grouping)
MEDIA_DIR = DATA_DIR / 'media'

# Media download settings
DOWNLOAD_IMAGES = True
DOWNLOAD_AUDIO = True
MEDIA_TYPES = {
    'images': ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'],
    'audio': ['mp3', 'wav', 'ogg', 'm4a', 'aac'],
    'video': ['mp4', 'webm', 'avi', 'mov', 'flv']
}

# Media organization
MAX_FILENAME_LENGTH = 255  # Maximum filename length for file system compatibility

# Logging settings (console only)
LOG_LEVEL = 'INFO'  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Error handling settings
SKIP_ON_ERROR = True  # Continue crawling even if one post fails
SAVE_PARTIAL_DATA = True  # Save data even if some fields are missing
GRACEFUL_DEGRADATION = True  # Don't fail if optional data is missing

# Rate limiting (currently not used, but kept for future use)

# Output settings
JSON_INDENT = 2  # Pretty print JSON with 2-space indentation
INCLUDE_METADATA = True  # Include crawl timestamp and other metadata in JSON

# Comment scraping settings
MAX_COMMENT_DEPTH = 10  # Maximum depth for nested replies

# Create necessary directories
def create_directories():
    """Create all necessary directories for the crawler"""
    directories = [DATA_DIR, METADATA_DIR, AUDIO_DIR, IMAGES_DIR]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)



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
