## TuoiTre Media Downloader Documentation

## Overview

The `crawler/downloader.py` module provides comprehensive media downloading functionality for TuoiTre.vn, including:

- Download all images from posts with organized storage
- Download audio/podcast files when available
- Progress tracking for large downloads
- File validation (size checks)
- Graceful error handling
- Automatic retry with network errors
- Statistics tracking

---

## Core Components

### MediaDownloader Class

Main class for handling file downloads with progress tracking and validation.

**Initialization:**
```python
from crawler.downloader import MediaDownloader

downloader = MediaDownloader(scraper, base_dir=Path('./media'))
```

**Parameters:**
- `scraper`: TuoiTreScraper instance
- `base_dir`: Base directory for downloads (optional, defaults to `config.MEDIA_DIR`)

**Features:**
- ✅ Streaming downloads with chunked reading
- ✅ Progress indicators for large files (>100KB)
- ✅ File validation (size > 0)
- ✅ Automatic cleanup on failed downloads
- ✅ Download statistics tracking
- ✅ Human-readable size formatting

---

## Functions

### 1. download_images()

Downloads all images from a post to `./images/<postId>/` with original filenames.

**Signature:**
```python
def download_images(
    scraper,
    post_id: str,
    soup: BeautifulSoup = None,
    post_url: str = None,
    save_dir: Path = None
) -> List[str]
```

**Parameters:**
- `scraper`: TuoiTreScraper instance
- `post_id`: Post ID for organizing downloads
- `soup`: BeautifulSoup object (optional, will fetch if not provided)
- `post_url`: Post URL (required if soup is None)
- `save_dir`: Custom save directory (defaults to `./images/<postId>/`)

**Returns:**
- List of paths to successfully downloaded images

**Directory Structure:**
```
./images/
└── <postId>/
    ├── img_1_original-filename.jpg
    ├── img_2_another-image.png
    ├── img_3_photo.webp
    └── ...
```

**Example:**
```python
from crawler.scraper import TuoiTreScraper
from crawler.downloader import download_images

scraper = TuoiTreScraper()
post_id = "123456"
post_url = "https://tuoitre.vn/article-123456.htm"

# Download all images
image_paths = download_images(scraper, post_id, post_url=post_url)

print(f"Downloaded {len(image_paths)} images:")
for path in image_paths:
    print(f"  - {path}")

scraper.close()
```

**Features:**
- ✅ Extracts images from post content
- ✅ Preserves original filenames
- ✅ Adds numeric prefix (img_1_, img_2_, etc.)
- ✅ Filters out tracking pixels, icons (< 50x50)
- ✅ Skips already downloaded images
- ✅ Validates all downloads (size > 0)
- ✅ Logs progress and statistics

**Extraction Logic:**
1. Finds main content container
2. Extracts `<img>` tags
3. Checks src, data-src, data-original attributes
4. Also extracts `<picture>` and `<source>` elements
5. Filters out invalid/tracking images
6. Removes duplicates

---

### 2. download_audio()

Downloads audio/podcast from a post (if available) to `./audio/<postId>.<extension>`.

**Signature:**
```python
def download_audio(
    scraper,
    post_id: str,
    soup: BeautifulSoup = None,
    post_url: str = None,
    save_dir: Path = None
) -> Optional[str]
```

**Parameters:**
- `scraper`: TuoiTreScraper instance
- `post_id`: Post ID for filename
- `soup`: BeautifulSoup object (optional)
- `post_url`: Post URL (required if soup is None)
- `save_dir`: Custom save directory (defaults to `./audio/`)

**Returns:**
- Path to downloaded audio file, or None if no audio found

**File Naming:**
```
./audio/<postId>.<extension>

Examples:
  ./audio/123456.mp3
  ./audio/789012.m4a
  ./audio/345678.wav
```

**Example:**
```python
from crawler.downloader import download_audio

scraper = TuoiTreScraper()
post_id = "123456"
post_url = "https://tuoitre.vn/article-123456.htm"

# Download audio if available
audio_path = download_audio(scraper, post_id, post_url=post_url)

if audio_path:
    print(f"✓ Downloaded audio: {audio_path}")
else:
    print("No audio found (normal)")

scraper.close()
```

**Features:**
- ✅ Detects `<audio>` tags
- ✅ Finds podcast player containers
- ✅ Extracts from data attributes
- ✅ Returns None if no audio found (graceful)
- ✅ Validates download
- ✅ Shows progress for large files

**Extraction Logic:**
1. Check `<audio>` tag with src attribute
2. Check `<source>` tags within audio
3. Look for podcast/audio player containers
4. Search for links to audio files (.mp3, .m4a, etc.)
5. Return first valid audio URL found

---

### 3. download_all_media()

Downloads all media (images + audio) from a post in one call.

**Signature:**
```python
def download_all_media(
    scraper,
    post_id: str,
    post_url: str,
    soup: BeautifulSoup = None,
    include_images: bool = True,
    include_audio: bool = True
) -> Dict[str, Any]
```

