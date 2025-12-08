#!/usr/bin/env python3
"""
Test script for the JSON exporter
"""

import json
from pathlib import Path
import shutil
from crawler.json_exporter import (
    save_post_json,
    validate_post_data,
    format_post_data,
    save_multiple_posts,
    save_combined_json,
    load_post_json,
    get_export_summary,
    validate_json_file,
    check_encoding_issues
)
from crawler.utils.logger import create_module_logger

logger = create_module_logger('TestJSONExporter')


def create_sample_post_data():
    """Create sample post data with Vietnamese text"""
    return {
        'postId': '123456',
        'title': 'Tin tức về kinh tế Việt Nam năm 2024',
        'content': {
            'text': 'Đây là nội dung bài viết về kinh tế. Việt Nam đang phát triển mạnh mẽ.',
            'html': '<p>Đây là nội dung bài viết về kinh tế. <strong>Việt Nam</strong> đang phát triển mạnh mẽ.</p>'
        },
        'author': 'Nguyễn Văn A',
        'date': '2024-12-08T10:30:00',
        'category': 'kinh-doanh',
        'audio_url': 'https://example.com/audio/123456.mp3',
        'vote_reactions': {
            'like': 150,
            'love': 45,
            'haha': 10
        },
        'comments': [
            {
                'commentId': 'comment_1',
                'author': 'Trần Thị B',
                'text': 'Bài viết rất hay và bổ ích!',
                'date': '2024-12-08T11:00:00',
                'vote_react_list': {'like': 25},
                'depth': 0,
                'replies': [
                    {
                        'commentId': 'comment_1_1',
                        'author': 'Lê Văn C',
                        'text': 'Tôi hoàn toàn đồng ý!',
                        'date': '2024-12-08T11:30:00',
                        'vote_react_list': {'like': 10},
                        'depth': 1,
                        'replies': []
                    }
                ]
            },
            {
                'commentId': 'comment_2',
                'author': 'Phạm Thị D',
                'text': 'Cảm ơn tác giả đã chia sẻ!',
                'date': '2024-12-08T12:00:00',
                'vote_react_list': {'like': 30, 'love': 5},
                'depth': 0,
                'replies': []
            }
        ]
    }


def test_validation():
    """Test post data validation"""
    logger.info("="*60)
    logger.info("Testing post data validation")
    logger.info("="*60)

    # Test 1: Valid data
    logger.info("\nTest 1: Valid post data")
    valid_data = create_sample_post_data()
    is_valid, errors = validate_post_data(valid_data)

    if is_valid:
        logger.info("✓ Valid data passed validation")
    else:
        logger.error(f"✗ Valid data failed validation: {errors}")

    # Test 2: Missing required field
    logger.info("\nTest 2: Missing required field (postId)")
    invalid_data = create_sample_post_data()
    del invalid_data['postId']
    is_valid, errors = validate_post_data(invalid_data)

    if not is_valid and 'postId' in str(errors):
        logger.info(f"✓ Correctly detected missing postId: {errors[0]}")
    else:
        logger.error("✗ Failed to detect missing postId")

    # Test 3: Invalid field type
    logger.info("\nTest 3: Invalid field type")
    invalid_data = create_sample_post_data()
    invalid_data['comments'] = "not a list"  # Should be list
    is_valid, errors = validate_post_data(invalid_data)

    if not is_valid and 'list' in str(errors):
        logger.info(f"✓ Correctly detected invalid type: {errors[0]}")
    else:
        logger.error("✗ Failed to detect invalid type")

    # Test 4: Nested comment validation
    logger.info("\nTest 4: Nested comment validation")
    invalid_data = create_sample_post_data()
    invalid_data['comments'][0]['replies'][0]['commentId'] = 123  # Should be string
    is_valid, errors = validate_post_data(invalid_data)

    if not is_valid:
        logger.info(f"✓ Correctly detected nested comment issue")
    else:
        logger.error("✗ Failed to detect nested comment issue")

    logger.info("\n" + "="*60)


