"""
Quick test to debug URL extraction from tuoitre.vn
"""
import sys
import re
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from crawler.scraper import TuoiTreScraper
from crawler.utils.helpers import normalize_url
import config

def test_url_extraction():
    """Test URL extraction from category page"""
    scraper = TuoiTreScraper()

    try:
        category_url = "https://tuoitre.vn/thoi-su.htm"
        print(f"Fetching: {category_url}\n")

        soup = scraper.get_html(category_url)

        # Method 1: Find box-category-item
        print("=" * 60)
        print("Method 1: Finding box-category-item containers")
        print("=" * 60)
        articles = soup.find_all('div', class_=re.compile(r'box-category-item'))
        print(f"Found {len(articles)} article containers\n")

        urls_found = []
        for i, article in enumerate(articles[:10], 1):  # Check first 10
            link = article.find('a', href=True)
            if link:
                href = link.get('href')
                print(f"{i}. Raw href: {href}")

                # Normalize URL
                full_url = normalize_url(href, category_url)
                print(f"   Full URL: {full_url}")

                # Check validation
                is_allowed = config.is_url_allowed(full_url)
                print(f"   is_url_allowed: {is_allowed}")

                # Check tuoitre.vn
                has_tuoitre = 'tuoitre.vn' in full_url
                print(f"   Has tuoitre.vn: {has_tuoitre}")

                # Check article ID pattern
                has_id = bool(re.search(r'-\d{6,}\.htm', full_url))
                print(f"   Has article ID: {has_id}")

                # Check exclude patterns
                exclude_patterns = [
                    r'/tag/',
                    r'/video/',
                    r'/podcast/',
                    r'-p\d+\.htm$',
                    r'\.htm$'
                ]

                for pattern in exclude_patterns:
                    if re.search(pattern, full_url):
                        print(f"   Matches exclude pattern: {pattern}")
                        if not re.search(r'-\d{6,}\.htm', full_url):
                            print(f"      -> EXCLUDED (no article ID)")
                        else:
                            print(f"      -> ALLOWED (has article ID)")

                # Final verdict
                if is_allowed and has_tuoitre and has_id:
                    print(f"   ✓ VALID ARTICLE URL")
                    urls_found.append(full_url)
                else:
                    print(f"   ✗ INVALID")

                print()

        print("=" * 60)
        print(f"Total valid URLs found: {len(urls_found)}")
        print("=" * 60)

        if urls_found:
            print("\nValid URLs:")
            for url in urls_found[:5]:
                print(f"  - {url}")
        else:
            print("\n⚠ NO VALID URLS FOUND!")
            print("\nDEBUGGING INFO:")
            print("- Check if normalize_url is working correctly")
            print("- Check if article ID pattern is matching")
            print("- Check if exclude patterns are too strict")

    finally:
        scraper.close()

if __name__ == '__main__':
    test_url_extraction()
