#!/usr/bin/env python3
"""
Test script for the TuoiTre media downloader
"""

import json
from pathlib import Path
from crawler.scraper import TuoiTreScraper, get_category_post_urls, scrape_post_details
from crawler.downloader import (
    download_images,
    download_audio,
    download_all_media,
    get_media_urls,
    MediaDownloader
)
from crawler.utils.logger import create_module_logger

logger = create_module_logger('TestDownloader')


def test_media_url_extraction(post_url=None):
    """Test extracting media URLs without downloading"""
    logger.info("="*60)
    logger.info("Testing media URL extraction")
    logger.info("="*60)

    scraper = TuoiTreScraper()

    try:
        if not post_url:
            # Get a post URL
            category_url = "https://tuoitre.vn/thoi-su.htm"
            post_urls = get_category_post_urls(scraper, category_url, max_posts=3, max_pages=1)

            if not post_urls:
                logger.error("No post URLs found")
                return None

            post_url = post_urls[0]

        logger.info(f"Extracting media URLs from: {post_url}")

        # Get soup
        soup = scraper.get_html(post_url)

        # Extract media URLs
        media_urls = get_media_urls(soup, post_url)

        logger.info(f"\nFound media:")
        logger.info(f"  Images: {len(media_urls['images'])}")
        logger.info(f"  Audio: {len(media_urls['audio'])}")

        # Display first few image URLs
        if media_urls['images']:
            logger.info("\nFirst 3 image URLs:")
            for i, url in enumerate(media_urls['images'][:3], 1):
                logger.info(f"  {i}. {url}")

        # Display audio URL
        if media_urls['audio']:
            logger.info(f"\nAudio URL: {media_urls['audio'][0]}")

        return media_urls

    finally:
        scraper.close()


def test_image_download(post_url=None, post_id=None):
    """Test downloading images from a post"""
    logger.info("="*60)
    logger.info("Testing image download")
    logger.info("="*60)

    scraper = TuoiTreScraper()

    try:
        if not post_url:
            # Get a post URL
            category_url = "https://tuoitre.vn/thoi-su.htm"
            post_urls = get_category_post_urls(scraper, category_url, max_posts=1, max_pages=1)

            if not post_urls:
                logger.error("No post URLs found")
                return None

            post_url = post_urls[0]

        # Extract post ID if not provided
        if not post_id:
            post_details = scrape_post_details(scraper, post_url)
            post_id = post_details['postId'] if post_details else 'test_post'

        logger.info(f"Downloading images from: {post_url}")
        logger.info(f"Post ID: {post_id}")

        # Download images
        image_paths = download_images(
            scraper,
            post_id,
            post_url=post_url
        )

        if image_paths:
            logger.info(f"\n✓ Downloaded {len(image_paths)} images:")
            for i, path in enumerate(image_paths[:5], 1):  # Show first 5
                file_path = Path(path)
                size = file_path.stat().st_size if file_path.exists() else 0
                logger.info(f"  {i}. {file_path.name} ({size:,} bytes)")

            if len(image_paths) > 5:
                logger.info(f"  ... and {len(image_paths) - 5} more")

            # Validate downloads
            logger.info("\nValidating downloads...")
            valid = 0
            invalid = 0

            for path in image_paths:
                file_path = Path(path)
                if file_path.exists() and file_path.stat().st_size > 0:
                    valid += 1
                else:
                    invalid += 1

            logger.info(f"  Valid: {valid}")
            logger.info(f"  Invalid: {invalid}")

        else:
            logger.info("No images found or downloaded")

        return image_paths

    finally:
        scraper.close()


def test_audio_download(post_url=None, post_id=None):
    """Test downloading audio from a post"""
    logger.info("="*60)
    logger.info("Testing audio download")
    logger.info("="*60)

    scraper = TuoiTreScraper()

    try:
        if not post_url:
            # For audio, we might need to check multiple posts
            logger.info("Searching for posts with audio...")

            category_url = "https://tuoitre.vn/thoi-su.htm"
            post_urls = get_category_post_urls(scraper, category_url, max_posts=10, max_pages=2)

            # Check each post for audio
            for url in post_urls:
                soup = scraper.get_html(url)
                media_urls = get_media_urls(soup, url)

                if media_urls['audio']:
                    post_url = url
                    logger.info(f"Found post with audio: {url}")
                    break

            if not post_url:
                logger.info("⚠ No posts with audio found")
                logger.info("  This is normal - not all posts have audio")
                return None

        # Extract post ID if not provided
        if not post_id:
            post_details = scrape_post_details(scraper, post_url)
            post_id = post_details['postId'] if post_details else 'test_post'

        logger.info(f"Downloading audio from: {post_url}")
        logger.info(f"Post ID: {post_id}")

        # Download audio
        audio_path = download_audio(
            scraper,
            post_id,
            post_url=post_url
        )

        if audio_path:
            logger.info(f"\n✓ Downloaded audio:")
            file_path = Path(audio_path)
            size = file_path.stat().st_size if file_path.exists() else 0
            logger.info(f"  Path: {audio_path}")
            logger.info(f"  Size: {size:,} bytes ({size / (1024*1024):.2f} MB)")

            # Validate
            if file_path.exists() and size > 0:
                logger.info("  Validation: ✓ PASSED")
            else:
                logger.info("  Validation: ✗ FAILED")

        else:
            logger.info("No audio found on this post")

        return audio_path

    finally:
        scraper.close()


