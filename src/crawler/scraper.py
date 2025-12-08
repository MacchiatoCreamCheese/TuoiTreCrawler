"""
Web scraper for TuoiTre.vn
Handles fetching post URLs, scraping post details, and extracting reactions
"""

import time
import random
import re
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException, Timeout, ConnectionError

import config
from crawler.utils.exceptions import NetworkError, ParseError, RateLimitError
from crawler.utils.error_handler import retry_on_error, handle_network_error
from crawler.utils.logger import create_module_logger
from crawler.utils.helpers import (
    normalize_url,
    clean_text,
    parse_vietnamese_date,
    calculate_delay,
    generate_unique_id
)

logger = create_module_logger('Scraper')


class TuoiTreScraper:
    """
    Main scraper class for TuoiTre.vn
    Handles HTTP requests with rate limiting and user agent rotation
    """

    def __init__(
        self,
        delay_min: float = None,
        delay_max: float = None,
        max_retries: int = None,
        timeout: int = None
    ):
        """
        Initialize scraper

        Args:
            delay_min: Minimum delay between requests
            delay_max: Maximum delay between requests
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        self.delay_min = delay_min or config.REQUEST_DELAY_MIN
        self.delay_max = delay_max or config.REQUEST_DELAY_MAX
        self.max_retries = max_retries or config.MAX_RETRIES
        self.timeout = timeout or config.REQUEST_TIMEOUT

        self.session = requests.Session()
        self.last_request_time = 0
        self.user_agents = config.USER_AGENTS.copy()
        self.current_user_agent_index = 0

        logger.info("TuoiTreScraper initialized")
        logger.info(f"Delay: {self.delay_min}s - {self.delay_max}s")
        logger.info(f"Max retries: {self.max_retries}")
        logger.info(f"Timeout: {self.timeout}s")

    def _get_next_user_agent(self) -> str:
        """
        Get next user agent from rotation list

        Returns:
            User agent string
        """
        user_agent = self.user_agents[self.current_user_agent_index]
        self.current_user_agent_index = (self.current_user_agent_index + 1) % len(self.user_agents)
        return user_agent

    def _apply_rate_limit(self):
        """
        Apply rate limiting delay between requests
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.delay_min:
            delay = calculate_delay(self.delay_min, self.delay_max)
            logger.debug(f"Rate limiting: sleeping for {delay:.2f}s")
            time.sleep(delay)

        self.last_request_time = time.time()

    @retry_on_error(
        max_retries=3,
        delay=1.0,
        backoff=2.0,
        exceptions=(RequestException, NetworkError)
    )
    def _make_request(
        self,
        url: str,
        method: str = 'GET',
        **kwargs
    ) -> requests.Response:
        """
        Make HTTP request with rate limiting and error handling

        Args:
            url: URL to request
            method: HTTP method
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            NetworkError: If request fails after retries
        """
        # Apply rate limiting
        self._apply_rate_limit()

        # Rotate user agent
        headers = kwargs.get('headers', {})
        headers['User-Agent'] = self._get_next_user_agent()
        kwargs['headers'] = headers

        # Set timeout if not provided
        if 'timeout' not in kwargs:
            kwargs['timeout'] = self.timeout

        try:
            logger.debug(f"{method} {url}")
            response = self.session.request(method, url, **kwargs)

            # Check for rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise RateLimitError(
                    f"Rate limited by server",
                    retry_after=retry_after
                )

            # Raise for HTTP errors
            response.raise_for_status()

            logger.debug(f"Response: {response.status_code} ({len(response.content)} bytes)")
            return response

        except (Timeout, ConnectionError, RequestException) as e:
            error = handle_network_error(e, url)
            logger.error(f"Request failed: {error}")
            raise error

    def get_html(self, url: str) -> BeautifulSoup:
        """
        Fetch and parse HTML from URL

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object

        Raises:
            NetworkError: If request fails
        """
        response = self._make_request(url)

        # Handle Vietnamese encoding
        response.encoding = response.apparent_encoding or config.DEFAULT_ENCODING

        soup = BeautifulSoup(response.content, 'html.parser')
        return soup

    def close(self):
        """Close the session"""
        self.session.close()
        logger.info("Scraper session closed")


