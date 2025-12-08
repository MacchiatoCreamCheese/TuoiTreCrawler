# TuoiTre.vn Web Crawler

A Python web crawler for extracting articles, comments, and media from tuoitre.vn (Vietnamese news website).

## Features

- Extract 100+ posts from multiple categories
- Scrape comprehensive post metadata (title, author, date, etc.)
- Extract article content with proper Vietnamese text encoding
- Scrape comments with nested replies and vote reactions
- Download all media (images, audio, video) with organized folder structure
- Save data as JSON files with graceful degradation for missing data
- Respect rate limits with configurable delays and user agent rotation
- Robust error handling and logging

## Media Downloader

The `MediaDownloader` class provides comprehensive media downloading functionality:

### Features
- **Image Downloads**: Extracts and downloads all images from posts to organized folders
- **Audio Downloads**: Downloads podcast/audio files when available
- **Progress Tracking**: Shows download progress for large files (>100KB)
- **File Validation**: Validates file size and integrity after download
- **Statistics Tracking**: Monitors download success/failure rates and total bytes
- **Automatic Cleanup**: Removes partial downloads on failure
- **Organized Storage**: Saves media in structured directories by post ID

### Usage

```python
from crawler.scraper import TuoiTreScraper
from crawler.downloader import MediaDownloader

scraper = TuoiTreScraper()
downloader = MediaDownloader(scraper)

# Download all images from a post
soup = scraper.get_html("https://tuoitre.vn/some-article-123456.htm")
success = downloader.download_images(scraper, "123456", soup)

# Download audio if available
audio_success = downloader.download_audio(scraper, "123456", soup)

# Download all media types
all_success = downloader.download_all_media(scraper, "123456", soup)

# Get download statistics
stats = downloader.get_statistics()
print(f"Images downloaded: {stats['images_downloaded']}")
print(f"Total bytes: {stats['total_bytes_formatted']}")

scraper.close()
```

### Storage Structure

Media files are organized in the following structure:
```
data/media/
├── images/
│   ├── 123456/
│   │   ├── image1.jpg
│   │   ├── image2.png
│   │   └── image3.jpeg
│   └── 789012/
│       └── image1.jpg
└── audio/
    ├── 123456/
    │   └── podcast.mp3
    └── 789012/
        └── audio-file.mp3
```

### Configuration Options

- **Base Directory**: Configurable via `config.MEDIA_DIR` (default: `./data/media`)
- **File Organization**: Organized by post ID for easy reference
- **Progress Display**: Shows progress for files >100KB
- **Validation**: Automatic file size validation after download

## Recent Updates

### Code Cleanup (December 2025)
- **Documentation**: Consolidated all separate documentation files into this comprehensive README
- **Tests**: Cleaned up and organized test files for better maintainability
- **URL Validation**: Streamlined URL validation system while maintaining robust filtering

## Project Structure

```
TuoiTreCrawler/
├── config.py                 # Configuration settings
├── main.py                   # Main entry point with CLI
├── requirements.txt          # Python dependencies
├── crawler/                  # Main crawler package
│   ├── __init__.py
│   ├── scraper.py            # Article and category scraping
│   ├── parser.py             # Comment extraction and parsing
│   ├── downloader.py         # Media downloading
│   ├── json_exporter.py      # JSON export functionality
│   └── utils/               # Utility modules
│       ├── __init__.py
│       ├── exceptions.py    # Custom exceptions
│       ├── error_handler.py # Error handling utilities
│       ├── logger.py        # Logging utilities
│       └── helpers.py       # General helper functions
├── data/                    # Output directory
│   └── media/              # Downloaded media files
├── logs/                   # Log files
│   └── crawler.log
└── test_*.py               # Test scripts
```

## Architecture & Workflow

### Overall Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         main.py                             │
│                  (Entry Point & Orchestration)              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ├──► 1. Parse CLI arguments
                  ├──► 2. Setup logging & directories
                  ├──► 3. Initialize components
                  └──► 4. Run crawl_posts() workflow
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   ┌─────────┐    ┌─────────┐    ┌──────────┐
   │ Scraper │    │ Parser  │    │Downloader│
   └─────────┘    └─────────┘    └──────────┘
        │              │               │
        └──────────────┴───────────────┘
                       │
                       ▼
               ┌──────────────┐
               │ JSON Exporter│
               └──────────────┘
                       │
                       ▼
                  Output Files
