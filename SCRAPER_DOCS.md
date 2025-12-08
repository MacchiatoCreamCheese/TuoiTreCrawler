# TuoiTre Scraper Module Documentation

## Overview

The `crawler/scraper.py` module provides comprehensive functionality for scraping TuoiTre.vn, including:

- Fetching post URLs from category pages with automatic pagination
- Scraping detailed post information (title, content, author, date, etc.)
- Extracting vote reactions/emotions
- Rate limiting with configurable delays
- User agent rotation
- Automatic retries on network errors (max 3 attempts)

## Core Components

### TuoiTreScraper Class

The main scraper class that handles HTTP requests with built-in rate limiting and user agent rotation.

```python
from crawler.scraper import TuoiTreScraper

# Initialize with default settings from config
scraper = TuoiTreScraper()

# Or customize settings
scraper = TuoiTreScraper(
    delay_min=2.0,      # Minimum delay between requests (seconds)
    delay_max=5.0,      # Maximum delay between requests (seconds)
    max_retries=3,      # Maximum retry attempts
    timeout=30          # Request timeout (seconds)
)
```

#### Key Features

**Rate Limiting**
- Automatically enforces delays between requests
- Uses random delays within min/max range
- Configured via `delay_min` and `delay_max` parameters

**User Agent Rotation**
- Rotates through 6 different user agents
- Automatically applied to each request
- Helps avoid detection/blocking

**Error Handling**
- Automatic retries on network errors (with exponential backoff)
- Handles timeouts, connection errors, and HTTP errors
- Raises custom `NetworkError` exceptions

**Usage Example:**
```python
# Make a simple request
soup = scraper.get_html("https://tuoitre.vn/thoi-su.htm")

# Close session when done
scraper.close()
```

---

## Functions

### 1. get_category_post_urls()

Fetches all post URLs from a category page, handling pagination automatically.

**Signature:**
```python
def get_category_post_urls(
    scraper: TuoiTreScraper,
    category_url: str,
    max_posts: int = 35,
    max_pages: int = 10
) -> List[str]
```

**Parameters:**
- `scraper`: TuoiTreScraper instance
- `category_url`: Category page URL (e.g., "https://tuoitre.vn/thoi-su.htm")
- `max_posts`: Maximum number of post URLs to collect (default: 35)
- `max_pages`: Maximum number of pages to crawl (default: 10)

**Returns:**
- List of post URLs (strings)

**How it works:**
1. Fetches the category page
2. Extracts all article URLs from the page
3. Validates URLs (must be valid article URLs with numeric IDs)
4. Continues to next page (pagination format: `category-p2.htm`)
5. Stops when `max_posts` reached or no more pages found

**Pagination Handling:**
- Page 1: `https://tuoitre.vn/thoi-su.htm`
- Page 2: `https://tuoitre.vn/thoi-su-p2.htm`
- Page 3: `https://tuoitre.vn/thoi-su-p3.htm`
- etc.

**URL Validation:**
- Must be from `tuoitre.vn` domain
- Must contain numeric article ID (format: `-123456.htm`)
- Excludes category pages, tag pages, video pages, etc.

**Example:**
```python
scraper = TuoiTreScraper()

# Get 50 posts from "thoi-su" (current affairs) category
post_urls = get_category_post_urls(
    scraper,
    "https://tuoitre.vn/thoi-su.htm",
    max_posts=50,
    max_pages=5
)

print(f"Found {len(post_urls)} post URLs")
for url in post_urls:
    print(url)

scraper.close()
```

---

### 2. scrape_post_details()

Scrapes comprehensive details from a single post.

**Signature:**
```python
def scrape_post_details(
    scraper: TuoiTreScraper,
    post_url: str
) -> Optional[Dict[str, Any]]
```

**Parameters:**
- `scraper`: TuoiTreScraper instance
- `post_url`: URL of the post to scrape