def get_category_post_urls(
    scraper: TuoiTreScraper,
    category_url: str,
    max_posts: int = 35,
    max_pages: int = 10
) -> List[str]:
    """
    Get all post URLs from a category page, handling pagination

    Args:
        scraper: TuoiTreScraper instance
        category_url: Category page URL
        max_posts: Maximum number of post URLs to retrieve
        max_pages: Maximum number of pages to crawl

    Returns:
        List of post URLs

    Raises:
        NetworkError: If fetching category page fails
        ParseError: If parsing fails
    """
    logger.info(f"Fetching post URLs from category: {category_url}")
    post_urls = []
    current_page = 1

    while len(post_urls) < max_posts and current_page <= max_pages:
        try:
            # Construct pagination URL
            if current_page == 1:
                page_url = category_url
            else:
                # TuoiTre.vn pagination format: category-pX.htm
                base_url = category_url.replace('.htm', '')
                page_url = f"{base_url}-p{current_page}.htm"

            logger.info(f"Fetching page {current_page}: {page_url}")
            soup = scraper.get_html(page_url)

            # Extract post URLs from the page
            # TuoiTre.vn typically uses <h3 class="title-news"> for post titles
            # or <a> tags with specific patterns
            page_post_urls = []

            # Method 1: Find article links in news list
            articles = soup.find_all(['article', 'div'], class_=re.compile(r'(box-category-item|news-item|item-news)'))

            if not articles:
                # Method 2: Find links with specific patterns
                articles = soup.find_all('h3', class_=re.compile(r'title-news'))

            for article in articles:
                # Find link within article
                link = article.find('a', href=True)

                if link and link.get('href'):
                    href = link['href']

                    # Normalize URL
                    full_url = normalize_url(href, category_url)

                    # Filter out non-article URLs
                    if _is_valid_article_url(full_url):
                        if full_url not in post_urls:
                            page_post_urls.append(full_url)
                            post_urls.append(full_url)

                            if len(post_urls) >= max_posts:
                                break

            logger.info(f"Found {len(page_post_urls)} post URLs on page {current_page}")

            # Check if we found any posts on this page
            if not page_post_urls:
                logger.warning(f"No posts found on page {current_page}, stopping pagination")
                break

            current_page += 1

        except NetworkError as e:
            logger.error(f"Failed to fetch page {current_page}: {e}")
            if config.SKIP_ON_ERROR:
                break
            else:
                raise

        except Exception as e:
            logger.error(f"Error parsing page {current_page}: {e}")
            if config.SKIP_ON_ERROR:
                break
            else:
                raise ParseError(f"Failed to parse category page", url=page_url)

    logger.info(f"Total post URLs collected: {len(post_urls)}")
    return post_urls[:max_posts]


def _is_valid_article_url(url: str) -> bool:
    """
    Check if URL is a valid article URL

    Args:
        url: URL to check

    Returns:
        True if URL is a valid article
    """
    if not url:
        return False

    # Check against disallowed paths from config
    if not config.is_url_allowed(url):
        logger.debug(f"URL blocked by disallowed paths: {url}")
        return False

    # Must be from tuoitre.vn
    if 'tuoitre.vn' not in url:
        return False

    # Exclude category pages, tag pages, etc.
    exclude_patterns = [
        r'/tag/',
        r'/video/',
        r'/podcast/',
        r'-p\d+\.htm$',  # Pagination pages
        r'\.htm$'  # Category pages typically end with .htm
    ]

    # Valid article URLs typically have format: /post-title-123456.htm or /category/post-title-123456.htm
    # They should have a numeric ID
    has_id = bool(re.search(r'-\d{6,}\.htm', url))

    if not has_id:
        return False

    # Check exclusions
    for pattern in exclude_patterns:
        if re.search(pattern, url):
            if not re.search(r'-\d{6,}\.htm', url):  # Unless it has article ID
                return False

    return True