```

### Component Descriptions

#### 1. **config.py** - Configuration Hub
Central configuration for all crawler settings including:
- Category URLs to crawl (thoi-su, phap-luat, nhip-song-tre)
- Rate limiting (1-2 second delays between requests)
- Media download settings
- Error handling behavior (graceful degradation)
- Directory paths for data storage

#### 2. **scraper.py** - TuoiTreScraper Class
Handles all HTTP requests to TuoiTre.vn with intelligent features:
- **Rate Limiting**: Enforces delays between requests to respect server
- **User-Agent Rotation**: Cycles through multiple user agents to appear as different browsers
- **Retry Logic**: Automatically retries failed requests up to 3 times
- **Error Handling**: Gracefully handles timeouts, connection errors, and rate limits

**Key Functions:**
- `get_category_post_urls()`: Crawls category pages to collect post URLs
- `scrape_post_details()`: Extracts post metadata (title, author, content, etc.)
- `extract_vote_reactions()`: Extracts article reactions (likes, loves, etc.)
- `_is_valid_article_url()`: Validates URLs using pattern matching and filtering

#### 3. **parser.py** - Comment Extraction
Extracts comments using the TuoiTre.vn Comment API (not HTML parsing):

**Why API instead of HTML?**
Comments are loaded dynamically via JavaScript after page load, so they're not visible in the initial HTML that BeautifulSoup receives. The crawler directly calls the comment API endpoint.

**API Endpoint:**
```
https://id.tuoitre.vn/api/getlist-comment.api
?objId={post_id}&objType=1&pageindex={page}&pagesize=100
```

**Process:**
1. Extract post ID from URL
2. Make paginated API requests to fetch all comments
3. Parse double-nested JSON (API returns JSON string in Data field)
4. Build comment tree structure with parent-child relationships
5. Return hierarchical comment data with nested replies

**Comment Structure:**
```python
{
    'commentId': 'uuid',
    'author': 'User Name',
    'text': 'Comment text',
    'date': '2025-12-08',
    'vote_react_list': {'like': 5, 'love': 2},
    'replies': [nested_comments],
    'depth': 0
}
```

#### 4. **downloader.py** - Media Downloads
Downloads images and audio files from posts:

**Audio Extraction Challenge:**
Audio elements are created dynamically by JavaScript using the embedTTS library. The `<audio>` tag doesn't exist in initial HTML.

**Solution - URL Construction:**
The crawler parses the `embedTTS.init()` script configuration to construct the audio URL:

1. Find `<script>` containing `embedTTS.init`
2. Extract parameters:
   - `newsId`: Post ID (e.g., 20251208151651761)
   - `distributionDate`: Publication date (e.g., 2025/12/08)
   - `nameSpace`: Site namespace ('tuoitre')
   - `defaultVoice`: Voice variant (resolves `_voice` variable to 'nu-1' or 'nu')
   - `ext`: File extension ('m4a')
3. Construct URL pattern:
   ```
   https://tts.mediacdn.vn/{date}/{namespace}-{voice}-{newsId}.m4a
   ```

**Example:**
```
https://tts.mediacdn.vn/2025/12/08/tuoitre-nu-1-20251208151651761.m4a
```

**Features:**
- Progress tracking for large downloads
- File validation after download
- Organized storage by post ID
- Automatic retry on failure

#### 5. **json_exporter.py** - JSON Output
Saves scraped data as structured JSON files:

**Features:**
- UTF-8 encoding for Vietnamese characters
- Data validation before saving
- Crawl metadata (timestamp, version)
- Individual files per post + combined output file

**Final JSON Structure:**
```json
{
    "postId": "20251208151651761",
    "title": "Article title",
    "content": "Full article text...",
    "author": "Author name",
    "publishDate": "2025-12-08",
    "category": "thoi-su",
    "url": "https://tuoitre.vn/...",
    "description": "Article summary",
    "tags": ["tag1", "tag2"],
    "audioUrl": "https://tts.mediacdn.vn/.../file.m4a",
    "voteReactions": {"like": 10, "love": 5},
    "comments": [
        {
            "commentId": "uuid",
            "author": "User",
            "text": "Comment text",
            "vote_react_list": {"like": 2},
            "replies": [nested_comments]
        }
    ],
    "mediaPaths": {
        "images": ["data/media/123/images/img1.jpg"],
        "audio": "data/media/123/audio/file.m4a"
    },
    "commentCount": 45
}
```

### Complete Workflow

#### Phase 1: Initialization
```
main()
  → parse_arguments()        # Parse CLI flags (--count, --delay-min, etc.)
  → setup_logging()          # Configure console + file logging
  → create_directories()     # Create data/, logs/ folders
  → print_configuration()    # Show settings summary