def test_encoding():
    """Test UTF-8 encoding for Vietnamese text"""
    logger.info("="*60)
    logger.info("Testing UTF-8 encoding")
    logger.info("="*60)

    # Create test data with various Vietnamese characters
    test_data = {
        'postId': 'test_encoding',
        'title': 'Tiếng Việt: àáảãạ ăắằẳẵặ âấầẩẫậ đ èéẻẽẹ êếềểễệ',
        'content': {
            'text': 'Test các ký tự: ìíỉĩị òóỏõọ ôốồổỗộ ơớờởỡợ ùúủũụ ưứừửữự ỳýỷỹỵ',
            'html': '<p>HTML với tiếng Việt: <strong>Việt Nam</strong></p>'
        },
        'author': 'Nguyễn Văn Đức',
        'date': '2024-12-08T10:00:00',
        'category': 'test',
        'audio_url': None,
        'vote_reactions': {},
        'comments': []
    }

    # Check for encoding issues
    logger.info("\nChecking for encoding issues...")
    issues = check_encoding_issues(test_data)

    if not issues:
        logger.info("✓ No encoding issues detected")
    else:
        logger.warning(f"⚠ Encoding issues found: {issues}")

    # Save and reload to test encoding
    test_dir = Path('./test_json_output')
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        file_path = save_post_json(test_data, output_dir=test_dir)
        logger.info(f"\n✓ Saved test file: {file_path}")

        # Load and verify
        loaded_data = load_post_json(file_path)

        # Check if Vietnamese characters are preserved
        if loaded_data['title'] == test_data['title']:
            logger.info("✓ Vietnamese characters preserved correctly")
        else:
            logger.error("✗ Vietnamese characters corrupted")

        # Verify file is valid UTF-8
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.info(f"✓ File is valid UTF-8 ({len(content)} chars)")

    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

    logger.info("\n" + "="*60)


def test_save_single_post():
    """Test saving a single post"""
    logger.info("="*60)
    logger.info("Testing single post save")
    logger.info("="*60)

    test_dir = Path('./test_json_output')
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create sample data
        post_data = create_sample_post_data()

        # Save with validation
        logger.info("\nSaving post with validation...")
        file_path = save_post_json(
            post_data,
            output_dir=test_dir,
            validate=True,
            include_metadata=True
        )

        logger.info(f"✓ Saved to: {file_path}")
        logger.info(f"  Size: {file_path.stat().st_size} bytes")

        # Verify file exists
        if file_path.exists():
            logger.info("✓ File exists")
        else:
            logger.error("✗ File does not exist")

        # Verify file size > 0
        if file_path.stat().st_size > 0:
            logger.info(f"✓ File has content ({file_path.stat().st_size} bytes)")
        else:
            logger.error("✗ File is empty")

        # Load and verify
        loaded_data = load_post_json(file_path)

        if loaded_data['postId'] == post_data['postId']:
            logger.info("✓ Data loaded correctly")
        else:
            logger.error("✗ Data mismatch")

        # Check metadata was added
        if 'metadata' in loaded_data:
            logger.info("✓ Metadata included")
            logger.info(f"  Crawled at: {loaded_data['metadata'].get('crawled_at')}")
        else:
            logger.warning("⚠ Metadata not included")

        # Display JSON structure
        logger.info("\nJSON structure preview:")
        preview = json.dumps(loaded_data, ensure_ascii=False, indent=2)
        lines = preview.split('\n')
        for line in lines[:20]:  # Show first 20 lines
            logger.info(f"  {line}")
        if len(lines) > 20:
            logger.info(f"  ... ({len(lines) - 20} more lines)")

    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

    logger.info("\n" + "="*60)


