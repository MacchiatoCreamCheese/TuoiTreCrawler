# TuoiTre.vn Crawler Report

## Overview
This report documents the TuoiTre.vn crawler we built, the approach we took, challenges we encountered, and how we addressed them. It also explains how to run the crawler (command-line and console UI), what the outputs look like, how we retrieve and store data (including nested comments and media), and how we handle pagination, missing media, posts without comments, and other edge cases—all while respecting reasonable use and the site’s terms of service.

## Goals and Scope
- Collect recent TuoiTre.vn articles across configurable categories.
- Extract article metadata (title, author, publish date, category, description, tags), full text, vote reactions, and nested comments/replies.
- Download associated media (images and audio/podcast) when enabled.
- Save per-post JSON in a predictable, validated structure for downstream use.
- Be resilient to transient failures, pagination quirks, and optional/missing fields, and allow a strict fail-fast mode when needed.

## Architecture and Approach
The project is organized into focused modules:
- `src/main.py`: CLI entrypoint, argument parsing, logging, run orchestration.
- `src/console_ui.py`: Guided interactive flow for non-CLI users.
- `src/crawler/scraper.py`: HTTP session, rate limiting, user-agent rotation, category pagination, article detail scraping, reaction extraction.
- `src/crawler/parser.py`: Comment API consumption, tree building, depth computation, statistics.
- `src/crawler/downloader.py`: Image/audio discovery and download with validation.
- `src/crawler/json_exporter.py`: Validation and JSON writing with metadata.
- `src/crawler/utils/*`: Helpers (text cleanup, IDs, filenames, retry/backoff, logging, exceptions).

### Data Flow (per run)
1. Collect category URLs (CLI args or defaults) and target post count per category.
2. For each category, paginate and collect article URLs up to the configured count.
3. For each article URL:
   - Scrape article details (metadata, text/html, tags, reactions).
   - Fetch and build nested comments via the TuoiTre comment API.
   - Download media (images, audio) if enabled.
   - Validate and format post data; persist as JSON.
4. Emit summary statistics (posts, comments, media, timing).

## Key Improvements Made
- **Strict mode now truly fails fast**: `--strict` disables graceful degradation/skip/partial saving so errors propagate immediately.
- **Configurable retries**: HTTP retries use the CLI `--max-retries` with exponential backoff and rate-limit handling (429 Retry-After respected).
- **Comment robustness**: Comment API requests now use the same retry/backoff/UA rotation as page fetches; post ID parsing accepts shorter IDs; depths are computed from parents so nested reply metadata is accurate.
- **Graceful media handling**: Image/audio download skips invalid/empty files and logs warnings without crashing unless strict mode is on.

## Running the Crawler
### Command-Line (recommended for batch runs)
From project root in the `ttcrawler` conda environment:
```bash
python src/main.py [options]
```
Common options:
- `--urls <url1> <url2> ...` : category URLs (default: config defaults).
- `--count N` : posts per category (default: config.POSTS_PER_CATEGORY).
- `--delay-min/--delay-max` : request delay bounds (seconds).
- `--max-retries N` : request retry attempts (with backoff).
- `--no-media` : skip all media downloads.
- `--images-only` : only images, no audio.
- `--output-dir PATH` : JSON output directory (default: `./data/metadata`).
- `--log-level {DEBUG,INFO,...}` : verbosity.
- `--strict` : fail fast on errors (no graceful degradation).
- `--dry-run` : print config and exit (no network).

Examples:
```bash
# Default categories, default counts
python src/main.py

# Custom categories and counts
python src/main.py --urls https://tuoitre.vn/thoi-su.htm https://tuoitre.vn/the-gioi.htm --count 20

# Faster tests with minimal media
python src/main.py --urls https://tuoitre.vn/thoi-su.htm --count 5 --images-only

# Fail fast and fewer retries
python src/main.py --strict --max-retries 1
```

### Console UI (guided)
```bash
python -m src.console_ui
```
Prompts for three category URLs (defaults provided), then a per-category post count (requires total ≥ 100). Applies the same crawl flow using sensible defaults.

## Output Format
Per-post JSON is written to `./data/metadata/<postId>.json` (or the specified `--output-dir`). Structure:
```jsonc
{
  "postId": "1234567890123",
  "title": "...",
  "content": { "text": "..." },
  "author": "...",
  "date": "2025-12-08T12:00:00",
  "category": "thoi-su",
  "audio_podcast": "./audio/1234567890123.m4a",
  "vote_reactions": { "like": 10, "love": 2 },
  "comments": [...],                // nested tree with replies
  "url": "https://tuoitre.vn/...",
  "description": "...",
  "tags": ["tag1", "tag2"],
  "media_paths": {
    "images": ["./images/1234567890123/img_1_name.jpg"],
    "audio": "./audio/1234567890123.m4a"
  },
  "comment_count": 45,
  "metadata": {
    "crawled_at": "...",
    "crawler_version": "1.0.0",
    "data_format_version": "1.0"
  }
}
```

### Comments
Each comment:
```jsonc
{
  "commentId": "uuid-or-api-id",
  "author": "User",
  "text": "Comment text",
  "date": "2025-12-08T12:34:56",
  "vote_react_list": {"like": 5, "love": 1},
  "replies": [ ... nested ... ],
  "depth": 0
}
```
Depth is computed from the parent chain; replies increment depth accordingly.

## Data Retrieval Details
### Duplicate Handling
- Deduplication happens only during STEP 1 (URL collection).
- For each category, we paginate (up to 30 pages) until we gather the requested unique post count.
- URLs are normalized, validated (`_is_valid_article_url`), and postId is extracted via `-(\d+)\.htm`; a global `seen_post_ids` set skips any already-seen post across all categories.
- If a page yields no new unique posts, pagination for that category stops; STEP 2 assumes inputs are already unique and performs no duplicate filtering.

