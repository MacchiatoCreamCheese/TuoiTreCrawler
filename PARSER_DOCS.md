# TuoiTre Comment Parser Documentation

## Overview

The `crawler/parser.py` module provides comprehensive functionality for extracting comments from TuoiTre.vn posts, including:

- Extracting all comments with full metadata
- Recursive extraction of nested replies (unlimited depth)
- Vote reaction extraction for each comment
- Graceful handling of posts with no comments
- Validation to ensure at least one post has 20+ comments
- Comment statistics and analysis

## Core Functions

### 1. extract_comments()

The main function for extracting all comments from a post.

**Signature:**
```python
def extract_comments(
    scraper,
    post_url: str,
    soup: BeautifulSoup = None,
    max_depth: int = None
) -> List[Dict[str, Any]]
```

**Parameters:**
- `scraper`: TuoiTreScraper instance
- `post_url`: URL of the post to extract comments from
- `soup`: Optional BeautifulSoup object (if already fetched)
- `max_depth`: Maximum depth for nested replies (defaults to `config.MAX_COMMENT_DEPTH`)

**Returns:**
List of comment dictionaries with nested replies

**Comment Structure:**
```python
{
    'commentId': 'comment_123456',     # Unique identifier
    'author': 'User Name',              # Comment author
    'text': 'Comment content...',       # Comment text
    'date': '2024-01-01T12:00:00',     # ISO timestamp
    'vote_react_list': {                # Vote reactions
        'like': 10,
        'love': 5,
        'haha': 2
    },
    'depth': 0,                         # Nesting depth (0 = top-level)
    'replies': [                        # Nested replies (same structure)
        {
            'commentId': 'comment_789012',
            'author': 'Another User',
            'text': 'Reply content...',
            'date': '2024-01-01T13:00:00',
            'vote_react_list': {},
            'depth': 1,
            'replies': []
        }
    ]
}
```

**Example:**
```python
from crawler.scraper import TuoiTreScraper
from crawler.parser import extract_comments

scraper = TuoiTreScraper()
post_url = "https://tuoitre.vn/some-article-123456.htm"

comments = extract_comments(scraper, post_url)

print(f"Found {len(comments)} top-level comments")
for comment in comments:
    print(f"- {comment['author']}: {comment['text'][:50]}...")
    print(f"  Reactions: {comment['vote_react_list']}")
    print(f"  Replies: {len(comment['replies'])}")

scraper.close()
```

**Features:**
- ✅ Automatically detects comment container
- ✅ Extracts all comment fields (ID, author, text, date, reactions)
- ✅ Recursively extracts nested replies
- ✅ Handles pagination (if LOAD_ALL_COMMENTS is enabled)
- ✅ Gracefully handles missing data
- ✅ Returns empty list if no comments found

---

### 2. validate_comment_count()

Validates that a post has minimum required number of comments.

**Signature:**
```python
def validate_comment_count(
    comments: List[Dict[str, Any]],
    min_required: int = 20
) -> bool
```

**Parameters:**
- `comments`: List of comment dictionaries from `extract_comments()`
- `min_required`: Minimum number of comments required (default: 20)

**Returns:**
- `True` if total comments (including nested) >= min_required
- `False` otherwise

**Example:**
```python
comments = extract_comments(scraper, post_url)

if validate_comment_count(comments, min_required=20):
    print("✓ This post has 20+ comments")
else:
    print("✗ This post has fewer than 20 comments")
```

**Note:** Counts ALL comments including nested replies at any depth.

---

### 3. find_posts_with_comments()

Searches through multiple posts to find ones with minimum comment count.

**Signature:**
```python
def find_posts_with_comments(
    scraper,
    post_urls: List[str],
    min_comments: int = 20
) -> Tuple[List[str], List[int]]
```

**Parameters:**
- `scraper`: TuoiTreScraper instance
- `post_urls`: List of post URLs to check
- `min_comments`: Minimum number of comments required (default: 20)

**Returns:**
Tuple of:
1. List of post URLs that have >= min_comments
2. List of comment counts for all checked posts

