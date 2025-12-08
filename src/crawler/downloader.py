"""
Media downloader for TuoiTre.vn
Handles downloading images, audio, and video with progress tracking
"""

import os
import re
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from urllib.parse import urlparse, unquote
import hashlib

import requests
from bs4 import BeautifulSoup

import config
from crawler.utils.logger import create_module_logger
from crawler.utils.helpers import (
    sanitize_filename,
    normalize_url,
    get_file_extension,
    estimate_media_type
)
from crawler.utils.exceptions import MediaDownloadError

logger = create_module_logger('Downloader')


class MediaDownloader:
    """
    Handles downloading media files with progress tracking and validation
    """

    def __init__(self, scraper, base_dir: Path = None):
        """
        Initialize media downloader

        Args:
            scraper: TuoiTreScraper instance
            base_dir: Base directory for media downloads (defaults to config.MEDIA_DIR)
        """
        self.scraper = scraper
        self.base_dir = base_dir or config.MEDIA_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            'images_downloaded': 0,
            'images_failed': 0,
            'audio_downloaded': 0,
            'audio_failed': 0,
            'total_bytes': 0
        }

        logger.info(f"MediaDownloader initialized with base dir: {self.base_dir}")

    def download_file(
        self,
        url: str,
        save_path: Path,
        chunk_size: int = 8192,
        show_progress: bool = True
    ) -> bool:
        """
        Download a file from URL with progress tracking

        Args:
            url: URL of file to download
            save_path: Path to save downloaded file
            chunk_size: Size of chunks for streaming download
            show_progress: Whether to show progress indicator

        Returns:
            True if download successful, False otherwise
        """
        try:
            # Make request with streaming
            response = self.scraper._make_request(url, stream=True)

            # Get file size if available
            total_size = int(response.headers.get('content-length', 0))

            # Create parent directory
            save_path.parent.mkdir(parents=True, exist_ok=True)

            # Download with progress tracking
            downloaded = 0
            start_time = time.time()

            with open(save_path, 'wb') as f:
                if total_size > 0 and show_progress:
                    # Show progress for large files (>100KB)
                    if total_size > 100 * 1024:
                        logger.info(f"Downloading {save_path.name} ({self._format_bytes(total_size)})...")

                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Show progress for large files
                        if show_progress and total_size > 1024 * 1024:  # > 1MB
                            progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                            if int(progress) % 25 == 0:  # Log every 25%
                                logger.debug(f"Progress: {progress:.1f}%")

            # Validate download
            if not self._validate_download(save_path, total_size):
                logger.error(f"Download validation failed for {save_path}")
                return False

            # Update statistics
            file_size = save_path.stat().st_size
            self.stats['total_bytes'] += file_size

            elapsed = time.time() - start_time
            if show_progress and file_size > 100 * 1024:
                speed = file_size / elapsed if elapsed > 0 else 0
                logger.info(f"✓ Downloaded {save_path.name} "
                          f"({self._format_bytes(file_size)} in {elapsed:.1f}s, "
                          f"{self._format_bytes(speed)}/s)")

            return True

        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            # Clean up partial download
            if save_path.exists():
                try:
                    save_path.unlink()
                except Exception:
                    pass
            return False

    def _validate_download(self, file_path: Path, expected_size: int = None) -> bool:
        """
        Validate downloaded file

        Args:
            file_path: Path to downloaded file
            expected_size: Expected file size (optional)

        Returns:
            True if file is valid
        """
        # Check file exists
        if not file_path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return False

        # Check file size > 0
        file_size = file_path.stat().st_size
        if file_size == 0:
            logger.warning(f"File is empty (0 bytes): {file_path}")
            return False

        # Check against expected size (allow 1% difference for headers/metadata)
        if expected_size and expected_size > 0:
            size_diff = abs(file_size - expected_size)
            if size_diff > (expected_size * 0.01):
                logger.warning(
                    f"File size mismatch: expected {expected_size}, got {file_size}"
                )
                # Don't fail on size mismatch, just warn
                # Some servers report incorrect content-length

        logger.debug(f"File validation passed: {file_path} ({file_size} bytes)")
        return True

    def _format_bytes(self, bytes_num: int) -> str:
        """Format bytes to human readable string"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_num < 1024.0:
                return f"{bytes_num:.1f}{unit}"
            bytes_num /= 1024.0
        return f"{bytes_num:.1f}TB"

    def _generate_filename(self, url: str, prefix: str = '') -> str:
        """
        Generate filename from URL

        Args:
            url: Media URL
            prefix: Optional prefix for filename

        Returns:
            Sanitized filename
        """
        # Parse URL
        parsed = urlparse(url)
        path = unquote(parsed.path)

        # Get filename from URL
        filename = os.path.basename(path)

        # If no filename, generate from URL hash
        if not filename or filename == '/':
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            ext = get_file_extension(url) or 'jpg'
            filename = f"{prefix}{url_hash}.{ext}"

        # Sanitize filename
        filename = sanitize_filename(filename)

        # Add prefix if provided and not already present
        if prefix and not filename.startswith(prefix):
            filename = f"{prefix}{filename}"

        return filename

    def get_statistics(self) -> Dict[str, Any]:
        """Get download statistics"""
        return {
            **self.stats,
            'total_bytes_formatted': self._format_bytes(self.stats['total_bytes'])
        }


def download_images(
    scraper,
    post_id: str,
    soup: BeautifulSoup = None,
    post_url: str = None,
    save_dir: Path = None
) -> List[str]:
    """
    Download all images from a post

    Args:
        scraper: TuoiTreScraper instance
        post_id: Post ID for organizing downloads
        soup: BeautifulSoup object (if already fetched)
        post_url: URL of the post (required if soup is None)
        save_dir: Custom save directory (defaults to ./images/<postId>/)

    Returns:
        List of paths to downloaded images
    """
    logger.info(f"Downloading images for post {post_id}")

    # Fetch page if soup not provided
    if soup is None:
        if not post_url:
            raise ValueError("Either soup or post_url must be provided")
        soup = scraper.get_html(post_url)

    # Determine save directory (./images/<postId>/)
    if save_dir is None:
        save_dir = config.IMAGES_DIR / post_id
    save_dir.mkdir(parents=True, exist_ok=True)

    # Initialize downloader
    downloader = MediaDownloader(scraper, save_dir)

    # Extract image URLs
    image_urls = _extract_image_urls(soup, post_url)

    if not image_urls:
        logger.info(f"No images found for post {post_id}")
        return []

    logger.info(f"Found {len(image_urls)} images to download")

    # Download each image
    downloaded_paths = []

    for i, img_url in enumerate(image_urls, 1):
        try:
            # Normalize URL
            img_url = normalize_url(img_url, post_url)

            # Generate filename
            filename = downloader._generate_filename(img_url, prefix=f'img_{i}_')
            save_path = save_dir / filename

            # Skip if already exists
            if save_path.exists() and save_path.stat().st_size > 0:
                logger.debug(f"Image already exists: {filename}")
                try:
                    rel_path = save_path.relative_to(config.BASE_DIR)
                    downloaded_paths.append(f"./{rel_path.as_posix()}")
                except Exception:
                    downloaded_paths.append(str(save_path))
                continue

            # Download image
            logger.info(f"[{i}/{len(image_urls)}] Downloading: {filename}")

            success = downloader.download_file(
                img_url,
                save_path,
                show_progress=True
            )

            if success:
                try:
                    rel_path = save_path.relative_to(config.BASE_DIR)
                    downloaded_paths.append(f"./{rel_path.as_posix()}")
                except Exception:
                    downloaded_paths.append(str(save_path))
                downloader.stats['images_downloaded'] += 1
                logger.debug(f"✓ Saved: {save_path}")
            else:
                downloader.stats['images_failed'] += 1
                logger.warning(f"✗ Failed to download: {img_url}")

                if not config.SKIP_ON_ERROR:
                    raise MediaDownloadError(f"Failed to download image", media_url=img_url)

        except Exception as e:
            downloader.stats['images_failed'] += 1
            logger.warning(f"Error downloading image {img_url}: {e}")

            if not config.SKIP_ON_ERROR:
                raise

    # Log summary
    stats = downloader.get_statistics()
    logger.info(f"Image download complete for post {post_id}:")
    logger.info(f"  Downloaded: {stats['images_downloaded']}")
    logger.info(f"  Failed: {stats['images_failed']}")
    logger.info(f"  Total size: {stats['total_bytes_formatted']}")

    return downloaded_paths


def _extract_image_urls(soup: BeautifulSoup, base_url: str = None) -> List[str]:
    """
    Extract all image URLs from post content

    Args:
        soup: BeautifulSoup object
        base_url: Base URL for resolving relative URLs

    Returns:
        List of image URLs
    """
    image_urls = []

    # Find all img tags in content
    content_selectors = [
        ('div', {'class': re.compile(r'detail-content|article-content|content-detail')}),
        ('article', {}),
    ]

    content_element = None
    for tag, attrs in content_selectors:
        content_element = soup.find(tag, attrs)
        if content_element:
            break

    if not content_element:
        # Fallback: search entire page
        content_element = soup

    # Extract image URLs
    for img in content_element.find_all('img'):
        # Try multiple attributes
        img_url = img.get('src') or img.get('data-src') or img.get('data-original')

        if img_url:
            # Normalize URL
            if base_url:
                img_url = normalize_url(img_url, base_url)

            # Filter out tracking pixels, icons, etc.
            if _is_valid_image_url(img_url):
                image_urls.append(img_url)

    # Also check for picture/source elements
    for picture in content_element.find_all('picture'):
        for source in picture.find_all('source'):
            src = source.get('srcset') or source.get('src')
            if src:
                # srcset may contain multiple URLs
                urls = [u.strip().split()[0] for u in src.split(',')]
                for url in urls:
                    if base_url:
                        url = normalize_url(url, base_url)
                    if _is_valid_image_url(url):
                        image_urls.append(url)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in image_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


def _is_valid_image_url(url: str) -> bool:
    """
    Check if URL is a valid image URL

    Args:
        url: URL to check

    Returns:
        True if URL appears to be a valid image
    """
    if not url:
        return False

    # Skip data URLs, tracking pixels, etc.
    if url.startswith('data:'):
        return False

    # Skip very small images (likely icons/pixels)
    # Check URL parameters for dimensions
    size_match = re.search(r'(\d+)x(\d+)', url)
    if size_match:
        width, height = int(size_match.group(1)), int(size_match.group(2))
        if width < 50 or height < 50:
            return False

    # Check file extension
    ext = get_file_extension(url)
    if ext and ext not in config.MEDIA_TYPES.get('images', []):
        return False

    # Skip common tracking/analytics images
    skip_patterns = [
        r'pixel',
        r'tracking',
        r'analytics',
        r'1x1',
        r'blank\.(gif|png)',
        r'spacer\.(gif|png)',
    ]

    for pattern in skip_patterns:
        if re.search(pattern, url, re.I):
            return False

    return True


def download_audio(
    scraper,
    post_id: str,
    soup: BeautifulSoup = None,
    post_url: str = None,
    save_dir: Path = None
) -> Optional[str]:
    """
    Download audio/podcast from a post (if available)

    Args:
        scraper: TuoiTreScraper instance
        post_id: Post ID for organizing downloads
        soup: BeautifulSoup object (if already fetched)
        post_url: URL of the post (required if soup is None)
        save_dir: Custom save directory (defaults to ./audio/)

    Returns:
        Path to downloaded audio file, or None if no audio found
    """
    logger.info(f"Checking for audio/podcast in post {post_id}")

    # Fetch page if soup not provided
    if soup is None:
        if not post_url:
            raise ValueError("Either soup or post_url must be provided")
        soup = scraper.get_html(post_url)

    # Determine save directory (./audio/)
    if save_dir is None:
        save_dir = config.AUDIO_DIR
    save_dir.mkdir(parents=True, exist_ok=True)

    # Initialize downloader
    downloader = MediaDownloader(scraper, save_dir)

    # Extract audio URL
    audio_url = _extract_audio_url(soup, post_url)

    if not audio_url:
        logger.info(f"No audio found for post {post_id}")
        return None

    try:
        # Normalize URL
        audio_url = normalize_url(audio_url, post_url)

        # Get file extension
        ext = get_file_extension(audio_url) or 'mp3'

        # Generate filename: <postId>.<extension>
        filename = f"{post_id}.{ext}"
        save_path = save_dir / filename

        # Skip if already exists
        if save_path.exists() and save_path.stat().st_size > 0:
            logger.info(f"Audio already exists: {filename}")
            try:
                rel_path = save_path.relative_to(config.BASE_DIR)
                return f"./{rel_path.as_posix()}"
            except Exception:
                return str(save_path)

        # Download audio
        logger.info(f"Downloading audio: {filename}")
        logger.info(f"  URL: {audio_url}")

        success = downloader.download_file(
            audio_url,
            save_path,
            show_progress=True
        )

        if success:
            downloader.stats['audio_downloaded'] += 1
            logger.info(f"✓ Audio saved: {save_path}")
            try:
                rel_path = save_path.relative_to(config.BASE_DIR)
                return f"./{rel_path.as_posix()}"
            except Exception:
                return str(save_path)
        else:
            downloader.stats['audio_failed'] += 1
            logger.warning(f"✗ Failed to download audio: {audio_url}")

            if not config.SKIP_ON_ERROR:
                raise MediaDownloadError(f"Failed to download audio", media_url=audio_url)

            return None

    except Exception as e:
        downloader.stats['audio_failed'] += 1
        logger.warning(f"Error downloading audio from {post_url}: {e}")

        if not config.SKIP_ON_ERROR:
            raise

        return None


def _extract_audio_url(soup: BeautifulSoup, base_url: str = None) -> Optional[str]:
    """
    Extract audio/podcast URL from post

    Args:
        soup: BeautifulSoup object
        base_url: Base URL for resolving relative URLs

    Returns:
        Audio URL or None if not found
    """
    # Try multiple methods to find audio

    # Method 1: TuoiTre.vn video.js audio player (vjs-tech class)
    # Example: <audio class="vjs-tech" src="https://tts.mediacdn.vn/...m4a">
    audio_tag = soup.find('audio', class_='vjs-tech')
    if audio_tag:
        audio_url = audio_tag.get('src')
        if audio_url:
            logger.debug(f"Found audio with vjs-tech class: {audio_url}")
            return normalize_url(audio_url, base_url) if base_url else audio_url

    # Method 2: Extract from embedTTS.init script
    # Audio is loaded dynamically via JavaScript, but we can construct the URL
    # from the configuration in the embedTTS.init() call
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and 'embedTTS.init' in script.string:
            try:
                content = script.string

                # Extract parameters from embedTTS.init
                news_id_match = re.search(r"newsId:\s*['\"](\d+)['\"]", content)
                dist_date_match = re.search(r"distributionDate:\s*['\"]([^'\"]+)['\"]", content)
                namespace_match = re.search(r"nameSpace:\s*['\"]([^'\"]+)['\"]", content)
                domain_match = re.search(r"domainStorage:\s*['\"]([^'\"]+)['\"]", content)
                ext_match = re.search(r"ext:\s*['\"]([^'\"]+)['\"]", content)
                voice_match = re.search(r"defaultVoice:\s*([^,\s}]+)", content)

                if news_id_match and dist_date_match and namespace_match:
                    news_id = news_id_match.group(1)
                    dist_date = dist_date_match.group(1).replace('/', '/')  # Keep as yyyy/MM/dd
                    namespace = namespace_match.group(1)
                    domain = domain_match.group(1) if domain_match else 'https://tts.mediacdn.vn'
                    ext = ext_match.group(1) if ext_match else 'm4a'

                    # Get voice (can be 'nu-1', 'nu', or 'nam')
                    voice = 'nu-1'  # Default
                    if voice_match:
                        voice_value = voice_match.group(1).strip()
                        # Remove any trailing comments like //'nu'
                        voice_value = voice_value.split('//')[0].strip().strip('"\'')

                        if voice_value == '_voice':
                            # _voice is a variable - look for its assignment in the script
                            voice_assignment = re.search(r'var\s+_voice\s*=\s*["\']([^"\']+)["\']', content)
                            if voice_assignment:
                                voice = voice_assignment.group(1)
                            else:
                                # Default is nu-1
                                voice = 'nu-1'
                        else:
                            voice = voice_value

                    # Construct URL: {domain}/{date}/{namespace}-{voice}-{newsId}.{ext}
                    audio_url = f"{domain}/{dist_date}/{namespace}-{voice}-{news_id}.{ext}"
                    logger.debug(f"Constructed audio URL from embedTTS script: {audio_url}")
                    return audio_url

            except Exception as e:
                logger.debug(f"Error extracting audio from embedTTS script: {e}")
                continue

    # Method 3: Standard audio tag
    audio_tag = soup.find('audio')
    if audio_tag:
        # Check src attribute
        audio_url = audio_tag.get('src')
        if audio_url:
            logger.debug(f"Found audio tag with src: {audio_url}")
            return normalize_url(audio_url, base_url) if base_url else audio_url

        # Check source tags within audio
        source = audio_tag.find('source')
        if source:
            audio_url = source.get('src')
            if audio_url:
                logger.debug(f"Found audio source tag: {audio_url}")
                return normalize_url(audio_url, base_url) if base_url else audio_url

    # Method 4: Podcast player containers
    podcast_selectors = [
        ('div', {'class': re.compile(r'podcast|audio-player')}),
        ('div', {'id': re.compile(r'podcast|audio')}),
    ]

    for tag, attrs in podcast_selectors:
        container = soup.find(tag, attrs)
        if container:
            # Look for data attributes
            audio_url = container.get('data-src') or container.get('data-url')
            if audio_url:
                return normalize_url(audio_url, base_url) if base_url else audio_url

            # Look for links to audio files
            for link in container.find_all('a', href=True):
                href = link['href']
                ext = get_file_extension(href)
                if ext in config.MEDIA_TYPES.get('audio', []):
                    return normalize_url(href, base_url) if base_url else href

    # Method 5: Links to audio files in content
    content = soup.find('div', class_=re.compile(r'detail-content|article-content'))
    if content:
        for link in content.find_all('a', href=True):
            href = link['href']
            ext = get_file_extension(href)
            if ext in config.MEDIA_TYPES.get('audio', []):
                return normalize_url(href, base_url) if base_url else href

    return None


def download_all_media(
    scraper,
    post_id: str,
    post_url: str,
    soup: BeautifulSoup = None,
    include_images: bool = True,
    include_audio: bool = True
) -> Dict[str, Any]:
    """
    Download all media (images and audio) from a post

    Args:
        scraper: TuoiTreScraper instance
        post_id: Post ID
        post_url: URL of the post
        soup: BeautifulSoup object (optional)
        include_images: Whether to download images
        include_audio: Whether to download audio

    Returns:
        Dictionary with download results
    """
    logger.info(f"Downloading all media for post {post_id}")

    # Fetch page if not provided
    if soup is None:
        soup = scraper.get_html(post_url)

    results = {
        'post_id': post_id,
        'images': [],
        'audio': None,
        'errors': []
    }

    # Download images
    if include_images and config.DOWNLOAD_IMAGES:
        try:
            image_paths = download_images(scraper, post_id, soup, post_url)
            results['images'] = image_paths
            logger.info(f"Downloaded {len(image_paths)} images")
        except Exception as e:
            error_msg = f"Failed to download images: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)

            if not config.SKIP_ON_ERROR:
                raise

    # Download audio
    if include_audio and config.DOWNLOAD_AUDIO:
        try:
            audio_path = download_audio(scraper, post_id, soup, post_url)
            results['audio'] = audio_path
            if audio_path:
                logger.info(f"Downloaded audio: {audio_path}")
            else:
                logger.info("No audio found")
        except Exception as e:
            error_msg = f"Failed to download audio: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)

            if not config.SKIP_ON_ERROR:
                raise

    return results


def get_media_urls(soup: BeautifulSoup, post_url: str = None) -> Dict[str, List[str]]:
    """
    Extract all media URLs without downloading

    Args:
        soup: BeautifulSoup object
        post_url: Post URL for resolving relative URLs

    Returns:
        Dictionary with lists of URLs by media type
    """
    return {
        'images': _extract_image_urls(soup, post_url),
        'audio': [_extract_audio_url(soup, post_url)] if _extract_audio_url(soup, post_url) else []
    }
