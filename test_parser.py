#!/usr/bin/env python3
"""
Test script for the TuoiTre comment parser
"""

import json
from crawler.scraper import TuoiTreScraper, get_category_post_urls
from crawler.parser import (
    extract_comments,
    validate_comment_count,
    find_posts_with_comments,
    get_comment_statistics
)
from crawler.utils.logger import create_module_logger

logger = create_module_logger('TestParser')


def print_comment_tree(comments, indent=0, max_depth=3):
    """
    Print comment tree structure for visualization

    Args:
        comments: List of comment dictionaries
        indent: Current indentation level
        max_depth: Maximum depth to display
    """
    if indent > max_depth:
        return

    for i, comment in enumerate(comments, 1):
        prefix = "  " * indent + "├─"
        author = comment.get('author', 'Unknown')
        text = comment.get('text', '')[:60]
        reactions = comment.get('vote_react_list', {})
        reaction_str = ', '.join([f"{k}:{v}" for k, v in reactions.items()]) if reactions else 'no reactions'

        print(f"{prefix} [{i}] {author}: {text}... ({reaction_str})")

        if comment.get('replies'):
            print_comment_tree(comment['replies'], indent + 1, max_depth)


def test_extract_comments(post_url=None):
    """Test extracting comments from a post"""
    logger.info("="*60)
    logger.info("Testing extract_comments")
    logger.info("="*60)

    scraper = TuoiTreScraper()

    try:
        if not post_url:
            # Get a post URL from a category
            logger.info("Fetching post URLs to find one with comments...")
            category_url = "https://tuoitre.vn/thoi-su.htm"
            post_urls = get_category_post_urls(scraper, category_url, max_posts=5, max_pages=1)

            if not post_urls:
                logger.error("No post URLs found")
                return None

            post_url = post_urls[0]

        logger.info(f"Extracting comments from: {post_url}")

        # Extract comments
        comments = extract_comments(scraper, post_url)

        if not comments:
            logger.warning("No comments found on this post")
            return None

        logger.info(f"✓ Extracted {len(comments)} top-level comments")

        # Display first few comments
        logger.info("\nComment structure preview:")
        print_comment_tree(comments[:3], max_depth=2)

        # Get statistics
        stats = get_comment_statistics(comments)
        logger.info("\n" + "="*60)
        logger.info("Comment Statistics:")
        logger.info("="*60)
        logger.info(f"Total comments: {stats['total_comments']}")
        logger.info(f"Top-level comments: {stats['top_level_comments']}")
        logger.info(f"Max nesting depth: {stats['max_depth']}")
        logger.info(f"Comments with reactions: {stats['comments_with_reactions']}")
        logger.info(f"Avg replies per comment: {stats['average_replies_per_comment']:.2f}")
        logger.info("\nDepth distribution:")
        for depth, count in sorted(stats['depth_distribution'].items()):
            logger.info(f"  Depth {depth}: {count} comments")

        # Validate comment count
        logger.info("\n" + "="*60)
        is_valid = validate_comment_count(comments, min_required=20)

        if is_valid:
            logger.info("✓ This post meets the 20+ comments requirement")
        else:
            logger.info("✗ This post does not meet the 20+ comments requirement")

        # Save sample to JSON
        output_file = 'data/test_comments.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'post_url': post_url,
                'total_comments': stats['total_comments'],
                'statistics': stats,
                'comments': comments[:3]  # Save only first 3 for brevity
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"\nSample comments saved to: {output_file}")

        return comments

    finally:
        scraper.close()


def test_find_posts_with_comments():
    """Test finding posts with minimum comment count"""
    logger.info("="*60)
    logger.info("Testing find_posts_with_comments")
    logger.info("="*60)

    scraper = TuoiTreScraper()

    try:
        # Get some post URLs
        logger.info("Fetching post URLs...")
        category_url = "https://tuoitre.vn/thoi-su.htm"
        post_urls = get_category_post_urls(scraper, category_url, max_posts=10, max_pages=2)

        if not post_urls:
            logger.error("No post URLs found")
            return

        logger.info(f"Found {len(post_urls)} post URLs")
        logger.info("\nSearching for posts with 20+ comments...\n")

        # Find posts with at least 20 comments
        posts_with_comments, comment_counts = find_posts_with_comments(
            scraper,
            post_urls,
            min_comments=20
        )

        logger.info("\n" + "="*60)
        logger.info("Results:")
        logger.info("="*60)

        if posts_with_comments:
            logger.info(f"✓ Found {len(posts_with_comments)} post(s) with 20+ comments:")
            for url in posts_with_comments:
                logger.info(f"  - {url}")
        else:
            logger.info("✗ No posts found with 20+ comments")
            logger.info("  Try checking more posts or different categories")

        # Show comment count distribution
        if comment_counts:
            logger.info("\nComment count distribution:")
            for i, count in enumerate(comment_counts, 1):
                status = "✓" if count >= 20 else " "
                logger.info(f"  {status} Post {i}: {count} comments")

        return posts_with_comments

    finally:
        scraper.close()