```

#### Phase 2: URL Collection
```
crawl_posts() → STEP 1: Collect Post URLs

For each category URL:
  1. Fetch category page HTML
  2. Find all <a> tags with article links
  3. Extract and normalize URLs
  4. Validate with _is_valid_article_url():
     ├─► Check: config.is_url_allowed() (no disallowed paths)
     ├─► Check: 'tuoitre.vn' in URL
     ├─► Check: Has numeric ID pattern (-\d{6,}\.htm)
     └─► Exclude: tag pages, category pages, pagination
  5. Collect up to max_posts URLs per category

Result: List of ~105 post URLs (35 × 3 categories)
```

#### Phase 3: Post Scraping (Main Loop)
```
For each post URL:

  ├─► Step 1: Scrape Post Details
  │   ├─► Fetch post HTML
  │   ├─► Extract: title, author, date, content, tags
  │   └─► Return post_details dict
  │
  ├─► Step 2: Extract Comments via API
  │   ├─► Extract post_id from URL
  │   ├─► Call Comment API with pagination
  │   │   └─► Parse double-nested JSON
  │   ├─► Build comment tree (parent-child relationships)
  │   └─► Return hierarchical comment structure
  │
  ├─► Step 3: Extract Vote Reactions
  │   ├─► Find reaction elements in HTML
  │   └─► Return {'like': 10, 'love': 5, ...}
  │
  ├─► Step 4: Download Media
  │   ├─► Download Images:
  │   │   ├─► Find all <img> tags
  │   │   └─► Save to data/media/{post_id}/images/
  │   │
  │   └─► Download Audio:
  │       ├─► Parse embedTTS.init script
  │       ├─► Construct audio URL
  │       └─► Save to data/media/{post_id}/audio/
  │
  ├─► Step 5: Format & Save
  │   ├─► Combine all data into structured dict
  │   ├─► Validate required fields
  │   └─► Save as {postId}.json with UTF-8
  │
  └─► Step 6: Update Statistics
      ├─► Total posts scraped
      ├─► Total comments
      ├─► Posts with 20+ comments
      └─► Media download counts
```

#### Phase 4: Completion
```
print_summary()
  → Display statistics:
    ├─► Posts scraped/failed
    ├─► Comment counts
    ├─► Media download counts
    ├─► Performance metrics
    └─► Requirement validation (20+ comments)
```

### Data Flow Diagram

```
User runs: python main.py --count 35

                    main.py
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   Parse Args    Setup Logging    Create Dirs
        │              │              │
        └──────────────┼──────────────┘
                       │
              crawl_posts() starts
                       │
         ┌─────────────┴─────────────┐
         │                           │
    STEP 1: Collect URLs        STEP 2: Scrape Posts
         │                           │
   ┌─────▼─────┐              ┌─────▼─────┐
   │ Category  │              │  For each │
   │  Pages    │              │  post URL │
   └─────┬─────┘              └─────┬─────┘
         │                           │
   List of URLs              ┌───────┼───────┐
         │                   │       │       │
         │              Scrape  Comments  Media
         │              Details    API    Download
         │                   │       │       │
         │                   └───────┼───────┘
         │                           │
         │                     Format Data
         │                           │
         │                      Save JSON
         │                           │
         └───────────────────────────┘
                       │
                  Statistics
                       │
                Print Summary