**Example:**
```python
from crawler.scraper import TuoiTreScraper, get_category_post_urls
from crawler.parser import find_posts_with_comments

scraper = TuoiTreScraper()

# Get post URLs from a category
post_urls = get_category_post_urls(
    scraper,
    "https://tuoitre.vn/thoi-su.htm",
    max_posts=20
)

# Find posts with 20+ comments
posts_with_enough, counts = find_posts_with_comments(
    scraper,
    post_urls,
    min_comments=20
)

print(f"Found {len(posts_with_enough)} posts with 20+ comments:")
for url in posts_with_enough:
    print(f"  - {url}")

scraper.close()
```

**Use Case:**
Use this to ensure your crawl includes at least one post meeting the comment requirement.

---

### 4. get_comment_statistics()

Get detailed statistics about comment structure.

**Signature:**
```python
def get_comment_statistics(
    comments: List[Dict[str, Any]]
) -> Dict[str, Any]
```

**Parameters:**
- `comments`: List of comment dictionaries

**Returns:**
Dictionary with statistics:
```python
{
    'total_comments': 45,              # Total including nested
    'top_level_comments': 15,          # Only top-level
    'max_depth': 3,                    # Maximum nesting depth
    'depth_distribution': {            # Comments at each depth
        0: 15,
        1: 20,
        2: 8,
        3: 2
    },
    'comments_with_reactions': 30,     # Comments with reactions
    'average_replies_per_comment': 2.0 # Avg replies
}
```

**Example:**
```python
comments = extract_comments(scraper, post_url)
stats = get_comment_statistics(comments)

print(f"Total comments: {stats['total_comments']}")
print(f"Max depth: {stats['max_depth']}")
print(f"Comments with reactions: {stats['comments_with_reactions']}")
```

---

## Comment Field Extraction

### commentId

**Extraction Strategy:**
1. Check `data-comment-id` attribute
2. Check `id` attribute
3. Check child elements with `data-commentid`
4. Generate unique ID if not found (prefix: `comment_`)

**Format:** String (e.g., "123456" or "comment_abc123")

---

### author

**Extraction Strategy:**
1. Try `<span class="author">` or similar
2. Try `<a class="user-name">` or similar
3. Try `<strong class="author">`
4. Try `<meta itemprop="author">`
5. Default to "Anonymous" if not found

**Format:** String (Vietnamese text cleaned and normalized)

---

### text

**Extraction Strategy:**
1. Find comment content container (`comment-content`, etc.)
2. Extract text, excluding nested reply containers
3. Clean and normalize text (remove extra whitespace)

**Format:** String (Vietnamese text)

**Example:**
```
"Bài viết rất hay và bổ ích. Cảm ơn tác giả đã chia sẻ!"
```

---

### date

**Extraction Strategy:**
1. Try `<time datetime="...">` attribute
2. Try `<span class="date">` or similar
3. Parse Vietnamese date formats
4. Return ISO 8601 format or original string

**Format:** ISO 8601 string or original date text

**Examples:**
```
"2024-01-01T12:00:00"
"10/12/2024 14:30"
```

---

### vote_react_list

**Extraction Strategy:**
1. Find reaction container element
2. Extract individual reaction counts
3. Determine reaction type from CSS classes
4. Fallback to data attributes

**Format:** Dictionary with reaction types and counts

**Examples:**
```python
# Post with reactions
{
    'like': 15,
    'love': 3,
    'haha': 1
}

# Post without reactions
{}
```

**Reaction Types:**
- `like` - Like/thumbs up
- `love` - Love/heart
- `haha` - Laugh
- `wow` - Wow/surprised
- `sad` - Sad
- `angry` - Angry

---

### depth

**Format:** Integer (0-based)

**Values:**
- `0` - Top-level comment
- `1` - Reply to top-level comment
- `2` - Reply to reply
- `3+` - Deeper nesting

**Configuration:**
Maximum depth controlled by `config.MAX_COMMENT_DEPTH` (default: 10)

---

### replies

**Format:** List of comment dictionaries (same structure)