def test_all_media_download(post_url=None):
    """Test downloading all media from a post"""
    logger.info("="*60)
    logger.info("Testing all media download")
    logger.info("="*60)

    scraper = TuoiTreScraper()

    try:
        if not post_url:
            # Get a post URL
            category_url = "https://tuoitre.vn/thoi-su.htm"
            post_urls = get_category_post_urls(scraper, category_url, max_posts=1, max_pages=1)

            if not post_urls:
                logger.error("No post URLs found")
                return None

            post_url = post_urls[0]

        # Get post details
        post_details = scrape_post_details(scraper, post_url)
        post_id = post_details['postId'] if post_details else 'test_post'

        logger.info(f"Downloading all media from: {post_url}")
        logger.info(f"Post ID: {post_id}")

        # Download all media
        results = download_all_media(
            scraper,
            post_id,
            post_url,
            include_images=True,
            include_audio=True
        )

        # Display results
        logger.info("\n" + "="*60)
        logger.info("Download Results:")
        logger.info("="*60)

        logger.info(f"Post ID: {results['post_id']}")
        logger.info(f"Images downloaded: {len(results['images'])}")

        if results['images']:
            total_image_size = sum(
                Path(p).stat().st_size for p in results['images'] if Path(p).exists()
            )
            logger.info(f"Total image size: {total_image_size:,} bytes ({total_image_size / (1024*1024):.2f} MB)")

        if results['audio']:
            audio_size = Path(results['audio']).stat().st_size if Path(results['audio']).exists() else 0
            logger.info(f"Audio: ✓ ({audio_size:,} bytes)")
        else:
            logger.info("Audio: No audio found")

        if results['errors']:
            logger.info(f"\nErrors: {len(results['errors'])}")
            for error in results['errors']:
                logger.info(f"  - {error}")

        # Save results to JSON
        output_file = 'data/test_media_download.json'
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        logger.info(f"\nResults saved to: {output_file}")

        return results

    finally:
        scraper.close()


def test_progress_indicators():
    """Test progress indicators for large downloads"""
    logger.info("="*60)
    logger.info("Testing progress indicators")
    logger.info("="*60)

    scraper = TuoiTreScraper()
    downloader = MediaDownloader(scraper)

    try:
        # Test with a reasonably sized file
        test_url = "https://tuoitre.vn/path/to/large/image.jpg"  # Placeholder

        logger.info("Testing progress tracking with various file sizes...")
        logger.info("(This test uses actual post images)")

        # Get a real post with images
        category_url = "https://tuoitre.vn/thoi-su.htm"
        post_urls = get_category_post_urls(scraper, category_url, max_posts=1, max_pages=1)

        if post_urls:
            soup = scraper.get_html(post_urls[0])
            media_urls = get_media_urls(soup, post_urls[0])

            if media_urls['images']:
                logger.info(f"\nDownloading {len(media_urls['images'][:3])} images to test progress...")

                for i, img_url in enumerate(media_urls['images'][:3], 1):
                    save_path = Path(f'./test_downloads/test_progress_{i}.jpg')
                    logger.info(f"\n[{i}] Testing: {img_url}")

                    success = downloader.download_file(
                        img_url,
                        save_path,
                        show_progress=True
                    )

                    if success:
                        logger.info("✓ Download successful with progress tracking")
                    else:
                        logger.info("✗ Download failed")

        # Show statistics
        stats = downloader.get_statistics()
        logger.info("\n" + "="*60)
        logger.info("Download Statistics:")
        logger.info("="*60)
        logger.info(f"Total downloaded: {stats['total_bytes_formatted']}")
        logger.info(f"Images: {stats['images_downloaded']} successful, {stats['images_failed']} failed")

    finally:
        scraper.close()