**Returns:**
Dictionary with post details, or `None` if scraping fails (when `SKIP_ON_ERROR=True`)

**Post Details Structure:**
```python
{
    'postId': '123456',                    # Extracted from URL
    'url': 'https://tuoitre.vn/...',      # Post URL
    'title': 'Article title',              # Post title
    'author': 'Author name',               # Author (may be None)
    'publishDate': '2024-01-01T12:00:00', # ISO format date (may be None)
    'category': 'thoi-su',                 # Category slug
    'description': 'Article summary',      # Summary/sapo (may be None)
    'content': {
        'text': 'Plain text content...',   # Text-only content
        'html': '<div>HTML content...</div>' # HTML content
    },
    'tags': ['tag1', 'tag2'],             # List of tags
    'scrapedAt': '2024-01-01T14:00:00'    # Timestamp of scraping
}
```

**Extraction Details:**

**postId**: Extracted from URL pattern `-(\d+).htm`

**title**: Tries multiple selectors:
- `<h1 class="article-title">` or similar
- `<meta property="og:title">`

**author**: Tries multiple selectors:
- `<div class="author">` or similar
- `<meta name="author">`
- Cleans prefixes like "Tác giả:", "Theo:", "By:"

**publishDate**: Tries multiple sources:
- `<time datetime="...">` attribute
- `<meta property="article:published_time">`
- Text parsing for Vietnamese date formats
- Returns ISO 8601 format

**category**: Extracted from:
- Breadcrumb navigation
- URL path (first segment)

**description**: Tries multiple selectors:
- `<h2 class="sapo">` (Vietnamese for summary)
- `<meta property="og:description">`

**content**: Extracts from:
- `<div class="detail-content">` or similar
- Returns both plain text and HTML versions
- Removes `<script>`, `<style>`, `<iframe>` tags

**tags**: Extracted from tags container with links

**Example:**
```python
scraper = TuoiTreScraper()

post_details = scrape_post_details(
    scraper,
    "https://tuoitre.vn/some-article-123456.htm"
)

if post_details:
    print(f"Title: {post_details['title']}")
    print(f"Author: {post_details['author']}")
    print(f"Date: {post_details['publishDate']}")
    print(f"Content length: {len(post_details['content']['text'])} chars")

scraper.close()
```

---

### 3. extract_vote_reactions()

Extracts vote reactions/emotions from a post (likes, loves, etc.).

**Signature:**
```python
def extract_vote_reactions(
    scraper: TuoiTreScraper,
    post_url: str,
    soup: BeautifulSoup = None
) -> Dict[str, int]
```

**Parameters:**
- `scraper`: TuoiTreScraper instance
- `post_url`: URL of the post
- `soup`: Optional BeautifulSoup object (if already fetched)

**Returns:**
Dictionary with reaction types and counts

**Reaction Structure:**
```python
{
    'like': 10,
    'love': 5,
    'haha': 3,
    'wow': 2,
    'sad': 1,
    'angry': 0
}
```

**How it works:**
1. Tries to find reaction container elements
2. Extracts individual reaction counts
3. Identifies reaction types from CSS classes or attributes
4. Falls back to data attributes if no container found
5. Returns empty dict if no reactions found

**Example:**
```python
scraper = TuoiTreScraper()

reactions = extract_vote_reactions(
    scraper,
    "https://tuoitre.vn/some-article-123456.htm"
)

if reactions:
    print("Reactions found:")
    for reaction_type, count in reactions.items():
        print(f"  {reaction_type}: {count}")
else:
    print("No reactions found")

scraper.close()
```

---

## Complete Usage Example