**Parameters:**
- `scraper`: TuoiTreScraper instance
- `post_id`: Post ID
- `post_url`: Post URL
- `soup`: BeautifulSoup object (optional)
- `include_images`: Whether to download images
- `include_audio`: Whether to download audio

**Returns:**
Dictionary with download results:
```python
{
    'post_id': '123456',
    'post_url': 'https://tuoitre.vn/...',
    'images': [
        './images/123456/img_1_photo.jpg',
        './images/123456/img_2_image.png',
        ...
    ],
    'audio': './audio/123456.mp3',  # or None
    'errors': []  # List of error messages
}
```

**Example:**
```python
from crawler.downloader import download_all_media

scraper = TuoiTreScraper()

results = download_all_media(
    scraper,
    post_id="123456",
    post_url="https://tuoitre.vn/article-123456.htm",
    include_images=True,
    include_audio=True
)

print(f"Downloaded {len(results['images'])} images")
if results['audio']:
    print(f"Downloaded audio: {results['audio']}")
if results['errors']:
    print(f"Errors: {results['errors']}")

scraper.close()
```

---

### 4. get_media_urls()

Extracts media URLs without downloading (for preview/planning).

**Signature:**
```python
def get_media_urls(
    soup: BeautifulSoup,
    post_url: str = None
) -> Dict[str, List[str]]
```

**Returns:**
```python
{
    'images': [
        'https://cdn.tuoitre.vn/image1.jpg',
        'https://cdn.tuoitre.vn/image2.png',
        ...
    ],
    'audio': [
        'https://cdn.tuoitre.vn/podcast.mp3'
    ]  # or empty list
}
```

**Example:**
```python
from crawler.downloader import get_media_urls

scraper = TuoiTreScraper()
soup = scraper.get_html(post_url)

# Get URLs without downloading
media_urls = get_media_urls(soup, post_url)

print(f"Found {len(media_urls['images'])} images")
print(f"Found {len(media_urls['audio'])} audio files")

scraper.close()
```

---

## Progress Indicators

### For Large Downloads (> 100KB)

The downloader automatically shows progress for files larger than 100KB:

```
Downloading img_1_large-photo.jpg (2.5MB)...
Progress: 25.0%
Progress: 50.0%
Progress: 75.0%
✓ Downloaded img_1_large-photo.jpg (2.5MB in 3.2s, 800.0KB/s)
```

### For Small Files

Small files download silently:
```
✓ Downloaded img_2_icon.png (5.2KB in 0.1s, 52.0KB/s)
```

### Progress Levels

**Debug Level:**
- Shows detailed progress updates
- Logs every 25% completion

**Info Level:**
- Shows start/end of downloads for large files
- Shows summary statistics

**Configuration:**
```python
# In config.py
LOG_LEVEL = 'INFO'  # or 'DEBUG' for more detail
```

---

## File Validation

### Validation Checks

All downloaded files are automatically validated:

1. **File Exists:** Check file was created
2. **Size > 0:** File is not empty
3. **Size Match:** Compare with expected size (within 1% tolerance)

**Validation Logic:**
```python
def _validate_download(file_path, expected_size):
    # Check exists
    if not file_path.exists():
        return False

    # Check size > 0
    file_size = file_path.stat().st_size
    if file_size == 0:
        return False

    # Check size match (allow 1% difference)
    if expected_size:
        size_diff = abs(file_size - expected_size)
        if size_diff > (expected_size * 0.01):
            # Log warning but don't fail
            pass

    return True
```

**Automatic Cleanup:**
- Failed downloads are automatically deleted
- Partial files are removed
- Only valid files remain

---

## Graceful Error Handling

### Missing Media

**No Images:**
```python
image_paths = download_images(scraper, post_id, post_url=url)
# Returns: []  (empty list)
# Logs: "No images found for post <id>"
```

**No Audio:**
```python
audio_path = download_audio(scraper, post_id, post_url=url)
# Returns: None
# Logs: "No audio found for post <id>"
```

### Download Failures

**With SKIP_ON_ERROR = True** (default):
```python
# config.py
SKIP_ON_ERROR = True

# Behavior:
# - Logs warning
# - Continues with next file
# - Returns partial results
```

**With SKIP_ON_ERROR = False:**
```python
# config.py
SKIP_ON_ERROR = False

# Behavior:
# - Raises MediaDownloadError
# - Stops processing
# - Returns error to caller
```

### Network Errors

Network errors are handled by the scraper's retry mechanism:
- Max 3 retry attempts (configurable)
- Exponential backoff
- Automatic cleanup on failure

---

## Statistics Tracking

The MediaDownloader tracks download statistics:

```python
downloader = MediaDownloader(scraper)

# ... perform downloads ...

stats = downloader.get_statistics()
print(stats)
```

**Output:**
```python
{
    'images_downloaded': 15,
    'images_failed': 2,
    'audio_downloaded': 1,
    'audio_failed': 0,
    'total_bytes': 5242880,
    'total_bytes_formatted': '5.0MB'
}
```

---

## Configuration

Relevant config settings:

