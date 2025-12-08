#!/usr/bin/env python3
"""
TuoiTre.vn Web Crawler
Main entry point for the web crawler application
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

import config


def setup_logging(log_level: str = None) -> logging.Logger:
    """
    Configure logging for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    # Use config defaults if not provided
    level = log_level or config.LOG_LEVEL

    # Configure root logger (console only)
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    logger = logging.getLogger('TuoiTreCrawler')
    logger.info("Logging initialized")
    logger.info(f"Log level: {level}")
    logger.info("File logging disabled")

    return logger


def validate_urls(urls: List[str]) -> bool:
    """
    Validate that URLs are properly formatted

    Args:
        urls: List of URLs to validate

    Returns:
        True if all URLs are valid, False otherwise
    """
    import re
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    for url in urls:
        if not url_pattern.match(url):
            return False
    return True


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='TuoiTre.vn Web Crawler - Extract articles, comments, and media',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crawl default categories from config
  python main.py

  # Crawl specific category with custom post count
  python main.py --urls https://tuoitre.vn/thoi-su.htm --count 50

  # Crawl multiple categories
  python main.py --urls https://tuoitre.vn/thoi-su.htm https://tuoitre.vn/the-gioi.htm --count 30

  # Use custom delay and enable debug logging
  python main.py --delay-min 3 --delay-max 6 --log-level DEBUG

  # Disable media downloads
  python main.py --no-media
        """
    )

    # Category and crawling options
    parser.add_argument(
        '--urls',
        nargs='+',
        help='Category URLs to crawl (defaults to config.CATEGORY_URLS)',
        metavar='URL'
    )

    parser.add_argument(
        '--count',
        type=int,
        default=config.POSTS_PER_CATEGORY,
        help=f'Number of posts to crawl per category (default: {config.POSTS_PER_CATEGORY})',
        metavar='N'
    )

    # Rate limiting options
    parser.add_argument(
        '--delay-min',
        type=float,
        default=config.REQUEST_DELAY_MIN,
        help=f'Minimum delay between requests in seconds (default: {config.REQUEST_DELAY_MIN})',
        metavar='SEC'
    )

    parser.add_argument(
        '--delay-max',
        type=float,
        default=config.REQUEST_DELAY_MAX,
        help=f'Maximum delay between requests in seconds (default: {config.REQUEST_DELAY_MAX})',
        metavar='SEC'
    )

    # Media download options
    parser.add_argument(
        '--no-media',
        action='store_true',
        help='Disable media downloads (images, audio, video)'
    )

    parser.add_argument(
        '--images-only',
        action='store_true',
        help='Download only images (no audio or video)'
    )

    # Logging options
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default=config.LOG_LEVEL,
        help=f'Set logging level (default: {config.LOG_LEVEL})'
    )

    # Output options
    parser.add_argument(
        '--output-dir',
        help=f'Directory for output JSON files (default: {config.JSON_OUTPUT_DIR})',
        metavar='PATH'
    )

    # Error handling options
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Fail on first error instead of continuing (disables graceful degradation)'
    )

    parser.add_argument(
        '--max-retries',
        type=int,
        default=config.MAX_RETRIES,
        help=f'Maximum number of retries for failed requests (default: {config.MAX_RETRIES})',
        metavar='N'
    )

    # Dry run option
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Print configuration and exit without crawling'
    )

    # Version
    parser.add_argument(
        '--version',
        action='version',
        version='TuoiTre Crawler v1.0.0'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.delay_min > args.delay_max:
        parser.error("--delay-min cannot be greater than --delay-max")

    if args.count < 1:
        parser.error("--count must be at least 1")

    if args.urls and not validate_urls(args.urls):
        parser.error("Invalid URL format provided")

    return args


def print_configuration(args: argparse.Namespace, logger: logging.Logger):
    """
    Print current configuration settings

    Args:
        args: Parsed command-line arguments
        logger: Logger instance
    """
    logger.info("="*60)
    logger.info("TuoiTre.vn Web Crawler Configuration")
    logger.info("="*60)

    # Determine URLs to crawl
    urls_to_crawl = args.urls if args.urls else list(config.CATEGORY_URLS.values())

    logger.info(f"Categories to crawl: {len(urls_to_crawl)}")
    for i, url in enumerate(urls_to_crawl, 1):
        logger.info(f"  {i}. {url}")

    logger.info(f"Posts per category: {args.count}")
    logger.info(f"Total target posts: {len(urls_to_crawl) * args.count}")
    logger.info(f"Request delay: {args.delay_min}s - {args.delay_max}s")
    logger.info(f"Max retries: {args.max_retries}")

    # Media settings
    if args.no_media:
        logger.info("Media downloads: DISABLED")
    elif args.images_only:
        logger.info("Media downloads: Images only")
    else:
        logger.info("Media downloads: All types (images, audio, video)")

    # Error handling
    if args.strict:
        logger.info("Error handling: STRICT (fail on first error)")
    else:
        logger.info("Error handling: Graceful degradation enabled")

    # Output
    output_dir = Path(args.output_dir) if args.output_dir else config.JSON_OUTPUT_DIR
    logger.info(f"Output directory: {output_dir}")

    logger.info("="*60)


def show_progress(current: int, total: int, status: str = ""):
    """
    Display progress bar

    Args:
        current: Current progress
        total: Total items
        status: Optional status message
    """
    if total == 0:
        return

    percentage = (current / total) * 100
    bar_length = 40
    filled = int(bar_length * current / total)
    bar = '█' * filled + '░' * (bar_length - filled)

    print(f'\r[{bar}] {percentage:.1f}% ({current}/{total}) {status}', end='', flush=True)

    if current == total:
        print()  # New line when complete


def crawl_posts(args: argparse.Namespace, logger: logging.Logger) -> Dict[str, Any]:
    """
    Main crawling orchestration

    Args:
        args: Command-line arguments
        logger: Logger instance

    Returns:
        Dictionary with crawl results and statistics
    """
    from crawler.scraper import TuoiTreScraper, get_category_post_urls, scrape_post_details, extract_vote_reactions
    from crawler.parser import extract_comments, validate_comment_count, get_comment_statistics
    from crawler.downloader import download_all_media
    from crawler.json_exporter import save_post_json, format_post_data, save_multiple_posts

    # Initialize statistics
    stats = {
        'total_posts_scraped': 0,
        'total_posts_saved': 0,
        'total_comments': 0,
        'total_images': 0,
        'total_audio': 0,
        'posts_with_20plus_comments': 0,
        'failed_posts': 0,
        'start_time': time.time(),
        'posts_data': []
    }

    # Determine URLs to crawl
    category_urls = args.urls if args.urls else list(config.CATEGORY_URLS.values())

    # Calculate total posts to crawl
    total_posts_target = len(category_urls) * args.count

    logger.info("")
    logger.info("="*60)
    logger.info("Starting TuoiTre.vn Web Crawler")
    logger.info("="*60)
    logger.info(f"Categories: {len(category_urls)}")
    logger.info(f"Posts per category: {args.count}")
    logger.info(f"Total target: {total_posts_target} posts")
    logger.info(f"Delays: {args.delay_min}s - {args.delay_max}s")
    logger.info(f"User-Agent: {config.USER_AGENTS[0]}")
    logger.info("="*60)
    logger.info("")

    # Initialize scraper
    scraper = TuoiTreScraper(
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        max_retries=args.max_retries
    )

    all_posts_data = []
    current_progress = 0

    try:
        # Step 1: Get post URLs from each category
        logger.info("STEP 1: Collecting post URLs from categories...")
        logger.info("-" * 60)

        all_post_urls = []
        for i, category_url in enumerate(category_urls, 1):
            logger.info(f"[{i}/{len(category_urls)}] Category: {category_url}")

            try:
                category_slug = category_url.rstrip('/').split('/')[-1].replace('.htm', '')
                post_urls = get_category_post_urls(
                    scraper,
                    category_url,
                    max_posts=args.count,
                    max_pages=10
                )

                all_post_urls.extend([(category_slug, url) for url in post_urls])
                logger.info(f"  Found {len(post_urls)} posts")

            except Exception as e:
                logger.error(f"  Failed to get URLs from {category_url}: {e}")
                if not config.SKIP_ON_ERROR:
                    raise

        logger.info(f"\n✓ Collected {len(all_post_urls)} post URLs total\n")

        # Step 2: Scrape each post
        logger.info("STEP 2: Scraping posts...")
        logger.info("-" * 60)

        for i, (category_slug, post_url) in enumerate(all_post_urls, 1):
            try:
                current_progress = i
                show_progress(current_progress, len(all_post_urls), f"Post {i}")

                # Scrape post details
                post_details = scrape_post_details(scraper, post_url)
                if not post_details:
                    stats['failed_posts'] += 1
                    continue

                post_id = post_details['postId']
                stats['total_posts_scraped'] += 1

                # Extract comments
                comments = extract_comments(scraper, post_url)
                comment_stats = get_comment_statistics(comments)
                stats['total_comments'] += comment_stats['total_comments']

                # Check 20+ comments requirement
                if validate_comment_count(comments, config.MIN_COMMENTS_REQUIRED):
                    stats['posts_with_20plus_comments'] += 1

                # Extract vote reactions
                vote_reactions = extract_vote_reactions(scraper, post_url)

                # Download media (if enabled)
                media_paths = {'images': [], 'audio': None}
                if not args.no_media:
                    try:
                        media_results = download_all_media(
                            scraper,
                            post_id,
                            post_url,
                            include_images=not args.no_media,
                            include_audio=not args.no_media and not args.images_only
                        )
                        media_paths = media_results
                        stats['total_images'] += len(media_results.get('images', []))
                        if media_results.get('audio'):
                            stats['total_audio'] += 1

                    except Exception as e:
                        logger.warning(f"  Media download failed for {post_id}: {e}")

                # Format complete post data
                # Prefer category from crawl source when available
                category_value = category_slug or post_details.get('category')

                post_data = format_post_data(
                    post_id=post_id,
                    title=post_details.get('title', ''),
                    content=post_details.get('content', ''),
                    author=post_details.get('author'),
                    date=post_details.get('publishDate'),
                    category=category_value,
                    audio_podcast=media_paths.get('audio'),
                    vote_reactions=vote_reactions,
                    comments=comments,
                    url=post_url,
                    description=post_details.get('description'),
                    tags=post_details.get('tags', []),
                    media_paths=media_paths,
                    comment_count=comment_stats['total_comments']
                )

                all_posts_data.append(post_data)

                # Save JSON (if output directory specified)
                if args.output_dir or config.JSON_OUTPUT_DIR:
                    try:
                        output_dir = Path(args.output_dir) if args.output_dir else config.JSON_OUTPUT_DIR
                        save_post_json(post_data, output_dir=output_dir, validate=True)
                        stats['total_posts_saved'] += 1

                    except Exception as e:
                        logger.error(f"  Failed to save JSON for {post_id}: {e}")
                        if not config.SKIP_ON_ERROR:
                            raise

            except Exception as e:
                logger.error(f"\n  Failed to process post {post_url}: {e}")
                stats['failed_posts'] += 1

                if not config.SKIP_ON_ERROR:
                    raise

        # Complete progress bar
        show_progress(len(all_post_urls), len(all_post_urls), "Complete!")

        logger.info("")
        logger.info("✓ Post scraping complete\n")

    finally:
        scraper.close()

    # Calculate final statistics
    stats['end_time'] = time.time()
    stats['duration'] = stats['end_time'] - stats['start_time']
    stats['posts_data'] = all_posts_data

    return stats


def print_summary(stats: Dict[str, Any], logger: logging.Logger):
    """
    Print summary statistics

    Args:
        stats: Statistics dictionary
        logger: Logger instance
    """
    logger.info("")
    logger.info("="*60)
    logger.info("CRAWL SUMMARY")
    logger.info("="*60)

    # Post statistics
    logger.info("\nPost Statistics:")
    logger.info(f"  Total posts scraped: {stats['total_posts_scraped']}")
    logger.info(f"  Total posts saved: {stats['total_posts_saved']}")
    logger.info(f"  Failed posts: {stats['failed_posts']}")

    # Comment statistics
    logger.info("\nComment Statistics:")
    logger.info(f"  Total comments: {stats['total_comments']}")
    logger.info(f"  Posts with 20+ comments: {stats['posts_with_20plus_comments']}")

    if stats['posts_with_20plus_comments'] > 0:
        logger.info(f"  ✓ 20+ comments requirement MET")
    else:
        logger.warning(f"  ✗ 20+ comments requirement NOT MET")

    # Media statistics
    logger.info("\nMedia Statistics:")
    logger.info(f"  Total images downloaded: {stats['total_images']}")
    logger.info(f"  Total audio files: {stats['total_audio']}")

    # Performance
    duration = stats['duration']
    minutes = int(duration // 60)
    seconds = int(duration % 60)
    avg_time = duration / stats['total_posts_scraped'] if stats['total_posts_scraped'] > 0 else 0

    logger.info("\nPerformance:")
    logger.info(f"  Total duration: {minutes}m {seconds}s")
    logger.info(f"  Average per post: {avg_time:.1f}s")

    logger.info("")
    logger.info("="*60)


def main():
    """
    Main entry point for the crawler
    """
    # Parse command-line arguments
    args = parse_arguments()

    # Setup logging
    logger = setup_logging(args.log_level)

    # Apply strict mode to runtime flags (fail fast)
    if args.strict:
        config.SKIP_ON_ERROR = False
        config.GRACEFUL_DEGRADATION = False
        config.SAVE_PARTIAL_DATA = False

    # Create necessary directories
    try:
        config.create_directories()
        logger.info("Created necessary directories")
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        sys.exit(1)

    # Print configuration
    print_configuration(args, logger)

    # Dry run - exit without crawling
    if args.dry_run:
        logger.info("Dry run mode - exiting without crawling")
        return 0

    # Run crawler
    try:
        stats = crawl_posts(args, logger)

        # Print summary
        print_summary(stats, logger)

        # Check if minimum requirements met
        if stats['posts_with_20plus_comments'] == 0:
            logger.warning("\n⚠ WARNING: No posts with 20+ comments found!")
            logger.warning("   Consider crawling more posts or different categories")

        if stats['total_posts_scraped'] < 100:
            logger.warning(f"\n⚠ WARNING: Only scraped {stats['total_posts_scraped']} posts (target: 100+)")

        logger.info("\n✓ Crawler completed successfully")
        return 0

    except KeyboardInterrupt:
        logger.warning("\n\nCrawler interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"\n\nCrawler failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nCrawler interrupted by user")
        sys.exit(130)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
