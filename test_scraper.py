#!/usr/bin/env python3
"""
Test script for the TuoiTre scraper
"""

import json
from crawler.scraper import (
    TuoiTreScraper,
    get_category_post_urls,
    scrape_post_details,
    extract_vote_reactions
)
from crawler.utils.logger import create_module_logger

logger = create_module_logger('TestScraper')


def test_get_post_urls():
    """Test fetching post URLs from a category"""
    logger.info("="*60)
    logger.info("Testing get_category_post_urls")
    logger.info("="*60)

    scraper = TuoiTreScraper()

    try:
        # Test with a single category
        category_url = "https://tuoitre.vn/thoi-su.htm"
        post_urls = get_category_post_urls(
            scraper,
            category_url,
            max_posts=5,  # Get only 5 posts for testing
            max_pages=2
        )

        logger.info(f"Found {len(post_urls)} post URLs")
        for i, url in enumerate(post_urls, 1):
            logger.info(f"{i}. {url}")

        return post_urls

    finally:
        scraper.close()


def test_scrape_post(post_url: str = None):
    """Test scraping a single post"""
    logger.info("="*60)
    logger.info("Testing scrape_post_details")
    logger.info("="*60)

    scraper = TuoiTreScraper()

    try:
        if not post_url:
            # Get a post URL first
            category_url = "https://tuoitre.vn/thoi-su.htm"
            post_urls = get_category_post_urls(scraper, category_url, max_posts=1, max_pages=1)
            if post_urls:
                post_url = post_urls[0]
            else:
                logger.error("No post URLs found")
                return

        logger.info(f"Scraping post: {post_url}")

        post_details = scrape_post_details(scraper, post_url)

        if post_details:
            logger.info("Post details scraped successfully:")
            logger.info(f"  ID: {post_details.get('postId')}")
            logger.info(f"  Title: {post_details.get('title')}")
            logger.info(f"  Author: {post_details.get('author')}")
            logger.info(f"  Date: {post_details.get('publishDate')}")
            logger.info(f"  Category: {post_details.get('category')}")
            logger.info(f"  Content length: {len(post_details.get('content', {}).get('text', ''))} chars")
            logger.info(f"  Tags: {post_details.get('tags')}")

            # Save to JSON for inspection
            with open('data/test_post.json', 'w', encoding='utf-8') as f:
                json.dump(post_details, f, ensure_ascii=False, indent=2)
            logger.info("Post details saved to data/test_post.json")

            return post_details
        else:
            logger.error("Failed to scrape post details")

    finally:
        scraper.close()


def test_extract_reactions(post_url: str = None):
    """Test extracting vote reactions"""
    logger.info("="*60)
    logger.info("Testing extract_vote_reactions")
    logger.info("="*60)

    scraper = TuoiTreScraper()

    try:
        if not post_url:
            # Get a post URL first
            category_url = "https://tuoitre.vn/thoi-su.htm"
            post_urls = get_category_post_urls(scraper, category_url, max_posts=1, max_pages=1)
            if post_urls:
                post_url = post_urls[0]
            else:
                logger.error("No post URLs found")
                return

        logger.info(f"Extracting reactions from: {post_url}")

        reactions = extract_vote_reactions(scraper, post_url)

        if reactions:
            logger.info("Reactions found:")
            for reaction_type, count in reactions.items():
                logger.info(f"  {reaction_type}: {count}")
        else:
            logger.info("No reactions found (this is normal if the page doesn't have reactions)")

        return reactions

    finally:
        scraper.close()


def main():
    """Run all tests"""
    import sys

    print("\n" + "="*60)
    print("TuoiTre Scraper Test Suite")
    print("="*60 + "\n")

    # Test 1: Get post URLs
    print("\n[Test 1] Fetching post URLs from category page...")
    try:
        post_urls = test_get_post_urls()
        print(f"✓ Test 1 passed: Found {len(post_urls)} post URLs\n")
    except Exception as e:
        print(f"✗ Test 1 failed: {e}\n")
        logger.error("Test 1 failed", exc_info=True)
        return 1

    # Test 2: Scrape post details
    if post_urls:
        print("\n[Test 2] Scraping post details...")
        try:
            post_details = test_scrape_post(post_urls[0])
            if post_details:
                print(f"✓ Test 2 passed: Scraped post '{post_details.get('title', '')[:50]}...'\n")
            else:
                print("✗ Test 2 failed: No post details returned\n")
                return 1
        except Exception as e:
            print(f"✗ Test 2 failed: {e}\n")
            logger.error("Test 2 failed", exc_info=True)
            return 1

        # Test 3: Extract reactions
        print("\n[Test 3] Extracting vote reactions...")
        try:
            reactions = test_extract_reactions(post_urls[0])
            print(f"✓ Test 3 passed: Found {len(reactions)} reaction types\n")
        except Exception as e:
            print(f"✗ Test 3 failed: {e}\n")
            logger.error("Test 3 failed", exc_info=True)
            return 1

    print("\n" + "="*60)
    print("All tests completed successfully!")
    print("="*60 + "\n")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