def scrape_post_details(scraper: TuoiTreScraper, post_url: str) -> Optional[Dict[str, Any]]:
    """
    Scrape detailed information from a single post

    Args:
        scraper: TuoiTreScraper instance
        post_url: URL of the post to scrape

    Returns:
        Dictionary containing post details, or None if scraping fails

    Post details include:
        - postId: Unique post identifier
        - title: Post title
        - content: Post content (text and HTML)
        - author: Author name
        - date: Publication date
        - category: Post category
        - url: Post URL
    """
    logger.info(f"Scraping post: {post_url}")

    try:
        soup = scraper.get_html(post_url)

        # Extract post ID from URL
        post_id = _extract_post_id(post_url)

        # Extract title
        title = _extract_title(soup, post_url)

        # Extract author
        author = _extract_author(soup)

        # Extract publication date
        pub_date = _extract_date(soup)

        # Extract category
        category = _extract_category(soup, post_url)

        # Extract content
        content = _extract_content(soup)

        # Extract description/summary
        description = _extract_description(soup)

        # Extract tags
        tags = _extract_tags(soup)

        # Build post details dictionary
        post_details = {
            'postId': post_id,
            'url': post_url,
            'title': title,
            'author': author,
            'publishDate': pub_date,
            'category': category,
            'description': description,
            'content': content,
            'tags': tags,
            'scrapedAt': datetime.now().isoformat()
        }

        logger.info(f"Successfully scraped post: {title[:50]}...")
        return post_details

    except NetworkError as e:
        logger.error(f"Network error scraping post {post_url}: {e}")
        if not config.SKIP_ON_ERROR:
            raise
        return None

    except Exception as e:
        logger.error(f"Error scraping post {post_url}: {e}", exc_info=True)
        if not config.SKIP_ON_ERROR:
            raise ParseError(f"Failed to scrape post", url=post_url)
        return None


def _extract_post_id(url: str) -> str:
    """Extract post ID from URL"""
    # TuoiTre URLs format: /post-title-123456.htm
    match = re.search(r'-(\d+)\.htm', url)
    if match:
        return match.group(1)

    # Fallback: generate ID from URL
    return generate_unique_id(url, prefix='post_')


def _extract_title(soup: BeautifulSoup, url: str) -> str:
    """Extract post title"""
    # Try multiple selectors
    selectors = [
        ('h1', {'class': re.compile(r'article-title|detail-title|title-detail')}),
        ('h1', {'class': 'detail-title'}),
        ('h1', {}),
        ('meta', {'property': 'og:title'}),
    ]

    for tag, attrs in selectors:
        element = soup.find(tag, attrs)
        if element:
            if tag == 'meta':
                title = element.get('content', '')
            else:
                title = element.get_text(strip=True)

            if title:
                return clean_text(title)

    logger.warning(f"Could not find title for {url}")
    return "Untitled"


def _extract_author(soup: BeautifulSoup) -> Optional[str]:
    """Extract post author"""
    # Try multiple selectors
    selectors = [
        ('div', {'class': re.compile(r'author|writer|detail-author')}),
        ('span', {'class': re.compile(r'author|writer')}),
        ('p', {'class': re.compile(r'author|writer')}),
        ('meta', {'name': 'author'}),
    ]

    for tag, attrs in selectors:
        element = soup.find(tag, attrs)
        if element:
            if tag == 'meta':
                author = element.get('content', '')
            else:
                author = element.get_text(strip=True)

            if author:
                # Clean up author text
                author = re.sub(r'(Tác giả:|Theo|By:?)', '', author, flags=re.IGNORECASE)
                return clean_text(author)

    return None


def _extract_date(soup: BeautifulSoup) -> Optional[str]:
    """Extract publication date"""
    # Try multiple selectors
    selectors = [
        ('div', {'class': re.compile(r'date-time|detail-time|date-post')}),
        ('time', {}),
        ('span', {'class': re.compile(r'date|time')}),
        ('meta', {'property': 'article:published_time'}),
        ('meta', {'name': 'pubdate'}),
    ]

    for tag, attrs in selectors:
        element = soup.find(tag, attrs)
        if element:
            # Try datetime attribute first
            date_str = element.get('datetime') or element.get('content')

            # If not found, get text content
            if not date_str:
                date_str = element.get_text(strip=True)

            if date_str:
                # Try to parse the date
                parsed_date = parse_vietnamese_date(date_str)
                if parsed_date:
                    return parsed_date.isoformat()

                # Return as-is if parsing fails
                return clean_text(date_str)

    return None


def _extract_category(soup: BeautifulSoup, url: str) -> Optional[str]:
    """Extract post category"""
    # Try to extract from breadcrumbs
    breadcrumbs = soup.find('div', class_=re.compile(r'breadcrumb'))
    if breadcrumbs:
        links = breadcrumbs.find_all('a')
        if len(links) > 1:  # Skip "Home"
            return clean_text(links[1].get_text(strip=True))

    # Try to extract from URL
    parsed = urlparse(url)
    path_parts = [p for p in parsed.path.split('/') if p and p != '']
    if path_parts:
        # First part is usually the category
        category = path_parts[0].replace('.htm', '')
        return category

    return None


