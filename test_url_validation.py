#!/usr/bin/env python3
"""
Test script for URL validation against disallowed paths
"""

import config

# Try to import _is_valid_article_url, but don't fail if dependencies are missing
try:
    from crawler.scraper import _is_valid_article_url
    SCRAPER_AVAILABLE = True
except ImportError as e:
    print(f"Note: Could not import scraper module ({e})")
    print("Will test only config.is_url_allowed()\n")
    SCRAPER_AVAILABLE = False
    _is_valid_article_url = None


def test_url_validation():
    """Test URL validation with disallowed paths"""
    print("="*60)
    print("URL Validation Test")
    print("="*60)
    print()

    # Test cases: (url, expected_result, description)
    test_cases = [
        # Valid article URLs
        ("https://tuoitre.vn/thoi-su/article-title-123456.htm", True, "Valid article URL"),
        ("https://tuoitre.vn/the-gioi/another-article-789012.htm", True, "Valid article in the-gioi"),
        ("https://tuoitre.vn/kinh-doanh/business-news-345678.htm", True, "Valid article in kinh-doanh"),

        # Disallowed paths - should be blocked
        ("https://tuoitre.vn/tim-kiem.htm?q=test", False, "Search page (tim-kiem.htm)"),
        ("https://tuoitre.vn/print/article-title-123456.htm", False, "Print version (/print/)"),
        ("https://tuoitre.vn/ImageView.aspx?id=123", False, "Image viewer (ImageView.aspx)"),
        ("https://tuoitre.vn/ajax-box-mua-sam/product-123.htm", False, "Shopping box AJAX (/ajax-box-mua-sam/)"),

        # Invalid article URLs
        ("https://tuoitre.vn/thoi-su.htm", False, "Category page (no article ID)"),
        ("https://tuoitre.vn/thoi-su-p2.htm", False, "Pagination page"),
        ("https://tuoitre.vn/tag/covid-19.htm", False, "Tag page"),
        ("https://tuoitre.vn/video/news-video.htm", False, "Video page"),
        ("https://example.com/article-123456.htm", False, "Not from tuoitre.vn"),
        ("", False, "Empty URL"),
        (None, False, "None URL"),

        # Edge cases
        ("https://tuoitre.vn/thoi-su/print/article-123456.htm", False, "Article with /print/ in path"),
        ("https://tuoitre.vn/thoi-su/tim-kiem.htm", False, "Path contains tim-kiem.htm"),
    ]

    passed = 0
    failed = 0

    print("Testing config.is_url_allowed():")
    print("-" * 60)

    for url, expected, description in test_cases:
        result = config.is_url_allowed(url)
        status = "✓ PASS" if result == expected else "✗ FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status} | {description}")
        print(f"       URL: {url}")
        print(f"       Expected: {expected}, Got: {result}")
        print()

    print()

    if SCRAPER_AVAILABLE:
        print("="*60)
        print("Testing _is_valid_article_url() (includes all validations):")
        print("-" * 60)

        for url, expected, description in test_cases:
            # For None, skip _is_valid_article_url test
            if url is None:
                continue

            result = _is_valid_article_url(url)
            status = "✓ PASS" if result == expected else "✗ FAIL"

            # Don't count this in overall stats since it's just a secondary check
            print(f"{status} | {description}")
            print(f"       URL: {url}")
            print(f"       Expected: {expected}, Got: {result}")
            print()
    else:
        print("Skipping _is_valid_article_url() tests (scraper module not available)")
        print()

    print()
    print("="*60)
    print(f"Summary: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("="*60)

    return failed == 0


def test_disallowed_paths_config():
    """Test that disallowed paths are configured correctly"""
    print("\n")
    print("="*60)
    print("Configuration Check: DISALLOWED_PATHS")
    print("="*60)
    print()

    expected_paths = [
        '/tim-kiem.htm',
        '/print/',
        '/ImageView.aspx',
        '/ajax-box-mua-sam/',
    ]

    print("Expected disallowed paths:")
    for path in expected_paths:
        print(f"  - {path}")

    print()
    print("Configured disallowed paths:")
    for path in config.DISALLOWED_PATHS:
        print(f"  - {path}")

    print()

    all_present = all(path in config.DISALLOWED_PATHS for path in expected_paths)

    if all_present:
        print("✓ All expected paths are configured")
        return True
    else:
        print("✗ Some expected paths are missing")
        missing = [p for p in expected_paths if p not in config.DISALLOWED_PATHS]
        print(f"  Missing: {missing}")
        return False


def main():
    """Run all validation tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "URL VALIDATION TEST SUITE" + " "*18 + "║")
    print("╚" + "="*58 + "╝")
    print()

    # Test 1: Check configuration
    config_ok = test_disallowed_paths_config()

    # Test 2: Validate URLs
    validation_ok = test_url_validation()

    print()
    print("="*60)
    if config_ok and validation_ok:
        print("✓ ALL TESTS PASSED")
        print("="*60)
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("="*60)
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
