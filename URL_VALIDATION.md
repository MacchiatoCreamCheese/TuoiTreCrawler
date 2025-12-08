# URL Validation System

## Overview

The crawler uses a two-layer URL validation system:

1. **config.is_url_allowed()** - Basic blacklist filter for disallowed paths
2. **_is_valid_article_url()** - Complete validation including article patterns

## Layer 1: config.is_url_allowed()

Located in `config.py:107`

**Purpose:** Block URLs containing disallowed paths

**Disallowed Paths:**
- `/tim-kiem.htm` - Search pages
- `/print/` - Print versions of articles
- `/ImageView.aspx` - Image viewer pages
- `/ajax-box-mua-sam/` - Shopping box AJAX pages

**Usage:**
```python
import config

if config.is_url_allowed(url):
    # URL doesn't contain any disallowed paths
    proceed_with_scraping(url)
```

**Test Results:**
```
✓ Blocks /tim-kiem.htm (search pages)
✓ Blocks /print/ (print versions)
✓ Blocks /ImageView.aspx (image viewer)
✓ Blocks /ajax-box-mua-sam/ (shopping AJAX)
✓ Allows normal article URLs
```

## Layer 2: _is_valid_article_url()

Located in `crawler/scraper.py:279`

**Purpose:** Complete validation including:
1. Disallowed paths check (uses `config.is_url_allowed()`)
2. Domain verification (must be from tuoitre.vn)
3. Article ID pattern matching (must have format `-123456.htm`)
4. Exclusion of category pages, tag pages, video pages, etc.

**Validation Logic:**
```python
def _is_valid_article_url(url: str) -> bool:
    # 1. Check if empty
    if not url:
        return False

    # 2. Check against disallowed paths
    if not config.is_url_allowed(url):
        return False

    # 3. Must be from tuoitre.vn
    if 'tuoitre.vn' not in url:
        return False

    # 4. Must have article ID pattern
    has_id = bool(re.search(r'-\d{6,}\.htm', url))
    if not has_id:
        return False

    # 5. Check exclusion patterns
    exclude_patterns = ['/tag/', '/video/', '/podcast/', ...]
    # ... additional checks

    return True
```

**Examples:**

### Valid Articles ✓
```
https://tuoitre.vn/thoi-su/article-title-123456.htm
https://tuoitre.vn/the-gioi/world-news-789012.htm
https://tuoitre.vn/kinh-doanh/business-article-345678.htm
```

### Blocked by Disallowed Paths ✗
```
https://tuoitre.vn/tim-kiem.htm?q=test           (search page)
https://tuoitre.vn/print/article-123456.htm      (print version)
https://tuoitre.vn/ImageView.aspx?id=123         (image viewer)
https://tuoitre.vn/ajax-box-mua-sam/item.htm     (shopping AJAX)
```

### Blocked by Pattern Validation ✗
```
https://tuoitre.vn/thoi-su.htm                   (category page - no ID)
https://tuoitre.vn/thoi-su-p2.htm                (pagination page)
https://tuoitre.vn/tag/covid-19.htm              (tag page)
https://tuoitre.vn/video/news-video.htm          (video page)
https://example.com/article-123456.htm           (wrong domain)
```

## Integration Points

### 1. Category URL Collection
In `get_category_post_urls()` at line 244:
```python
if self._is_valid_article_url(full_url):
    post_urls.append(full_url)
```

### 2. Post Scraping
In `scrape_post_details()` at line 349:
```python
# Validate URL before scraping
if not config.is_url_allowed(post_url):
    logger.warning(f"Skipping disallowed URL: {post_url}")
    return None
```

## Adding New Disallowed Paths

To block additional URL patterns, edit `config.py`:

```python
DISALLOWED_PATHS = [
    '/tim-kiem.htm',
    '/print/',
    '/ImageView.aspx',
    '/ajax-box-mua-sam/',
    '/new-path-to-block/',  # Add new patterns here
]
```

## Testing

Run the URL validation test suite:
```bash
python3 test_url_validation.py
```

This will:
1. Verify all disallowed paths are configured
2. Test config.is_url_allowed() against various URLs
3. Test _is_valid_article_url() with complete validation

**Note:** The test requires dependencies (beautifulsoup4, etc.). If dependencies are missing, it will test only `config.is_url_allowed()`.

## Summary

**Two-Layer Protection:**
- **Layer 1 (config):** Fast blacklist check - blocks known bad paths
- **Layer 2 (scraper):** Complete validation - ensures valid article URLs

**Both layers work together:**
```
URL → config.is_url_allowed() → _is_valid_article_url() → Scrape
      ↓ if blocked                ↓ if invalid           ↓ if valid
      Skip                         Skip                   Process
```

This design allows:
- Easy configuration of disallowed paths in one place
- Comprehensive validation before expensive scraping operations
- Clear separation between configuration and business logic
