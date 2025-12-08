"""
JSON exporter for TuoiTre.vn crawler
Handles saving post data as JSON with proper UTF-8 encoding and validation
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import config
from crawler.utils.logger import create_module_logger
from crawler.utils.helpers import sanitize_filename, clean_text
from crawler.utils.exceptions import ValidationError

logger = create_module_logger('JSONExporter')


def save_post_json(
    post_data: Dict[str, Any],
    output_dir: Path = None,
    filename: str = None,
    validate: bool = True,
    include_metadata: bool = True
) -> Path:
    """
    Save post data as JSON file with proper UTF-8 encoding

    Args:
        post_data: Dictionary containing post data
        output_dir: Output directory (defaults to config.JSON_OUTPUT_DIR)
        filename: Custom filename (defaults to <postId>.json)
        validate: Whether to validate JSON structure before saving
        include_metadata: Whether to include crawl metadata

    Returns:
        Path to saved JSON file

    Raises:
        ValidationError: If validation fails and validate=True
        IOError: If file write fails
    """
    # Determine output directory
    if output_dir is None:
        output_dir = config.JSON_OUTPUT_DIR
    output_dir = Path(output_dir)

    # Create directory if it doesn't exist
    create_directory(output_dir)

    # Validate post data structure
    if validate:
        is_valid, errors = validate_post_data(post_data)
        if not is_valid:
            error_msg = f"Post data validation failed: {', '.join(errors)}"
            logger.error(error_msg)
            raise ValidationError(error_msg)

    # Add crawl metadata if requested
    if include_metadata and config.INCLUDE_METADATA:
        post_data = add_crawl_metadata(post_data)

    # Generate filename
    if filename is None:
        post_id = post_data.get('postId', 'unknown')
        filename = f"{post_id}.json"

    # Sanitize filename
    filename = sanitize_filename(filename)
    if not filename.endswith('.json'):
        filename += '.json'

    # Full path
    file_path = output_dir / filename

    # Save JSON with proper UTF-8 encoding
    try:
        save_json_file(post_data, file_path)
        logger.info(f"✓ Saved post JSON: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"Failed to save JSON: {e}")
        raise


def validate_post_data(post_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate post data structure before saving

    Args:
        post_data: Post data dictionary to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Required fields
    required_fields = ['postId', 'title', 'content']

    for field in required_fields:
        if field not in post_data:
            errors.append(f"Missing required field: {field}")
        elif post_data[field] is None or post_data[field] == '':
            errors.append(f"Required field is empty: {field}")

    # Validate field types
    if 'postId' in post_data and not isinstance(post_data['postId'], str):
        errors.append("postId must be a string")

    if 'title' in post_data and not isinstance(post_data['title'], str):
        errors.append("title must be a string")

    if 'content' in post_data:
        if isinstance(post_data['content'], dict):
            # Content can be dict with 'text' and 'html'
            if 'text' not in post_data['content'] and 'html' not in post_data['content']:
                errors.append("content dict must have 'text' or 'html'")
        elif not isinstance(post_data['content'], str):
            errors.append("content must be a string or dict")

    # Optional field type validation
    if 'author' in post_data and post_data['author'] is not None:
        if not isinstance(post_data['author'], str):
            errors.append("author must be a string")

    if 'date' in post_data and post_data['date'] is not None:
        if not isinstance(post_data['date'], str):
            errors.append("date must be a string")

    if 'category' in post_data and post_data['category'] is not None:
        if not isinstance(post_data['category'], str):
            errors.append("category must be a string")

    if 'vote_reactions' in post_data and post_data['vote_reactions'] is not None:
        if not isinstance(post_data['vote_reactions'], dict):
            errors.append("vote_reactions must be a dict")

    if 'audio_podcast' in post_data and post_data['audio_podcast'] is not None:
        if not isinstance(post_data['audio_podcast'], str):
            errors.append("audio_podcast must be a string")

    if 'comments' in post_data and post_data['comments'] is not None:
        if not isinstance(post_data['comments'], list):
            errors.append("comments must be a list")
        else:
            # Validate comment structure
            comment_errors = validate_comments(post_data['comments'])
            errors.extend(comment_errors)

    # Check for Vietnamese text encoding issues
    encoding_issues = check_encoding_issues(post_data)
    if encoding_issues:
        errors.extend(encoding_issues)

    is_valid = len(errors) == 0

    if not is_valid:
        logger.warning(f"Validation found {len(errors)} issues")
        for error in errors:
            logger.warning(f"  - {error}")
    else:
        logger.debug("Post data validation passed")

    return is_valid, errors


def validate_comments(comments: List[Dict[str, Any]], depth: int = 0) -> List[str]:
    """
    Recursively validate comment structure

    Args:
        comments: List of comment dictionaries
        depth: Current recursion depth

    Returns:
        List of validation errors
    """
    errors = []

    for i, comment in enumerate(comments):
        comment_path = f"comments[{i}]" if depth == 0 else f"reply[{i}] at depth {depth}"

        # Required comment fields
        required_comment_fields = ['commentId', 'author', 'text']

        for field in required_comment_fields:
            if field not in comment:
                errors.append(f"{comment_path}: Missing field '{field}'")

        # Validate field types
        if 'commentId' in comment and not isinstance(comment['commentId'], str):
            errors.append(f"{comment_path}: commentId must be string")

        if 'author' in comment and not isinstance(comment['author'], str):
            errors.append(f"{comment_path}: author must be string")

        if 'text' in comment and not isinstance(comment['text'], str):
            errors.append(f"{comment_path}: text must be string")

        if 'vote_react_list' in comment and comment['vote_react_list'] is not None:
            if not isinstance(comment['vote_react_list'], dict):
                errors.append(f"{comment_path}: vote_react_list must be dict")

        # Recursively validate replies
        if 'replies' in comment and comment['replies']:
            if not isinstance(comment['replies'], list):
                errors.append(f"{comment_path}: replies must be list")
            else:
                reply_errors = validate_comments(comment['replies'], depth + 1)
                errors.extend(reply_errors)

    return errors


def check_encoding_issues(data: Any, path: str = 'root') -> List[str]:
    """
    Check for encoding issues in Vietnamese text

    Args:
        data: Data to check (can be dict, list, str)
        path: Current path for error reporting

    Returns:
        List of encoding issues found
    """
    issues = []

    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{path}.{key}"
            issues.extend(check_encoding_issues(value, new_path))

    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_path = f"{path}[{i}]"
            issues.extend(check_encoding_issues(item, new_path))

    elif isinstance(data, str):
        # Check for common encoding issues
        if '\ufffd' in data:  # Replacement character
            issues.append(f"{path}: Contains replacement character (encoding issue)")

        # Check for mojibake patterns (common with Vietnamese)
        mojibake_patterns = [
            r'Ã¡|Ã |áº£|Ã£|áº¡',  # Broken Vietnamese characters
            r'\x00',  # Null bytes
        ]

        for pattern in mojibake_patterns:
            if re.search(pattern, data):
                issues.append(f"{path}: Potential encoding issue detected")
                break

    return issues


def save_json_file(data: Dict[str, Any], file_path: Path) -> None:
    """
    Save data to JSON file with proper UTF-8 encoding

    Args:
        data: Data to save
        file_path: Path to save file

    Raises:
        IOError: If file write fails
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,  # Important for Vietnamese text
                indent=config.JSON_INDENT,
                sort_keys=False,
                default=json_serializer
            )

        logger.debug(f"Wrote JSON to {file_path} ({file_path.stat().st_size} bytes)")

    except Exception as e:
        logger.error(f"Failed to write JSON file: {e}")
        raise IOError(f"Failed to write JSON file: {e}")


