"""
Console UI for TuoiTre.vn crawler.
Prompts user for category URLs and post counts, then runs the crawler.
"""

import sys
from types import SimpleNamespace

import config
from main import (
    setup_logging,
    validate_urls,
    crawl_posts,
    print_summary,
)


def prompt_category_urls() -> list[str]:
    """Prompt for three category URLs with basic validation."""
    defaults = list(config.CATEGORY_URLS.values())
    urls = []
    print("\nEnter three TuoiTre category URLs (press Enter to use defaults):")
    for i in range(3):
        prompt = f"  Category {i + 1} URL [default: {defaults[i] if i < len(defaults) else ''}]: "
        value = input(prompt).strip()
        if not value:
            if i < len(defaults):
                value = defaults[i]
            else:
                print("  URL is required.")
                return []
        urls.append(value)

    if not validate_urls(urls):
        print("Invalid URL format detected. Please enter valid https URLs.")
        return []
    return urls


def prompt_post_count() -> int:
    """Prompt for posts per category; ensure total >= 100."""
    default = config.POSTS_PER_CATEGORY
    value = input(f"\nNumber of posts per category (default {default}, total >= 100): ").strip()
    if not value:
        count = default
    else:
        try:
            count = int(value)
        except ValueError:
            print("Please enter a valid integer.")
            return 0
    if count < 1:
        print("Post count must be at least 1.")
        return 0
    return count


def build_args(urls: list[str], count: int):
    """Build an argparse-like namespace for crawl_posts."""
    return SimpleNamespace(
        urls=urls,
        count=count,
        delay_min=config.REQUEST_DELAY_MIN,
        delay_max=config.REQUEST_DELAY_MAX,
        no_media=False,
        images_only=False,
        log_level=config.LOG_LEVEL,
        output_dir=None,
        strict=False,
        max_retries=config.MAX_RETRIES,
        dry_run=False,
    )


def run_console_ui() -> int:
    """Entry point for interactive console flow."""
    print("\n=== TuoiTre.vn Crawler - Console UI ===")
    urls = prompt_category_urls()
    if len(urls) != 3:
        return 1

    count = prompt_post_count()
    if count <= 0:
        return 1

    total = len(urls) * count
    if total < 100:
        print(f"Total posts must be at least 100. You entered {total}.")
        return 1

    # Setup logging
    logger = setup_logging(config.LOG_LEVEL)

    # Create directories
    try:
        config.create_directories()
    except Exception as e:
        print(f"Failed to create directories: {e}")
        return 1

    args = build_args(urls, count)

    try:
        stats = crawl_posts(args, logger)
        print_summary(stats, logger)

        if stats.get('posts_with_20plus_comments', 0) == 0:
            print("\nWARNING: No post with more than 20 comments was found. Consider rerunning with more posts or different categories.")
        if stats.get('total_posts_scraped', 0) < 100:
            print(f"\nWARNING: Only scraped {stats.get('total_posts_scraped', 0)} posts (target: 100+).")

        return 0
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_console_ui())

