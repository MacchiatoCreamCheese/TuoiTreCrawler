"""
Comment parser for TuoiTre.vn
Handles extracting comments with nested replies and vote reactions using API
"""

import re
import time
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup, Tag

import config
from crawler.utils.logger import create_module_logger
from crawler.utils.helpers import (
    clean_text,
    parse_vietnamese_date,
    generate_unique_id
)
from crawler.utils.exceptions import ParseError

logger = create_module_logger('Parser')


def extract_comments(
    scraper,
    post_url: str,
    soup: BeautifulSoup = None,
    max_depth: int = None
) -> List[Dict[str, Any]]:
    """
    Extract all comments from a post using TuoiTre.vn comment API

    Args:
        scraper: TuoiTreScraper instance
        post_url: URL of the post
        soup: BeautifulSoup object (not used, kept for compatibility)
        max_depth: Maximum depth for nested replies (uses config default if None)

    Returns:
        List of comment dictionaries with nested replies

    Each comment includes:
        - commentId: Unique comment identifier
        - author: Comment author name
        - text: Comment text content
        - date: Comment timestamp
        - vote_react_list: Dictionary of vote reactions
        - replies: List of nested reply comments (same structure)
        - depth: Nesting depth (0 for top-level)
    """
    logger.info(f"Extracting comments from: {post_url}")

    try:
        # Extract post ID from URL
        post_id = _extract_post_id_from_url(post_url)
        if not post_id:
            logger.warning(f"Could not extract post ID from URL: {post_url}")
            return []

        max_depth = max_depth or config.MAX_COMMENT_DEPTH

        # Fetch comments from API
        all_comments_data = _fetch_comments_from_api(scraper, post_id, post_url)

        if not all_comments_data:
            logger.info(f"No comments found for post: {post_url}")
            return []

        # Build comment tree with nested replies
        comment_tree = _build_comment_tree(all_comments_data, max_depth)

        total_comments = _count_all_comments(comment_tree)
        logger.info(f"Extracted {len(comment_tree)} top-level comments "
                   f"({total_comments} total including replies)")

        return comment_tree

    except Exception as e:
        logger.error(f"Error extracting comments from {post_url}: {e}", exc_info=True)
        if not config.GRACEFUL_DEGRADATION:
            raise ParseError(f"Failed to extract comments", url=post_url)
        return []


def _extract_post_id_from_url(post_url: str) -> Optional[str]:
    """
    Extract post ID from TuoiTre.vn URL
    Format: https://tuoitre.vn/article-title-20251207230626132.htm

    Args:
        post_url: Post URL

    Returns:
        Post ID or None if not found
    """
    match = re.search(r'-(\d{10,})\.htm', post_url)
    if match:
        return match.group(1)
    return None


def _fetch_comments_from_api(scraper, post_id: str, post_url: str) -> List[Dict[str, Any]]:
    """
    Fetch all comments from TuoiTre.vn comment API with pagination

    Args:
        scraper: TuoiTreScraper instance
        post_id: Post ID
        post_url: Post URL (for referer header)

    Returns:
        List of all comment dictionaries from API
    """
    all_comments = []
    page_index = 1
    page_size = 100  # Fetch more comments per page

    while True:
        try:
            # API endpoint
            api_url = f"https://id.tuoitre.vn/api/getlist-comment.api?objId={post_id}&objType=1&pageindex={page_index}&pagesize={page_size}"

            # Make request
            headers = {
                'User-Agent': 'StudentCrawler/1.0 (Educational Project)',
                'Accept': 'application/json',
                'Referer': post_url
            }

            logger.debug(f"Fetching comments page {page_index} from API")
            response = scraper.session.get(api_url, headers=headers, timeout=config.REQUEST_TIMEOUT)

            if response.status_code != 200:
                logger.warning(f"Comment API returned status {response.status_code}")
                break

            # Parse JSON response
            data = response.json()

            if not data.get('Success'):
                logger.debug(f"API request not successful: {data.get('Message', 'Unknown error')}")
                break

            # Data field contains JSON string, need to parse it again
            comments_json = data.get('Data', '[]')
            if isinstance(comments_json, str):
                comments = json.loads(comments_json)
            else:
                comments = comments_json

            if not comments:
                logger.debug(f"No more comments on page {page_index}")
                break

            all_comments.extend(comments)
            logger.debug(f"Fetched {len(comments)} comments from page {page_index}")

            # Check if there might be more pages
            if len(comments) < page_size:
                break

            page_index += 1

            # Respect rate limiting
            time.sleep(0.5)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse comment API response: {e}")
            break
        except Exception as e:
            logger.error(f"Error fetching comments from API: {e}")
            break

    logger.info(f"Fetched total of {len(all_comments)} comments from API")
    return all_comments