```

### Key Design Decisions

#### 1. API vs HTML Parsing for Comments
**Decision:** Use API instead of HTML parsing
**Reason:** Comments load dynamically via JavaScript, not visible in initial HTML
**Implementation:** Direct calls to `id.tuoitre.vn/api/getlist-comment.api`

#### 2. Audio URL Construction
**Decision:** Parse embedTTS script instead of waiting for JS execution
**Reason:** Audio element doesn't exist in initial HTML, created by JavaScript
**Implementation:** Extract parameters from `embedTTS.init()` call and construct URL manually

#### 3. Rate Limiting
**Decision:** 1-2 second delays between requests
**Reason:** Be respectful to TuoiTre.vn servers, avoid rate limiting
**Implementation:** `_apply_rate_limit()` with random delays

#### 4. Error Handling
**Decision:** Graceful degradation with `SKIP_ON_ERROR=True`
**Reason:** Continue crawling even if individual posts fail
**Implementation:** Try-except blocks with logging, optional strict mode

#### 5. User Agent Rotation
**Decision:** Rotate through multiple user agents
**Reason:** Appear as different browsers, reduce bot detection
**Implementation:** `_get_next_user_agent()` cycles through list

### Validation & Quality Checks

Throughout the process, the crawler validates:

1. **URL Validation** (`_is_valid_article_url`)
   - Must be from tuoitre.vn
   - Must have numeric ID
   - Not in disallowed paths

2. **Post Data Validation** (`validate_post_data`)
   - Required fields present: postId, title, content, url
   - Valid data types
   - Non-empty content

3. **Comment Count** (`validate_comment_count`)
   - Checks if post has ≥20 comments
   - Counts nested replies recursively

4. **Media Download** (in `MediaDownloader`)
   - Verifies file size > 0
   - Checks HTTP status codes
   - Validates file extensions

### Output Structure

```
TuoiTreCrawler/
├── data/
│   ├── tuoitre_posts_20251208_210000.json  # Combined output
│   ├── 20251208151651761.json              # Individual post
│   ├── 20251208152345678.json
│   └── media/
│       ├── 20251208151651761/
│       │   ├── images/
│       │   │   ├── img_0.jpg
│       │   │   └── img_1.jpg
│       │   └── audio/
│       │       └── audio.m4a
│       └── 20251208152345678/
│           └── ...
└── logs/
    └── crawler.log
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd TuoiTreCrawler
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.py` to customize:

- **Category URLs**: 3 default categories from tuoitre.vn
  - `thoi-su` (Current Affairs)
  - `the-gioi` (World News)
  - `kinh-doanh` (Business)
- **Crawling settings**: Posts per category, delays, timeouts
- **User agents**: List of user agents for rotation
- **Media settings**: Enable/disable specific media types
- **Paths**: Data and log directories
- **Logging**: Log level, format, rotation settings

## Usage

### Basic Usage

Run with default settings (crawls 3 categories, ~35 posts each):
```bash
python main.py
```

### Custom Category URLs

Crawl specific categories:
```bash
python main.py --urls https://tuoitre.vn/thoi-su.htm
```

Multiple categories:
```bash
python main.py --urls https://tuoitre.vn/thoi-su.htm https://tuoitre.vn/the-gioi.htm
```

### Custom Post Count

Crawl 50 posts per category:
```bash
python main.py --count 50
```

### Rate Limiting

Adjust request delays (in seconds):
```bash
python main.py --delay-min 3 --delay-max 6
```

### Media Downloads

Disable all media downloads:
```bash
python main.py --no-media
```

Download only images:
```bash
python main.py --images-only
```

### Logging

Enable debug logging:
```bash
python main.py --log-level DEBUG
```

Custom log file:
```bash
python main.py --log-file /path/to/custom.log
```

### Error Handling

Strict mode (fail on first error):
```bash
python main.py --strict
```

Custom retry attempts:
```bash
python main.py --max-retries 5
```

### Dry Run

Print configuration without crawling:
```bash
python main.py --dry-run
```

### Combined Example

```bash
python main.py \
  --urls https://tuoitre.vn/thoi-su.htm https://tuoitre.vn/kinh-doanh.htm \
  --count 40 \
  --delay-min 2 \
  --delay-max 4 \
  --log-level INFO \
  --max-retries 3