**Recursive Structure:**
```python
{
    'commentId': 'comment_1',
    'text': 'Top-level comment',
    'depth': 0,
    'replies': [
        {
            'commentId': 'comment_2',
            'text': 'First reply',
            'depth': 1,
            'replies': [
                {
                    'commentId': 'comment_3',
                    'text': 'Nested reply',
                    'depth': 2,
                    'replies': []
                }
            ]
        }
    ]
}
```

---

## Recursive Reply Extraction

The parser uses recursive extraction to handle nested comments of any depth:

```python
def _extract_nested_replies(element, post_url, parent_depth, max_depth):
    """Recursively extract nested replies"""

    # Stop at max depth
    if parent_depth >= max_depth:
        return []

    # Find reply container
    reply_container = find_reply_container(element)

    # Extract each reply
    for reply_elem in reply_container:
        reply = parse_comment(reply_elem, depth=parent_depth + 1)

        # Recursively extract nested replies
        reply['replies'] = _extract_nested_replies(
            reply_elem,
            post_url,
            parent_depth + 1,
            max_depth
        )

    return replies
```

**Depth Limit:**
- Default: 10 levels (from `config.MAX_COMMENT_DEPTH`)
- Can be customized per call
- Prevents infinite recursion
- Stops gracefully at max depth

---

## Handling Posts with No Comments

The parser gracefully handles posts without comments:

```python
comments = extract_comments(scraper, post_url)

if not comments:
    # Post has no comments - this is normal
    print("No comments on this post")
else:
    print(f"Found {len(comments)} comments")
```

**Behavior:**
- Returns empty list `[]` if no comments found
- Logs info message (not error)
- Does not raise exception
- Safe to process empty list

**Example with Safe Processing:**
```python
comments = extract_comments(scraper, post_url)

# Safe to iterate even if empty
for comment in comments:
    process_comment(comment)

# Safe to get statistics
stats = get_comment_statistics(comments)
# Returns: {'total_comments': 0, ...}

# Safe to validate
is_valid = validate_comment_count(comments, min_required=20)
# Returns: False
```

---

## Ensuring 20+ Comments Requirement

### Strategy 1: Use find_posts_with_comments()

```python
scraper = TuoiTreScraper()

# Get many post URLs
post_urls = get_category_post_urls(
    scraper,
    "https://tuoitre.vn/thoi-su.htm",
    max_posts=50
)

# Find posts with 20+ comments
posts_with_enough, counts = find_posts_with_comments(
    scraper,
    post_urls,
    min_comments=20
)

if posts_with_enough:
    print(f"✓ Found {len(posts_with_enough)} posts with 20+ comments")
    # Use these posts for crawling
else:
    print("Need to check more posts or different categories")
```

### Strategy 2: Validate During Crawling

```python
min_comments_met = False

for post_url in post_urls:
    # Extract comments
    comments = extract_comments(scraper, post_url)

    # Check if this meets requirement
    if validate_comment_count(comments, min_required=20):
        min_comments_met = True
        print(f"✓ Found post with 20+ comments: {post_url}")

    # Save post data...

# Final validation
if not min_comments_met:
    raise ValueError("No posts with 20+ comments found!")
```

### Strategy 3: Pre-check Before Full Crawl

```python
# Quick check: count comments without full extraction
def quick_comment_count(scraper, post_url):
    soup = scraper.get_html(post_url)
    comments = extract_comments(scraper, post_url, soup=soup)
    return len(comments)

# Check posts quickly
for post_url in post_urls[:20]:  # Check first 20
    count = quick_comment_count(scraper, post_url)
    if count >= 20:
        print(f"✓ Post {post_url} has {count} comments")
        # Add to crawl list
        break
```

---

## Error Handling

### Graceful Degradation

The parser implements graceful degradation controlled by config:

```python
# config.py
GRACEFUL_DEGRADATION = True  # Don't fail on missing fields
SKIP_ON_ERROR = True         # Continue on individual comment errors
```