def _build_comment_tree(comments_data: List[Dict[str, Any]], max_depth: int) -> List[Dict[str, Any]]:
    """
    Build hierarchical comment tree from flat API data

    Args:
        comments_data: List of comment dictionaries from API
        max_depth: Maximum nesting depth

    Returns:
        List of top-level comments with nested replies
    """
    # First, normalize all comments
    comments_by_id = {}
    top_level = []

    for comment_data in comments_data:
        comment = _normalize_api_comment(comment_data)
        if comment:
            comment_id = comment['commentId']
            comments_by_id[comment_id] = comment

            # Check if top-level (parent_id is "0" or None)
            parent_id = comment_data.get('parent_id', '0')
            if parent_id == '0' or parent_id is None:
                top_level.append(comment)

    # Build parent-child relationships
    for comment_data in comments_data:
        parent_id = comment_data.get('parent_id', '0')

        if parent_id and parent_id != '0' and parent_id in comments_by_id:
            comment_id = comment_data.get('id', '')  # Use the UUID as unique identifier

            if comment_id and comment_id in comments_by_id:
                child_comment = comments_by_id[comment_id]
                parent_comment = comments_by_id[parent_id]

                # Check depth limit
                if child_comment.get('depth', 0) <= max_depth:
                    parent_comment['replies'].append(child_comment)

    return top_level