```python
from crawler.scraper import (
    TuoiTreScraper,
    get_category_post_urls,
    scrape_post_details,
    extract_vote_reactions
)

# Initialize scraper
scraper = TuoiTreScraper(
    delay_min=2.0,
    delay_max=5.0,
    max_retries=3
)

try:
    # Step 1: Get post URLs from category
    category_url = "https://tuoitre.vn/thoi-su.htm"
    post_urls = get_category_post_urls(
        scraper,
        category_url,
        max_posts=10,
        max_pages=3
    )

    print(f"Found {len(post_urls)} posts")

    # Step 2: Scrape each post
    for i, post_url in enumerate(post_urls, 1):
        print(f"\n[{i}/{len(post_urls)}] Scraping: {post_url}")

        # Get post details
        post_details = scrape_post_details(scraper, post_url)

        if post_details:
            print(f"  Title: {post_details['title']}")
            print(f"  Author: {post_details.get('author', 'Unknown')}")
            print(f"  Date: {post_details.get('publishDate', 'Unknown')}")

            # Get reactions (reuse soup from previous request)
            soup = scraper.get_html(post_url)
            reactions = extract_vote_reactions(scraper, post_url, soup)

            if reactions:
                print(f"  Reactions: {reactions}")

            # Save to file or database
            # ...

finally:
    scraper.close()
```

---

## Testing

Run the test script to verify scraper functionality:

```bash
python3 test_scraper.py
```

This will:
1. Fetch 5 post URLs from a category
2. Scrape details from one post
3. Extract reactions from the post
4. Save sample output to `data/test_post.json`

---

## Error Handling

The scraper implements robust error handling:

**Network Errors:**
- Automatic retries with exponential backoff
- Max 3 retry attempts (configurable)
- Raises `NetworkError` after exhausting retries

**Parse Errors:**
- Graceful degradation for missing fields
- Returns `None` for optional fields
- Logs warnings for missing data

**Rate Limiting:**
- Detects HTTP 429 responses
- Respects `Retry-After` header
- Raises `RateLimitError` with retry delay

**Configuration:**
```python
# In config.py
SKIP_ON_ERROR = True          # Continue on errors
SAVE_PARTIAL_DATA = True      # Save incomplete posts
GRACEFUL_DEGRADATION = True   # Don't fail on missing fields
```

---

## Vietnamese Text Handling

The scraper properly handles Vietnamese text:

- **Encoding**: Uses UTF-8 with automatic detection
- **Normalization**: Unicode normalization (NFKC)
- **Date Parsing**: Supports Vietnamese date formats
- **Text Cleaning**: Removes extra whitespace, normalizes characters

---

## Rate Limiting Best Practices

To be respectful to TuoiTre.vn servers:

1. **Use reasonable delays**: Default 2-5 seconds is recommended
2. **Don't crawl too aggressively**: Limit concurrent requests
3. **Respect robots.txt**: Check allowed pages
4. **Monitor for blocking**: Watch for 429 responses
5. **Use caching**: Don't re-fetch the same page

**Recommended settings:**
```python
scraper = TuoiTreScraper(
    delay_min=2.0,    # At least 2 seconds
    delay_max=5.0,    # Up to 5 seconds
    max_retries=3,    # Retry up to 3 times
    timeout=30        # 30 second timeout
)
```

---

## Integration with Main Crawler

The scraper is designed to integrate with the main crawler:

```python
# In main.py
from crawler.scraper import TuoiTreScraper, get_category_post_urls, scrape_post_details

def main():
    scraper = TuoiTreScraper(
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        max_retries=args.max_retries
    )

    try:
        for category_url in category_urls:
            post_urls = get_category_post_urls(scraper, category_url, args.count)

            for post_url in post_urls:
                post_details = scrape_post_details(scraper, post_url)
                # Process post_details...

    finally:
        scraper.close()
```

---

## Next Steps

The scraper module is now complete. Next implementation tasks:

1. **Comment Scraper**: Implement comment extraction with nested replies
2. **Media Downloader**: Implement media file downloads
3. **JSON Exporter**: Save scraped data to JSON files
4. **Main Crawler Integration**: Connect scraper to main.py
5. **Testing**: Add comprehensive tests