def json_serializer(obj: Any) -> Any:
    """
    Custom JSON serializer for objects that aren't serializable by default

    Args:
        obj: Object to serialize

    Returns:
        Serializable version of object
    """
    # Handle datetime objects
    if isinstance(obj, datetime):
        return obj.isoformat()

    # Handle Path objects
    if isinstance(obj, Path):
        return str(obj)

    # Handle bytes
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')

    # For other objects, convert to string
    return str(obj)


def create_directory(directory: Path) -> Path:
    """
    Create directory if it doesn't exist

    Args:
        directory: Directory path to create

    Returns:
        Path to created/existing directory
    """
    directory = Path(directory)

    try:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")
        return directory

    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        raise


def add_crawl_metadata(post_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add crawl metadata to post data

    Args:
        post_data: Original post data

    Returns:
        Post data with added metadata
    """
    # Create a copy to avoid modifying original
    data = post_data.copy()

    # Add metadata
    metadata = {
        'crawled_at': datetime.now().isoformat(),
        'crawler_version': '1.0.0',
        'data_format_version': '1.0'
    }

    # Add to data (either as top-level or nested)
    if 'metadata' not in data:
        data['metadata'] = metadata
    else:
        # Merge with existing metadata
        data['metadata'].update(metadata)

    return data


def format_post_data(
    post_id: str,
    title: str,
    content: Any,
    author: Optional[str] = None,
    date: Optional[str] = None,
    category: Optional[str] = None,
    audio_podcast: Optional[str] = None,
    vote_reactions: Optional[Dict[str, int]] = None,
    comments: Optional[List[Dict[str, Any]]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Format post data into standardized structure

    Args:
        post_id: Post ID
        title: Post title
        content: Post content (string or dict with 'text' and 'html')
        author: Post author
        date: Publication date
        category: Post category
        audio_podcast: URL to audio file (if any)
        vote_reactions: Vote reactions dictionary
        comments: List of comments
        **kwargs: Additional fields to include

    Returns:
        Formatted post data dictionary
    """
    # Normalize content: we only keep text for JSON export to reduce size
    clean_content = content
    if isinstance(content, dict):
        clean_content = {
            'text': content.get('text', '')
        }

    # Build base structure
    data = {
        'postId': str(post_id),
        'title': clean_text(title) if title else '',
        'content': clean_content,
        'author': author,
        'date': date,
        'category': category,
        'audio_podcast': audio_podcast,
        'vote_reactions': vote_reactions or {},
        'comments': comments or []
    }

    # Add any additional fields
    data.update(kwargs)

    return data


def save_multiple_posts(
    posts: List[Dict[str, Any]],
    output_dir: Path = None,
    validate: bool = True
) -> List[Path]:
    """
    Save multiple posts as separate JSON files

    Args:
        posts: List of post data dictionaries
        output_dir: Output directory
        validate: Whether to validate each post

    Returns:
        List of paths to saved files
    """
    if output_dir is None:
        output_dir = config.JSON_OUTPUT_DIR

    saved_files = []
    failed_count = 0

    logger.info(f"Saving {len(posts)} posts to {output_dir}")

    for i, post_data in enumerate(posts, 1):
        try:
            file_path = save_post_json(
                post_data,
                output_dir=output_dir,
                validate=validate
            )
            saved_files.append(file_path)

            logger.info(f"[{i}/{len(posts)}] ✓ Saved: {file_path.name}")

        except Exception as e:
            failed_count += 1
            post_id = post_data.get('postId', 'unknown')
            logger.error(f"[{i}/{len(posts)}] ✗ Failed to save post {post_id}: {e}")

            if not config.SKIP_ON_ERROR:
                raise

    logger.info(f"Saved {len(saved_files)} posts, {failed_count} failed")

    return saved_files


def save_combined_json(
    posts: List[Dict[str, Any]],
    output_file: Path = None,
    validate: bool = True
) -> Path:
    """
    Save all posts in a single JSON file

    Args:
        posts: List of post data dictionaries
        output_file: Output file path
        validate: Whether to validate posts

    Returns:
        Path to saved file
    """
    if output_file is None:
        output_file = config.JSON_OUTPUT_DIR / 'all_posts.json'

    output_file = Path(output_file)

    # Create directory
    create_directory(output_file.parent)

    # Validate if requested
    if validate:
        validation_errors = []
        for i, post in enumerate(posts):
            is_valid, errors = validate_post_data(post)
            if not is_valid:
                validation_errors.append(f"Post {i}: {', '.join(errors)}")

        if validation_errors and not config.SKIP_ON_ERROR:
            error_msg = f"Validation failed:\n" + "\n".join(validation_errors)
            raise ValidationError(error_msg)

    # Create combined structure
    combined_data = {
        'metadata': {
            'total_posts': len(posts),
            'exported_at': datetime.now().isoformat(),
            'crawler_version': '1.0.0'
        },
        'posts': posts
    }

    # Save
    save_json_file(combined_data, output_file)
    logger.info(f"✓ Saved {len(posts)} posts to combined file: {output_file}")

    return output_file


def load_post_json(file_path: Path) -> Dict[str, Any]:
    """
    Load post data from JSON file

    Args:
        file_path: Path to JSON file

    Returns:
        Post data dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.debug(f"Loaded post data from {file_path}")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        raise

    except Exception as e:
        logger.error(f"Failed to load JSON from {file_path}: {e}")
        raise


def get_export_summary(output_dir: Path = None) -> Dict[str, Any]:
    """
    Get summary of exported JSON files

    Args:
        output_dir: Directory to analyze

    Returns:
        Summary dictionary
    """
    if output_dir is None:
        output_dir = config.JSON_OUTPUT_DIR

    output_dir = Path(output_dir)

    if not output_dir.exists():
        return {
            'total_files': 0,
            'total_size': 0,
            'files': []
        }

    # Find all JSON files
    json_files = list(output_dir.glob('*.json'))

    total_size = sum(f.stat().st_size for f in json_files)

    summary = {
        'total_files': len(json_files),
        'total_size': total_size,
        'total_size_formatted': format_bytes(total_size),
        'files': [
            {
                'name': f.name,
                'size': f.stat().st_size,
                'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            }
            for f in sorted(json_files, key=lambda x: x.stat().st_mtime, reverse=True)
        ]
    }

    return summary


def format_bytes(bytes_num: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_num < 1024.0:
            return f"{bytes_num:.1f}{unit}"
        bytes_num /= 1024.0
    return f"{bytes_num:.1f}TB"


def validate_json_file(file_path: Path) -> tuple[bool, List[str]]:
    """
    Validate a saved JSON file

    Args:
        file_path: Path to JSON file

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check file exists
    if not file_path.exists():
        errors.append(f"File does not exist: {file_path}")
        return False, errors

    # Check file size
    if file_path.stat().st_size == 0:
        errors.append(f"File is empty: {file_path}")
        return False, errors

    # Try to load JSON
    try:
        data = load_post_json(file_path)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return False, errors
    except Exception as e:
        errors.append(f"Failed to load file: {e}")
        return False, errors

    # Validate structure
    is_valid, validation_errors = validate_post_data(data)
    errors.extend(validation_errors)

    return is_valid, errors