def _normalize_api_comment(comment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Normalize API comment data to our standard format

    Args:
        comment_data: Raw comment data from API

    Returns:
        Normalized comment dictionary
    """
    try:
        # Extract fields from API response
        comment_id = comment_data.get('id', '')  # UUID is the unique identifier
        content = comment_data.get('content', '')
        sender_fullname = comment_data.get('sender_fullname', 'Anonymous')
        created_date = comment_data.get('created_date', '')
        parent_id = comment_data.get('parent_id', '0')

        # Calculate depth based on parent_id
        depth = 0 if parent_id == '0' or parent_id is None else 1

        # Vote reactions from the reactions object and individual fields
        vote_react_list = {}

        # Try to get from reactions object
        reactions = comment_data.get('reactions', {})
        if reactions:
            # Reaction types: 1=like, 3=love, 5=haha, 7=wow, 9=sad, 11=angry, 13=star
            reaction_map = {
                '1': 'like',
                '3': 'love',
                '5': 'haha',
                '7': 'wow',
                '9': 'sad',
                '11': 'angry',
                '13': 'star'
            }
            for key, name in reaction_map.items():
                count = reactions.get(key, 0)
                if count and count > 0:
                    vote_react_list[name] = count

        # Also add individual reaction counts if available
        if comment_data.get('loves'):
            vote_react_list['love'] = comment_data.get('loves', 0)
        if comment_data.get('likes'):
            vote_react_list['like'] = comment_data.get('likes', 0)
        if comment_data.get('hahas'):
            vote_react_list['haha'] = comment_data.get('hahas', 0)
        if comment_data.get('wows'):
            vote_react_list['wow'] = comment_data.get('wows', 0)
        if comment_data.get('sads'):
            vote_react_list['sad'] = comment_data.get('sads', 0)
        if comment_data.get('wraths'):
            vote_react_list['angry'] = comment_data.get('wraths', 0)
        if comment_data.get('stars'):
            vote_react_list['star'] = comment_data.get('stars', 0)

        return {
            'commentId': comment_id or generate_unique_id(),
            'author': clean_text(sender_fullname),
            'text': clean_text(content),
            'date': created_date,
            'vote_react_list': vote_react_list,
            'replies': [],
            'depth': depth
        }

    except Exception as e:
        logger.error(f"Error normalizing comment: {e}")
        return None


def _parse_comment_element(
    element: Tag,
    post_url: str,
    depth: int = 0,
    max_depth: int = 10
) -> Optional[Dict[str, Any]]:
    """
    Parse a single comment element and its nested replies

    Args:
        element: Comment element
        post_url: URL of the post
        depth: Current nesting depth
        max_depth: Maximum depth for recursion

    Returns:
        Comment dictionary or None if parsing fails
    """
    try:
        # Extract comment ID
        comment_id = _extract_comment_id(element, post_url)

        # Extract author
        author = _extract_comment_author(element)

        # Extract text content
        text = _extract_comment_text(element)

        # Extract date
        date = _extract_comment_date(element)

        # Extract vote reactions
        vote_react_list = _extract_comment_reactions(element)

        # Build comment dictionary
        comment = {
            'commentId': comment_id,
            'author': author,
            'text': text,
            'date': date,
            'vote_react_list': vote_react_list,
            'depth': depth,
            'replies': []
        }

        # Recursively extract nested replies
        if depth < max_depth:
            replies = _extract_nested_replies(element, post_url, depth, max_depth)
            if replies:
                comment['replies'] = replies

        return comment

    except Exception as e:
        logger.warning(f"Error parsing comment element at depth {depth}: {e}")
        if not config.GRACEFUL_DEGRADATION:
            raise
        return None


def _extract_comment_id(element: Tag, post_url: str) -> str:
    """Extract comment ID from element"""
    # Try data attributes
    comment_id = element.get('data-comment-id') or element.get('id')

    if comment_id:
        # Clean up ID (remove prefixes like "comment-")
        comment_id = re.sub(r'^comment-?', '', str(comment_id))
        return comment_id

    # Try finding ID in child elements
    id_elem = element.find(attrs={'data-commentid': True})
    if id_elem:
        return str(id_elem['data-commentid'])

    # Generate unique ID if not found
    return generate_unique_id(prefix='comment_')


def _extract_comment_author(element: Tag) -> str:
    """Extract comment author name"""
    # Try multiple selectors
    selectors = [
        ('span', {'class': re.compile(r'author|user-name|username|name-user')}),
        ('a', {'class': re.compile(r'author|user-name')}),
        ('strong', {'class': re.compile(r'author|name')}),
        ('div', {'class': re.compile(r'author')}),
    ]

    for tag, attrs in selectors:
        author_elem = element.find(tag, attrs)
        if author_elem:
            author = clean_text(author_elem.get_text(strip=True))
            if author:
                return author

    # Try meta tag
    author_elem = element.find('meta', {'itemprop': 'author'})
    if author_elem:
        return author_elem.get('content', 'Anonymous')

    return 'Anonymous'


def _extract_comment_text(element: Tag) -> str:
    """Extract comment text content"""
    # Try multiple selectors for comment content
    selectors = [
        ('div', {'class': re.compile(r'comment-content|content-comment|comment-text')}),
        ('p', {'class': re.compile(r'comment-content|content')}),
        ('div', {'class': re.compile(r'text|content')}),
        ('p', {}),
    ]

    for tag, attrs in selectors:
        content_elem = element.find(tag, attrs)
        if content_elem:
            # Get text, excluding nested reply containers
            text = content_elem.get_text(separator=' ', strip=True)

            # Remove reply container text if present
            for reply_container in content_elem.find_all(
                ['div', 'ul'],
                class_=re.compile(r'repl(y|ies)|nested')
            ):
                reply_text = reply_container.get_text(separator=' ', strip=True)
                text = text.replace(reply_text, '')

            text = clean_text(text)
            if text:
                return text

    # Fallback: get all text from element
    text = element.get_text(separator=' ', strip=True)
    return clean_text(text) if text else ''


def _extract_comment_date(element: Tag) -> Optional[str]:
    """Extract comment date/timestamp"""
    # Try multiple selectors
    selectors = [
        ('time', {}),
        ('span', {'class': re.compile(r'date|time')}),
        ('div', {'class': re.compile(r'date|time')}),
    ]

    for tag, attrs in selectors:
        date_elem = element.find(tag, attrs)
        if date_elem:
            # Try datetime attribute
            date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)

            if date_str:
                # Try to parse Vietnamese date
                parsed_date = parse_vietnamese_date(date_str)
                if parsed_date:
                    return parsed_date.isoformat()

                # Return as-is if parsing fails
                return clean_text(date_str)

    return None


def _extract_comment_reactions(element: Tag) -> Dict[str, int]:
    """
    Extract vote reactions for a comment

    Args:
        element: Comment element

    Returns:
        Dictionary of reaction types and counts
    """
    reactions = {}

    # Try to find reaction/vote elements
    reaction_selectors = [
        ('div', {'class': re.compile(r'reaction|vote|like')}),
        ('span', {'class': re.compile(r'reaction|vote|like')}),
    ]

    for tag, attrs in reaction_selectors:
        reaction_container = element.find(tag, attrs)
        if reaction_container:
            # Look for individual reaction counts
            reaction_elements = reaction_container.find_all(
                ['span', 'a', 'button'],
                class_=re.compile(r'like|love|haha|wow|sad|angry|count')
            )

            for react_elem in reaction_elements:
                # Extract count
                count_text = react_elem.get_text(strip=True)
                count_match = re.search(r'(\d+)', count_text)

                if count_match:
                    count = int(count_match.group(1))

                    # Determine reaction type
                    reaction_type = 'like'  # default
                    classes = react_elem.get('class', [])

                    for cls in classes:
                        cls_lower = cls.lower()
                        if any(r in cls_lower for r in ['like', 'love', 'haha', 'wow', 'sad', 'angry']):
                            reaction_type = cls_lower
                            break

                    reactions[reaction_type] = reactions.get(reaction_type, 0) + count

    # Try data attributes as fallback
    if not reactions:
        for attr in ['data-like', 'data-vote', 'data-reaction']:
            if element.get(attr):
                try:
                    reactions['like'] = int(element[attr])
                except (ValueError, TypeError):
                    pass

    return reactions


def _extract_nested_replies(
    element: Tag,
    post_url: str,
    parent_depth: int,
    max_depth: int
) -> List[Dict[str, Any]]:
    """
    Recursively extract nested replies from a comment

    Args:
        element: Parent comment element
        post_url: URL of the post
        parent_depth: Depth of parent comment
        max_depth: Maximum depth for recursion

    Returns:
        List of reply comment dictionaries
    """
    if parent_depth >= max_depth:
        logger.debug(f"Reached max depth {max_depth}, stopping recursion")
        return []

    replies = []

    # Try to find reply container
    reply_selectors = [
        ('div', {'class': re.compile(r'repl(y|ies)|nested-comment|child-comment')}),
        ('ul', {'class': re.compile(r'repl(y|ies)|children')}),
        ('div', {'class': re.compile(r'list-reply')}),
    ]

    reply_container = None
    for tag, attrs in reply_selectors:
        reply_container = element.find(tag, attrs)
        if reply_container:
            logger.debug(f"Found reply container at depth {parent_depth}")
            break

    if not reply_container:
        return []

    # Find individual reply elements
    reply_elements = reply_container.find_all(
        ['div', 'li'],
        class_=re.compile(r'comment-item|item-comment|reply-item'),
        recursive=False
    )

    for reply_elem in reply_elements:
        try:
            reply = _parse_comment_element(
                reply_elem,
                post_url,
                depth=parent_depth + 1,
                max_depth=max_depth
            )
            if reply:
                replies.append(reply)
        except Exception as e:
            logger.warning(f"Failed to parse reply at depth {parent_depth + 1}: {e}")
            if not config.SKIP_ON_ERROR:
                raise

    return replies


def _count_all_comments(comments: List[Dict[str, Any]]) -> int:
    """
    Count total comments including all nested replies

    Args:
        comments: List of comment dictionaries

    Returns:
        Total count of comments
    """
    count = len(comments)
    for comment in comments:
        if comment.get('replies'):
            count += _count_all_comments(comment['replies'])
    return count


def validate_comment_count(comments: List[Dict[str, Any]], min_required: int = 20) -> bool:
    """
    Validate that we have minimum required number of comments

    Args:
        comments: List of comment dictionaries
        min_required: Minimum number of comments required

    Returns:
        True if requirement is met
    """
    total = _count_all_comments(comments)
    is_valid = total >= min_required

    if is_valid:
        logger.info(f"✓ Comment count validation passed: {total} >= {min_required}")
    else:
        logger.warning(f"✗ Comment count validation failed: {total} < {min_required}")

    return is_valid


def get_comment_statistics(comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get statistics about comment structure

    Args:
        comments: List of comment dictionaries

    Returns:
        Dictionary with comment statistics
    """
    total_comments = _count_all_comments(comments)
    top_level_count = len(comments)

    # Count comments at each depth
    depth_counts = {}
    max_depth = 0

    def count_by_depth(comment_list, current_depth=0):
        nonlocal max_depth
        for comment in comment_list:
            depth = comment.get('depth', current_depth)
            depth_counts[depth] = depth_counts.get(depth, 0) + 1
            max_depth = max(max_depth, depth)

            if comment.get('replies'):
                count_by_depth(comment['replies'], current_depth + 1)

    count_by_depth(comments)

    # Count comments with reactions
    comments_with_reactions = 0

    def count_reactions(comment_list):
        nonlocal comments_with_reactions
        for comment in comment_list:
            if comment.get('vote_react_list'):
                comments_with_reactions += 1
            if comment.get('replies'):
                count_reactions(comment['replies'])

    count_reactions(comments)

    return {
        'total_comments': total_comments,
        'top_level_comments': top_level_count,
        'max_depth': max_depth,
        'depth_distribution': depth_counts,
        'comments_with_reactions': comments_with_reactions,
        'average_replies_per_comment': (total_comments - top_level_count) / top_level_count if top_level_count > 0 else 0
    }
