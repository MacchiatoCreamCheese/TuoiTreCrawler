# TuoiTre.vn Web Crawler

Python crawler for tuoitre.vn articles: collects posts, comments, reactions, downloads media (images + audio), and saves JSON outputs.

## Features
- Crawl multiple categories with configurable post counts and delays
- Scrape post metadata (title, author, date, category, tags)
- Extract article content (text + optional HTML) with Unicode normalization
- Fetch comments via TuoiTre API (nested replies + reactions)
- Download images and audio (podcast/tts) with validation and progress
- Save per-post JSON with optional metadata; graceful error handling

## Requirements
- Python 3.7+
- `requests`, `beautifulsoup4`, `lxml`, `fake-useragent`, `pyyaml` (see `requirements.txt`)

## Install
```bash
git clone <repository-url>
cd TuoiTreCrawler
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration (key fields in `src/config.py`)
- `CATEGORY_URLS`: default categories (`thoi-su`, `phap-luat`, `nhip-song-tre`)
- `POSTS_PER_CATEGORY`: default posts per category
- `REQUEST_DELAY_MIN/MAX`, `REQUEST_TIMEOUT`, `MAX_RETRIES`
- Media: `DOWNLOAD_IMAGES`, `DOWNLOAD_AUDIO`; paths `IMAGES_DIR=./images`, `AUDIO_DIR=./audio`
- JSON output: `JSON_OUTPUT_DIR=./data/metadata`, `JSON_INDENT`, `INCLUDE_METADATA`
- Error behavior: `SKIP_ON_ERROR`, `SAVE_PARTIAL_DATA`, `GRACEFUL_DEGRADATION`

## Running (CLI)
```bash
python src/main.py                     # default crawl (35 posts each category)
python src/main.py --urls https://tuoitre.vn/thoi-su.htm --count 50
python src/main.py --delay-min 2 --delay-max 4
python src/main.py --no-media          # skip media
python src/main.py --images-only       # images, no audio
python src/main.py --log-level DEBUG
python src/main.py --strict            # fail fast
python src/main.py --dry-run           # print config, exit
```
`--output-dir` overrides JSON output location.

## Console UI
Interactive flow (prompts for 3 URLs, requires total >= 100):
```bash
python -m src.console_ui
```

## Workflow (simplified)
1) Collect post URLs per category (pagination, filtered article URLs).  
2) For each post:
   - Scrape details (title, author, date, category, description, tags, content text/html).
   - Fetch comments via API (build nested tree, count reactions).
   - Extract vote reactions from page (best-effort).
   - Download media (images to `./images/{postId}/`, audio to `./audio/{postId}.<ext>`) unless `--no-media`.
   - Format and validate data; save JSON to `JSON_OUTPUT_DIR` (default `./data/metadata`).
3) Print summary (counts, timings, warnings for <20 comments or <100 posts).

## Data formats
### Post JSON (from `format_post_data`)
```jsonc
{
  "postId": "1234567890123",
  "title": "...",
  "content": {"text": "..."},
  "author": "...",
  "date": "2025-12-08T12:00:00",
  "category": "thoi-su",
  "audio_podcast": "./audio/1234567890123.m4a",
  "vote_reactions": {"like": 10, "love": 2},
  "comments": [...],
  "url": "https://tuoitre.vn/...",
  "description": "...",
  "tags": ["tag1", "tag2"],
  "media_paths": {"images": ["./images/1234567890123/img_1.jpg"], "audio": "./audio/1234567890123.m4a"},
  "comment_count": 45,
  "metadata": { "crawled_at": "...", "crawler_version": "1.0.0", "data_format_version": "1.0" }
}
```

### Comment structure
```jsonc
{
  "commentId": "uuid",
  "author": "User",
  "text": "Comment text",
  "date": "2025-12-08T12:34:56",
  "vote_react_list": {"like": 5, "love": 1},
  "replies": [...],
  "depth": 0
}
```

## Media downloading
- Images: parsed from article content; saved under `./images/{postId}/img_<n>_<name>`.
- Audio: constructed from `embedTTS.init` script or `<audio>` tags; saved as `./audio/{postId}.<ext>`.
- Validation: size > 0; optional progress logs for large files; retries via scraper.

## Storage layout (default)
```
data/metadata/          # per-post JSON exports
images/<postId>/        # downloaded images
audio/<postId>.m4a      # downloaded audio (if any)
```

## Architecture (modules)
- `src/main.py`: CLI orchestration, argument parsing, logging setup, crawl loop.
- `src/console_ui.py`: Interactive prompts wrapper.
- `src/crawler/scraper.py`: HTTP session, rate limiting, category/post scraping, reactions.
- `src/crawler/parser.py`: Comment API consumption, tree building, stats.
- `src/crawler/downloader.py`: Images/audio downloading & validation.
- `src/crawler/json_exporter.py`: Validation and JSON saving.
- `src/crawler/utils/`: helpers, exceptions, retry/error handling, logging wrapper.

## Error handling & retries
- Automatic retries on network errors with backoff.
- `SKIP_ON_ERROR=True` continues on per-post failures; `--strict` to fail fast.
- Warnings when no post meets 20+ comments or <100 posts scraped.

## Troubleshooting
- Encoding issues: ensure UTF-8 locale; outputs saved UTF-8.
- Blocking/rate limiting: increase delays (`--delay-min/--delay-max`) and keep `MAX_RETRIES` modest.
- SSL issues: `pip install --upgrade certifi`.

## License / Usage
Educational use only. Respect tuoitre.vn terms of service.