def test_save_multiple_posts():
    """Test saving multiple posts"""
    logger.info("="*60)
    logger.info("Testing multiple post save")
    logger.info("="*60)

    test_dir = Path('./test_json_output')
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create multiple posts
        posts = []
        for i in range(5):
            post = create_sample_post_data()
            post['postId'] = f'post_{i+1}'
            post['title'] = f'Bài viết số {i+1}: {post["title"]}'
            posts.append(post)

        logger.info(f"\nSaving {len(posts)} posts...")

        # Save multiple posts
        saved_files = save_multiple_posts(posts, output_dir=test_dir)

        logger.info(f"✓ Saved {len(saved_files)} files:")
        for file_path in saved_files:
            logger.info(f"  - {file_path.name} ({file_path.stat().st_size} bytes)")

        # Verify all files exist
        all_exist = all(f.exists() for f in saved_files)
        if all_exist:
            logger.info("✓ All files exist")
        else:
            logger.error("✗ Some files missing")

    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

    logger.info("\n" + "="*60)


def test_combined_json():
    """Test saving posts in combined JSON file"""
    logger.info("="*60)
    logger.info("Testing combined JSON save")
    logger.info("="*60)

    test_dir = Path('./test_json_output')
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Create multiple posts
        posts = []
        for i in range(3):
            post = create_sample_post_data()
            post['postId'] = f'combined_{i+1}'
            post['title'] = f'Bài viết {i+1}'
            posts.append(post)

        logger.info(f"\nSaving {len(posts)} posts in combined file...")

        # Save combined
        output_file = test_dir / 'all_posts.json'
        file_path = save_combined_json(posts, output_file=output_file)

        logger.info(f"✓ Saved combined file: {file_path}")
        logger.info(f"  Size: {file_path.stat().st_size} bytes")

        # Load and verify
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'metadata' in data and 'posts' in data:
            logger.info("✓ Structure correct")
            logger.info(f"  Total posts in metadata: {data['metadata']['total_posts']}")
            logger.info(f"  Actual posts: {len(data['posts'])}")

            if data['metadata']['total_posts'] == len(data['posts']):
                logger.info("✓ Post count matches")
            else:
                logger.error("✗ Post count mismatch")
        else:
            logger.error("✗ Structure incorrect")

    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

    logger.info("\n" + "="*60)


def test_directory_creation():
    """Test automatic directory creation"""
    logger.info("="*60)
    logger.info("Testing directory creation")
    logger.info("="*60)

    test_dir = Path('./test_deeply/nested/directory/structure')

    try:
        # Directory should not exist initially
        if test_dir.exists():
            shutil.rmtree(test_dir.parents[3])

        logger.info(f"\nTesting creation of: {test_dir}")

        # Save post to non-existent directory
        post_data = create_sample_post_data()
        file_path = save_post_json(post_data, output_dir=test_dir)

        # Check directory was created
        if test_dir.exists() and test_dir.is_dir():
            logger.info("✓ Directory created successfully")
        else:
            logger.error("✗ Directory not created")

        # Check file was saved
        if file_path.exists():
            logger.info(f"✓ File saved: {file_path}")
        else:
            logger.error("✗ File not saved")

    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir.parents[3], ignore_errors=True)

    logger.info("\n" + "="*60)


def test_format_post_data():
    """Test formatting post data"""
    logger.info("="*60)
    logger.info("Testing post data formatting")
    logger.info("="*60)

    # Format post data using helper function
    formatted_data = format_post_data(
        post_id='789',
        title='Test Title with Vietnamese: Tiếng Việt',
        content='Content text',
        author='Test Author',
        date='2024-12-08',
        category='test-category',
        audio_url='https://example.com/audio.mp3',
        vote_reactions={'like': 100},
        comments=[],
        custom_field='custom_value'  # Extra field
    )

    logger.info("\nFormatted data:")
    logger.info(f"  postId: {formatted_data['postId']}")
    logger.info(f"  title: {formatted_data['title']}")
    logger.info(f"  content: {formatted_data['content']}")
    logger.info(f"  custom_field: {formatted_data.get('custom_field')}")

    # Validate
    is_valid, errors = validate_post_data(formatted_data)

    if is_valid:
        logger.info("\n✓ Formatted data is valid")
    else:
        logger.error(f"\n✗ Formatted data is invalid: {errors}")

    logger.info("\n" + "="*60)