### Article Discovery and Pagination
- Category pages are paged as `...-p2.htm`, `...-p3.htm`, etc.; we iterate until we reach the requested post count or `max_pages`.
- Article links are detected from common list item containers (`box-category-item`, `news-item`, etc.) and normalized to absolute URLs.
- Non-article URLs and disallowed paths (search/print/ajax) are filtered.

### Article Scraping
- Title, author, publish date, category, description, tags, and content are extracted using multiple selector fallbacks.
- Content retains text (and optionally HTML internally before formatting), with scripts/iframes stripped from text extraction.
- Reactions are parsed best-effort from reaction containers or data attributes.

### Comments and Nested Replies
- Comment API is called via `_make_request` (inherits retry/backoff/UA rotation).
- Pagination over comments uses a larger page size (100) to reduce calls; continues until no more results.
- IDs are extracted from URLs with a flexible `-\d+\.htm` pattern to avoid missing shorter IDs.
- A tree is built from parent/child relationships; depths are propagated from parents, so nested replies carry correct depth metadata.
- Vote reactions per comment are collected from both reaction maps and individual fields when available.

### Media (Images and Audio)
- Images: Found in main content (and `<picture>/<source>`), normalized to absolute URLs, filtered for valid extensions/sizes. Saved under `./images/<postId>/img_<n>_<name>`.
- Audio: Detected via `<audio>` tags or constructed from `embedTTS.init` script parameters; saved as `./audio/<postId>.<ext>`.
- Downloads stream with validation (non-empty files). Existing files are skipped to avoid re-downloads.

## Error Handling and Edge Cases
- **Pagination holes**: If a category page has no posts, pagination stops early with a warning.
- **Missing fields**: Title/author/date fall back to alternate selectors; absent fields are stored as empty/None. Validation ensures required JSON fields (`postId`, `title`, `content`) exist; others are optional.
- **Missing images/audio**: If media is absent or fails download, we log a warning and continue (unless `--strict`); `media_paths` will omit missing entries.
- **Posts without comments**: Comment API returning empty results produces `comments: []` and `comment_count = 0`; stats reflect that.
- **Rate limiting**: 429 responses honor `Retry-After`; exponential backoff is used for network/timeout/request errors up to `--max-retries`.
- **Encoding**: Responses use apparent encoding; JSON is written UTF-8 with `ensure_ascii=False`. Basic checks flag replacement characters if present.
- **Strict mode**: When `--strict` is set, graceful degradation is disabled and partial saves are off; any scraping/parse/download failure raises, stopping the run.
- **Invalid URLs**: CLI URL validation rejects malformed URLs; console UI prompts again if invalid input is provided.
- **Disallowed paths**: Search/print/ajax paths are filtered to avoid non-article content.

## Usage Guidance and Respecting Terms
- Keep request delays reasonable (`--delay-min/--delay-max`) and retries modest to avoid undue load.
- Limit categories/counts when testing; prefer `--dry-run` to verify configuration without traffic.
- Use the crawler for educational/research purposes; review TuoiTre.vn terms of service and avoid redistributing or republishing content in violation of their policies.
- If the site signals rate limits, allow backoff to proceed; do not circumvent protections.

## Challenges Encountered and Solutions
1) **Unreliable page structures**: Article pages and category listings use varied class names and containers.  
   *Solution*: Implement multiple selector fallbacks for titles, authors, dates, tags, and content; normalize URLs; filter disallowed paths.

2) **Comment API variance and nesting**: The API returns paged JSON with parent/child IDs; some article IDs are shorter than expected.  
   *Solution*: Loosened ID regex, paginated with larger pages, wrapped requests with backoff, and rebuilt a parent-child tree with depth propagation.

3) **Rate limits and transient failures**: 429/timeout/connection issues would drop posts.  
   *Solution*: Centralized retry/backoff in `_make_request`, respect `Retry-After`, configurable `--max-retries`, and strict mode to opt into fail-fast.

4) **Optional media**: Some posts lack images or audio, or links may be invalid.  
   *Solution*: Filter/sanitize URLs, validate downloads (non-empty), and proceed with warnings unless strict mode is enabled.

5) **Output correctness**: Needed consistent, validated JSON with Vietnamese-safe encoding.  
   *Solution*: JSON validation for required fields; UTF-8 `ensure_ascii=False`; added crawl metadata; normalized content text.

## How to Interpret Outputs
- `data/metadata/*.json`: One file per post; look at `comment_count`, `media_paths`, and `metadata.crawled_at` for run context.
- Images: `images/<postId>/...`; Audio: `audio/<postId>.<ext>`.
- Summary logs: totals for posts, comments, media, failures, and timing. Warnings indicate unmet targets (e.g., <20 comments, <100 posts) when applicable.

## Quick Start Checklist
1. Activate environment: `conda activate ttcrawler`
2. Dry run to verify config: `python src/main.py --dry-run`
3. Run a small crawl: `python src/main.py --urls https://tuoitre.vn/thoi-su.htm --count 5 --images-only`
4. Use console UI if preferred: `python -m src.console_ui`
5. Review JSON in `data/metadata/` and media in `images/` and `audio/`.

## Conclusion
The crawler is structured, configurable, and resilient for educational use: it discovers articles via paginated categories, extracts rich metadata, builds nested comments, and optionally downloads media. Robustness improvements (strict mode, retry/backoff, depth-aware comments, flexible ID parsing) make it dependable while keeping the codebase simple and maintainable. Use reasonable delays and modest scopes to respect the site, and rely on the built-in summaries and JSON validation to ensure output quality.