```python
# config.py

# Enable/disable media downloads
DOWNLOAD_IMAGES = True
DOWNLOAD_AUDIO = True
DOWNLOAD_VIDEO = True  # Not yet implemented

# Media types and extensions
MEDIA_TYPES = {
    'images': ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'],
    'audio': ['mp3', 'wav', 'ogg', 'm4a', 'aac'],
    'video': ['mp4', 'webm', 'avi', 'mov', 'flv']
}

# File organization
ORGANIZE_MEDIA_BY_POST = True  # Separate folder per post
MAX_FILENAME_LENGTH = 255      # Maximum filename length

# Error handling
SKIP_ON_ERROR = True           # Continue on errors
GRACEFUL_DEGRADATION = True    # Don't fail on missing data

# Paths
MEDIA_DIR = BASE_DIR / 'data' / 'media'
```

---

## Directory Structure

### With ORGANIZE_MEDIA_BY_POST = True

```
./images/
├── 123456/
│   ├── img_1_photo.jpg
│   ├── img_2_image.png
│   └── img_3_graphic.webp
├── 789012/
│   ├── img_1_banner.jpg
│   └── img_2_chart.png
└── ...

./audio/
├── 123456.mp3
├── 789012.m4a
└── ...
```

### With ORGANIZE_MEDIA_BY_POST = False

```
./media/
├── images/
│   ├── img_1_photo.jpg
│   ├── img_2_image.png
│   └── ...
├── audio/
│   ├── 123456.mp3
│   ├── 789012.m4a
│   └── ...
└── ...
```

---

## Filename Generation

### Images

**Format:** `img_<number>_<original-filename>`

**Examples:**
```
img_1_hero-banner.jpg
img_2_infographic-2024.png
img_3_abc123.webp
```

**If no filename in URL:**
```
img_1_a1b2c3d4.jpg  # Hash of URL + extension
```

### Audio

**Format:** `<postId>.<extension>`

**Examples:**
```
123456.mp3
789012.m4a
345678.wav
```

---

## Complete Usage Example

```python
from crawler.scraper import TuoiTreScraper, get_category_post_urls, scrape_post_details
from crawler.downloader import download_all_media
from pathlib import Path

# Initialize
scraper = TuoiTreScraper()

try:
    # Get posts
    post_urls = get_category_post_urls(
        scraper,
        "https://tuoitre.vn/thoi-su.htm",
        max_posts=10
    )

    # Process each post
    for post_url in post_urls:
        # Get post details
        post_details = scrape_post_details(scraper, post_url)
        post_id = post_details['postId']

        print(f"\nProcessing: {post_details['title']}")

        # Download all media
        media_results = download_all_media(
            scraper,
            post_id,
            post_url,
            include_images=True,
            include_audio=True
        )

        # Report results
        print(f"  Images: {len(media_results['images'])}")
        if media_results['audio']:
            print(f"  Audio: ✓")
        if media_results['errors']:
            print(f"  Errors: {len(media_results['errors'])}")

        # Add to post data
        post_details['media'] = media_results

        # Save post data with media paths
        # ... save to JSON ...

finally:
    scraper.close()
```

---

## Testing

Run the test suite:
```bash
python3 test_downloader.py
```

**Tests Include:**
1. ✅ Media URL extraction
2. ✅ Image downloads
3. ✅ Audio downloads
4. ✅ All media downloads
5. ✅ Progress indicators
6. ✅ File validation

---

## Error Types

### MediaDownloadError

Raised when media download fails (if SKIP_ON_ERROR = False):

```python
from crawler.utils.exceptions import MediaDownloadError

try:
    download_images(scraper, post_id, post_url=url)
except MediaDownloadError as e:
    print(f"Download failed: {e}")
    print(f"Media URL: {e.media_url}")
    print(f"Media type: {e.media_type}")
```

---

## Best Practices

### 1. Reuse Soup Object
```python
# Efficient: Fetch once, use multiple times
soup = scraper.get_html(post_url)
images = download_images(scraper, post_id, soup=soup, post_url=post_url)
audio = download_audio(scraper, post_id, soup=soup, post_url=post_url)
```

### 2. Check for Existing Files
```python
# Files are automatically skipped if they exist
# Re-running is safe and efficient
```

### 3. Handle Missing Media Gracefully
```python
# Always check return values
images = download_images(scraper, post_id, post_url=url)
if not images:
    logger.info("No images available")

audio = download_audio(scraper, post_id, post_url=url)
if audio is None:
    logger.info("No audio available")
```

### 4. Monitor Statistics
```python
downloader = MediaDownloader(scraper)
# ... downloads ...
stats = downloader.get_statistics()
logger.info(f"Total downloaded: {stats['total_bytes_formatted']}")
```

---

## Summary

**Media Downloader Features:**
- ✅ Download images to `./images/<postId>/` with original filenames
- ✅ Download audio to `./audio/<postId>.<ext>`
- ✅ Progress indicators for large downloads (>100KB)
- ✅ File validation (size > 0)
- ✅ Graceful handling of missing media
- ✅ Automatic retry on network errors
- ✅ Statistics tracking
- ✅ Clean directory organization
- ✅ Comprehensive error handling
- ✅ Full logging support

Ready for production crawling!