def _extract_description(soup: BeautifulSoup) -> Optional[str]:
    """Extract post description/summary"""
    selectors = [
        ('h2', {'class': re.compile(r'sapo|description|summary|detail-sapo')}),
        ('div', {'class': re.compile(r'sapo|description|summary')}),
        ('meta', {'property': 'og:description'}),
        ('meta', {'name': 'description'}),
    ]

    for tag, attrs in selectors:
        element = soup.find(tag, attrs)
        if element:
            if tag == 'meta':
                desc = element.get('content', '')
            else:
                desc = element.get_text(strip=True)

            if desc:
                return clean_text(desc)

    return None


def _extract_content(soup: BeautifulSoup) -> Dict[str, str]:
    """Extract post content (both text and HTML)"""
    # Try to find main content container
    content_selectors = [
        ('div', {'class': re.compile(r'detail-content|article-content|content-detail|fck')}),
        ('article', {'class': re.compile(r'content|detail')}),
        ('div', {'id': re.compile(r'main-detail-content|article-content')}),
    ]

    content_element = None
    for tag, attrs in content_selectors:
        content_element = soup.find(tag, attrs)
        if content_element:
            break

    if not content_element:
        logger.warning("Could not find content element")
        return {'text': '', 'html': ''}

    # Get HTML content
    html_content = str(content_element)

    # Get text content
    # Remove script and style tags
    for script in content_element(['script', 'style', 'iframe']):
        script.decompose()

    text_content = content_element.get_text(separator='\n', strip=True)
    text_content = clean_text(text_content)

    return {
        'text': text_content,
        'html': html_content
    }


def _extract_tags(soup: BeautifulSoup) -> List[str]:
    """Extract post tags"""
    tags = []

    # Try to find tags container
    tags_container = soup.find('div', class_=re.compile(r'tags|tag-list|detail-tag'))

    if tags_container:
        tag_links = tags_container.find_all('a')
        for link in tag_links:
            tag_text = clean_text(link.get_text(strip=True))
            if tag_text:
                tags.append(tag_text)

    return tags


def extract_vote_reactions(scraper: TuoiTreScraper, post_url: str, soup: BeautifulSoup = None) -> Dict[str, int]:
    """
    Extract vote reactions from a post

    Args:
        scraper: TuoiTreScraper instance
        post_url: URL of the post
        soup: BeautifulSoup object (if already fetched)

    Returns:
        Dictionary with reaction counts (e.g., {'like': 10, 'love': 5, ...})
    """
    logger.debug(f"Extracting vote reactions from: {post_url}")

    try:
        if soup is None:
            soup = scraper.get_html(post_url)

        reactions = {}

        # Try to find reactions container
        # TuoiTre.vn may use different structures for reactions
        reactions_selectors = [
            ('div', {'class': re.compile(r'reaction|emotion|feel')}),
            ('div', {'class': re.compile(r'like|vote')}),
            ('div', {'id': re.compile(r'reaction|emotion')}),
        ]

        reactions_container = None
        for tag, attrs in reactions_selectors:
            reactions_container = soup.find(tag, attrs)
            if reactions_container:
                break

        if reactions_container:
            # Extract individual reaction counts
            reaction_elements = reactions_container.find_all(['span', 'div', 'a'],
                                                            class_=re.compile(r'count|num'))

            for element in reaction_elements:
                # Try to extract reaction type and count
                reaction_text = element.get_text(strip=True)

                # Look for numbers
                count_match = re.search(r'(\d+)', reaction_text)
                if count_match:
                    count = int(count_match.group(1))

                    # Try to determine reaction type from class or parent
                    reaction_type = 'like'  # default

                    # Check element classes
                    classes = element.get('class', [])
                    for cls in classes:
                        if any(r in cls.lower() for r in ['like', 'love', 'haha', 'wow', 'sad', 'angry']):
                            reaction_type = cls.lower()
                            break

                    reactions[reaction_type] = reactions.get(reaction_type, 0) + count

        # If no reactions found through container, try meta tags or data attributes
        if not reactions:
            # Check for data attributes
            for element in soup.find_all(attrs={'data-like': True}):
                try:
                    reactions['like'] = int(element['data-like'])
                except (ValueError, KeyError):
                    pass

            for element in soup.find_all(attrs={'data-share': True}):
                try:
                    reactions['share'] = int(element['data-share'])
                except (ValueError, KeyError):
                    pass

        logger.debug(f"Found reactions: {reactions}")
        return reactions

    except Exception as e:
        logger.warning(f"Error extracting reactions from {post_url}: {e}")
        return {}