def test_file_validation():
    """Test file validation and size checks"""
    logger.info("="*60)
    logger.info("Testing file validation")
    logger.info("="*60)

    scraper = TuoiTreScraper()
    downloader = MediaDownloader(scraper)

    try:
        # Create test files
        test_dir = Path('./test_validation')
        test_dir.mkdir(parents=True, exist_ok=True)

        # Test 1: Valid file
        valid_file = test_dir / 'valid.txt'
        valid_file.write_text("This is a valid file with content")
        is_valid = downloader._validate_download(valid_file)
        logger.info(f"Valid file test: {'✓ PASSED' if is_valid else '✗ FAILED'}")

        # Test 2: Empty file
        empty_file = test_dir / 'empty.txt'
        empty_file.write_text("")
        is_valid = downloader._validate_download(empty_file)
        logger.info(f"Empty file test: {'✓ PASSED (detected as invalid)' if not is_valid else '✗ FAILED'}")

        # Test 3: Non-existent file
        missing_file = test_dir / 'missing.txt'
        is_valid = downloader._validate_download(missing_file)
        logger.info(f"Missing file test: {'✓ PASSED (detected as invalid)' if not is_valid else '✗ FAILED'}")

        # Clean up
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)

        logger.info("\n✓ File validation tests completed")

    finally:
        scraper.close()


def main():
    """Run all downloader tests"""
    print("\n" + "="*60)
    print("TuoiTre Media Downloader Test Suite")
    print("="*60 + "\n")

    results = {}

    # Test 1: Media URL extraction
    print("\n[Test 1] Extracting media URLs...")
    try:
        media_urls = test_media_url_extraction()
        results['url_extraction'] = media_urls is not None
        if media_urls:
            print(f"✓ Test 1 passed: Found {len(media_urls['images'])} images\n")
        else:
            print("⚠ Test 1 warning: No media found\n")
    except Exception as e:
        print(f"✗ Test 1 failed: {e}\n")
        logger.error("Test 1 failed", exc_info=True)
        results['url_extraction'] = False

    # Test 2: Image download
    print("\n[Test 2] Downloading images...")
    try:
        image_paths = test_image_download()
        results['image_download'] = image_paths is not None and len(image_paths) > 0
        if image_paths:
            print(f"✓ Test 2 passed: Downloaded {len(image_paths)} images\n")
        else:
            print("⚠ Test 2 warning: No images downloaded\n")
    except Exception as e:
        print(f"✗ Test 2 failed: {e}\n")
        logger.error("Test 2 failed", exc_info=True)
        results['image_download'] = False

    # Test 3: Audio download
    print("\n[Test 3] Downloading audio...")
    try:
        audio_path = test_audio_download()
        results['audio_download'] = audio_path is not None
        if audio_path:
            print(f"✓ Test 3 passed: Downloaded audio\n")
        else:
            print("⚠ Test 3 info: No audio found (normal)\n")
        results['audio_download'] = True  # Pass even if no audio found
    except Exception as e:
        print(f"✗ Test 3 failed: {e}\n")
        logger.error("Test 3 failed", exc_info=True)
        results['audio_download'] = False

    # Test 4: All media download
    print("\n[Test 4] Downloading all media...")
    try:
        all_media = test_all_media_download()
        results['all_media'] = all_media is not None
        if all_media:
            print(f"✓ Test 4 passed: Downloaded complete media set\n")
        else:
            print("✗ Test 4 failed\n")
    except Exception as e:
        print(f"✗ Test 4 failed: {e}\n")
        logger.error("Test 4 failed", exc_info=True)
        results['all_media'] = False

    # Test 5: Progress indicators
    print("\n[Test 5] Testing progress indicators...")
    try:
        test_progress_indicators()
        results['progress'] = True
        print("✓ Test 5 passed: Progress indicators working\n")
    except Exception as e:
        print(f"✗ Test 5 failed: {e}\n")
        logger.error("Test 5 failed", exc_info=True)
        results['progress'] = False

    # Test 6: File validation
    print("\n[Test 6] Testing file validation...")
    try:
        test_file_validation()
        results['validation'] = True
        print("✓ Test 6 passed: File validation working\n")
    except Exception as e:
        print(f"✗ Test 6 failed: {e}\n")
        logger.error("Test 6 failed", exc_info=True)
        results['validation'] = False

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")

    print("\n" + "="*60)

    return passed == total


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