def test_export_summary():
    """Test export summary function"""
    logger.info("="*60)
    logger.info("Testing export summary")
    logger.info("="*60)

    test_dir = Path('./test_json_output')
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Save some test files
        for i in range(3):
            post = create_sample_post_data()
            post['postId'] = f'summary_test_{i+1}'
            save_post_json(post, output_dir=test_dir)

        # Get summary
        summary = get_export_summary(test_dir)

        logger.info(f"\nExport Summary:")
        logger.info(f"  Total files: {summary['total_files']}")
        logger.info(f"  Total size: {summary['total_size_formatted']}")
        logger.info(f"\nFiles:")
        for file_info in summary['files']:
            logger.info(f"  - {file_info['name']} ({file_info['size']} bytes)")

        if summary['total_files'] == 3:
            logger.info("\n✓ Correct file count")
        else:
            logger.error(f"\n✗ Expected 3 files, found {summary['total_files']}")

    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

    logger.info("\n" + "="*60)


def main():
    """Run all JSON exporter tests"""
    print("\n" + "="*60)
    print("JSON Exporter Test Suite")
    print("="*60 + "\n")

    results = {}

    # Test 1: Validation
    print("\n[Test 1] Testing validation...")
    try:
        test_validation()
        results['validation'] = True
        print("✓ Test 1 passed\n")
    except Exception as e:
        print(f"✗ Test 1 failed: {e}\n")
        logger.error("Test 1 failed", exc_info=True)
        results['validation'] = False

    # Test 2: UTF-8 Encoding
    print("\n[Test 2] Testing UTF-8 encoding...")
    try:
        test_encoding()
        results['encoding'] = True
        print("✓ Test 2 passed\n")
    except Exception as e:
        print(f"✗ Test 2 failed: {e}\n")
        logger.error("Test 2 failed", exc_info=True)
        results['encoding'] = False

    # Test 3: Single post save
    print("\n[Test 3] Testing single post save...")
    try:
        test_save_single_post()
        results['single_save'] = True
        print("✓ Test 3 passed\n")
    except Exception as e:
        print(f"✗ Test 3 failed: {e}\n")
        logger.error("Test 3 failed", exc_info=True)
        results['single_save'] = False

    # Test 4: Multiple posts save
    print("\n[Test 4] Testing multiple posts save...")
    try:
        test_save_multiple_posts()
        results['multiple_save'] = True
        print("✓ Test 4 passed\n")
    except Exception as e:
        print(f"✗ Test 4 failed: {e}\n")
        logger.error("Test 4 failed", exc_info=True)
        results['multiple_save'] = False

    # Test 5: Combined JSON
    print("\n[Test 5] Testing combined JSON save...")
    try:
        test_combined_json()
        results['combined'] = True
        print("✓ Test 5 passed\n")
    except Exception as e:
        print(f"✗ Test 5 failed: {e}\n")
        logger.error("Test 5 failed", exc_info=True)
        results['combined'] = False

    # Test 6: Directory creation
    print("\n[Test 6] Testing directory creation...")
    try:
        test_directory_creation()
        results['directories'] = True
        print("✓ Test 6 passed\n")
    except Exception as e:
        print(f"✗ Test 6 failed: {e}\n")
        logger.error("Test 6 failed", exc_info=True)
        results['directories'] = False

    # Test 7: Format post data
    print("\n[Test 7] Testing post data formatting...")
    try:
        test_format_post_data()
        results['formatting'] = True
        print("✓ Test 7 passed\n")
    except Exception as e:
        print(f"✗ Test 7 failed: {e}\n")
        logger.error("Test 7 failed", exc_info=True)
        results['formatting'] = False

    # Test 8: Export summary
    print("\n[Test 8] Testing export summary...")
    try:
        test_export_summary()
        results['summary'] = True
        print("✓ Test 8 passed\n")
    except Exception as e:
        print(f"✗ Test 8 failed: {e}\n")
        logger.error("Test 8 failed", exc_info=True)
        results['summary'] = False

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