def test_nested_replies():
    """Test that nested replies are properly extracted"""
    logger.info("="*60)
    logger.info("Testing Nested Reply Extraction")
    logger.info("="*60)

    scraper = TuoiTreScraper()

    try:
        # This test requires finding a post with nested comments
        logger.info("Looking for posts with nested comment threads...")

        category_url = "https://tuoitre.vn/thoi-su.htm"
        post_urls = get_category_post_urls(scraper, category_url, max_posts=5, max_pages=1)

        max_nesting_depth = 0
        post_with_nested = None

        for post_url in post_urls:
            logger.info(f"\nChecking: {post_url}")
            comments = extract_comments(scraper, post_url)

            if comments:
                stats = get_comment_statistics(comments)
                depth = stats['max_depth']

                logger.info(f"  Max depth: {depth}")

                if depth > max_nesting_depth:
                    max_nesting_depth = depth
                    post_with_nested = post_url

        logger.info("\n" + "="*60)
        if max_nesting_depth > 0:
            logger.info(f"✓ Found nested comments with max depth: {max_nesting_depth}")
            logger.info(f"  Post: {post_with_nested}")
        else:
            logger.info("✗ No nested comments found in checked posts")

        return max_nesting_depth > 0

    finally:
        scraper.close()


def test_comment_reactions():
    """Test extraction of comment vote reactions"""
    logger.info("="*60)
    logger.info("Testing Comment Reaction Extraction")
    logger.info("="*60)

    scraper = TuoiTreScraper()

    try:
        # Get comments from a post
        category_url = "https://tuoitre.vn/thoi-su.htm"
        post_urls = get_category_post_urls(scraper, category_url, max_posts=3, max_pages=1)

        comments_with_reactions = 0
        total_comments_checked = 0

        for post_url in post_urls:
            logger.info(f"\nChecking reactions on: {post_url}")
            comments = extract_comments(scraper, post_url)

            def count_reactions_recursive(comment_list):
                nonlocal comments_with_reactions, total_comments_checked
                for comment in comment_list:
                    total_comments_checked += 1
                    if comment.get('vote_react_list'):
                        comments_with_reactions += 1

                    if comment.get('replies'):
                        count_reactions_recursive(comment['replies'])

            count_reactions_recursive(comments)

        logger.info("\n" + "="*60)
        logger.info(f"Total comments checked: {total_comments_checked}")
        logger.info(f"Comments with reactions: {comments_with_reactions}")

        if comments_with_reactions > 0:
            percentage = (comments_with_reactions / total_comments_checked) * 100
            logger.info(f"✓ {percentage:.1f}% of comments have reactions")
        else:
            logger.info("✗ No comment reactions found")
            logger.info("  (This is normal if the site doesn't show comment reactions)")

        return comments_with_reactions > 0

    finally:
        scraper.close()


def main():
    """Run all parser tests"""
    print("\n" + "="*60)
    print("TuoiTre Comment Parser Test Suite")
    print("="*60 + "\n")

    results = {}

    # Test 1: Extract comments
    print("\n[Test 1] Extracting comments from a post...")
    try:
        comments = test_extract_comments()
        results['extract_comments'] = comments is not None
        if comments:
            print(f"✓ Test 1 passed: Extracted {len(comments)} top-level comments\n")
        else:
            print("⚠ Test 1 warning: No comments found (may be normal)\n")
    except Exception as e:
        print(f"✗ Test 1 failed: {e}\n")
        logger.error("Test 1 failed", exc_info=True)
        results['extract_comments'] = False

    # Test 2: Find posts with 20+ comments
    print("\n[Test 2] Finding posts with 20+ comments...")
    try:
        posts_with_comments = test_find_posts_with_comments()
        results['find_posts'] = len(posts_with_comments) > 0 if posts_with_comments else False

        if results['find_posts']:
            print(f"✓ Test 2 passed: Found post(s) with 20+ comments\n")
        else:
            print("⚠ Test 2 warning: No posts with 20+ comments found\n")
            print("   Try running again or checking more posts\n")
    except Exception as e:
        print(f"✗ Test 2 failed: {e}\n")
        logger.error("Test 2 failed", exc_info=True)
        results['find_posts'] = False

    # Test 3: Nested replies
    print("\n[Test 3] Testing nested reply extraction...")
    try:
        has_nested = test_nested_replies()
        results['nested_replies'] = has_nested

        if has_nested:
            print("✓ Test 3 passed: Found and extracted nested replies\n")
        else:
            print("⚠ Test 3 warning: No nested replies found\n")
    except Exception as e:
        print(f"✗ Test 3 failed: {e}\n")
        logger.error("Test 3 failed", exc_info=True)
        results['nested_replies'] = False

    # Test 4: Comment reactions
    print("\n[Test 4] Testing comment reaction extraction...")
    try:
        has_reactions = test_comment_reactions()
        results['reactions'] = has_reactions

        if has_reactions:
            print("✓ Test 4 passed: Found comment reactions\n")
        else:
            print("⚠ Test 4 info: No comment reactions found\n")
            print("   (Normal if site doesn't display comment reactions)\n")
    except Exception as e:
        print(f"✗ Test 4 failed: {e}\n")
        logger.error("Test 4 failed", exc_info=True)
        results['reactions'] = False

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL/WARN"
        print(f"  {status}: {test_name}")

    print("\n" + "="*60)

    # Return success if at least extract_comments works
    return results.get('extract_comments', False)


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