```

## Output Format

### JSON Structure

Each post is saved as a JSON file with the following structure:

```json
{
  "id": "unique_post_id",
  "url": "https://tuoitre.vn/...",
  "metadata": {
    "title": "Article title",
    "author": "Author name",
    "publish_date": "2024-01-01T12:00:00",
    "category": "thoi-su",
    "tags": ["tag1", "tag2"]
  },
  "content": {
    "text": "Article content...",
    "html": "<p>Article content...</p>"
  },
  "comments": [
    {
      "id": "comment_id",
      "author": "Commenter name",
      "text": "Comment text",
      "timestamp": "2024-01-01T13:00:00",
      "votes": {
        "up": 10,
        "down": 2
      },
      "replies": [...]
    }
  ],
  "media": {
    "images": ["path/to/image1.jpg", ...],
    "audio": ["path/to/audio1.mp3", ...],
    "video": ["path/to/video1.mp4", ...]
  },
  "crawl_metadata": {
    "timestamp": "2024-01-01T14:00:00",
    "crawler_version": "1.0.0"
  }
}
```

## Vietnamese Text Encoding

The crawler properly handles Vietnamese text encoding:
- Default encoding: UTF-8
- Fallback encodings: latin-1, cp1252
- Unicode normalization for Vietnamese characters
- Proper handling of diacritics (á, à, ả, ã, ạ, ă, â, etc.)

## Error Handling

The crawler implements graceful degradation:
- Continues crawling even if individual posts fail
- Saves partial data when some fields are missing
- Retries failed requests with exponential backoff
- Comprehensive error logging
- Error aggregation and reporting

## Rate Limiting

To be respectful to tuoitre.vn servers:
- Configurable delays between requests (default: 2-5 seconds)
- User agent rotation
- Request timeout: 30 seconds
- Maximum retries: 3

## Development

### Adding New Utilities

Add new utility modules in `crawler/utils/`:
```python
# crawler/utils/my_module.py
from .logger import create_module_logger

logger = create_module_logger('MyModule')

def my_function():
    logger.info("My function called")
    # Implementation
```

### Custom Exceptions

Use custom exceptions from `crawler/utils/exceptions.py`:
```python
from crawler.utils.exceptions import ParseError, NetworkError

raise ParseError("Failed to parse element", url=url, element="title")
```

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- lxml
- fake-useragent
- pyyaml

See `requirements.txt` for full dependency list with versions.

## Troubleshooting

### Installation Issues

If you encounter SSL certificate errors:
```bash
pip install --upgrade certifi
```

### Encoding Issues

If Vietnamese characters appear garbled:
- Ensure your terminal supports UTF-8
- Check that output files are opened with UTF-8 encoding

### Rate Limiting

If you're getting blocked:
- Increase delay settings: `--delay-min 5 --delay-max 10`
- Reduce concurrent requests in `config.py`
- Check `RESPECT_ROBOTS_TXT` setting

## License

This project is for educational purposes only. Please respect tuoitre.vn's terms of service and robots.txt.

## Project Status

The crawler is now feature-complete with all core components implemented:

- ✅ **Scraper Module**: Complete article and category scraping with rate limiting
- ✅ **Parser Module**: Full comment extraction with nested replies and vote reactions
- ✅ **Media Downloader**: Comprehensive image and audio downloading with progress tracking
- ✅ **JSON Exporter**: Structured data export with validation
- ✅ **Error Handling**: Robust error handling and logging throughout
- ✅ **Testing**: Comprehensive test suite for all components
- ✅ **Documentation**: Consolidated documentation in this README

## Development

The codebase is now production-ready and well-documented. All major features have been implemented and tested.