**Behavior:**
- Missing author → "Anonymous"
- Missing text → ""
- Missing date → None
- Missing reactions → {}
- Failed nested extraction → []

### Error Logging

All errors are logged with appropriate level:

```python
logger.info("No comments found")          # Normal condition
logger.warning("Failed to parse comment") # Recoverable error
logger.error("Failed to extract comments") # Serious error
```

---

## Complete Usage Example

```python
from crawler.scraper import TuoiTreScraper, get_category_post_urls
from crawler.parser import (
    extract_comments,
    validate_comment_count,
    find_posts_with_comments,
    get_comment_statistics
)

# Initialize scraper
scraper = TuoiTreScraper()

try:
    # Step 1: Get post URLs
    post_urls = get_category_post_urls(
        scraper,
        "https://tuoitre.vn/thoi-su.htm",
        max_posts=30
    )

    # Step 2: Find posts with enough comments
    posts_with_enough, counts = find_posts_with_comments(
        scraper,
        post_urls,
        min_comments=20
    )

    if not posts_with_enough:
        print("WARNING: No posts with 20+ comments found")

    # Step 3: Extract comments from each post
    all_posts_data = []

    for post_url in post_urls:
        # Extract comments
        comments = extract_comments(scraper, post_url)

        # Get statistics
        stats = get_comment_statistics(comments)

        # Validate
        meets_requirement = validate_comment_count(comments, 20)

        # Save data
        post_data = {
            'url': post_url,
            'comments': comments,
            'comment_count': stats['total_comments'],
            'meets_20_comment_requirement': meets_requirement
        }

        all_posts_data.append(post_data)

        print(f"Post: {post_url}")
        print(f"  Comments: {stats['total_comments']}")
        print(f"  Max depth: {stats['max_depth']}")
        print(f"  Meets requirement: {meets_requirement}")

finally:
    scraper.close()
```

---

## Testing

Run the test suite:
```bash
python3 test_parser.py
```

**Tests Include:**
1. ✅ Extract comments from a post
2. ✅ Find posts with 20+ comments
3. ✅ Extract nested replies
4. ✅ Extract comment reactions

**Sample Output:**
```
[Test 1] Extracting comments from a post...
✓ Extracted 15 top-level comments (45 total including replies)

Comment Statistics:
  Total comments: 45
  Top-level comments: 15
  Max nesting depth: 3
  Comments with reactions: 30

✓ This post meets the 20+ comments requirement

[Test 2] Finding posts with 20+ comments...
✓ Found 3 post(s) with 20+ comments
```

---

## Configuration

Relevant config settings:

```python
# config.py
MAX_COMMENT_DEPTH = 10        # Maximum nesting depth
LOAD_ALL_COMMENTS = True      # Load paginated comments
GRACEFUL_DEGRADATION = True   # Don't fail on missing data
SKIP_ON_ERROR = True          # Continue on errors
MIN_COMMENTS_REQUIRED = 20    # Minimum comments for validation
```

---

## Performance Considerations

**Comment Extraction is Expensive:**
- Each post requires fetching and parsing HTML
- Recursive extraction for nested comments
- Multiple DOM queries per comment

**Optimization Tips:**
1. Use `soup` parameter to reuse fetched HTML
2. Limit `max_depth` if deep nesting not needed
3. Set `LOAD_ALL_COMMENTS = False` to skip pagination
4. Use `find_posts_with_comments()` to pre-filter

**Example Optimization:**
```python
# Fetch once, use multiple times
soup = scraper.get_html(post_url)

# Extract post details
post_details = scrape_post_details(scraper, post_url)

# Extract comments using same soup
comments = extract_comments(scraper, post_url, soup=soup)
```

---

## Summary

The comment parser provides:
- ✅ Complete comment extraction with all fields
- ✅ Recursive nested reply handling (unlimited depth)
- ✅ Vote reaction extraction
- ✅ Graceful handling of posts without comments
- ✅ Validation for 20+ comments requirement
- ✅ Detailed statistics and analysis
- ✅ Robust error handling
- ✅ Vietnamese text support

Ready for production use!
