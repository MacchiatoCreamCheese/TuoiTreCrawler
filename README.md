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

## Project Structure

```
TuoiTreCrawler/
├── config.py                 # Configuration settings
├── main.py                   # Main entry point with CLI
├── requirements.txt          # Python dependencies
├── crawler/                  # Main crawler package
│   ├── __init__.py
│   └── utils/               # Utility modules
│       ├── __init__.py
│       ├── exceptions.py    # Custom exceptions
│       ├── error_handler.py # Error handling utilities
│       ├── logger.py        # Logging utilities
│       └── helpers.py       # General helper functions
├── data/                    # Output directory
│   └── media/              # Downloaded media files
└── logs/                   # Log files
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

## Next Steps

The project structure is now complete. Next implementation steps:
1. Implement the main crawler class
2. Implement post scraping logic
3. Implement comment scraping with nested replies
4. Implement media download functionality
5. Implement JSON export
6. Add tests