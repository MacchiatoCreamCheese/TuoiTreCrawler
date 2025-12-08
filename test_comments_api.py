"""
Test to find TuoiTre.vn comment API endpoint
"""
import sys
from pathlib import Path
import requests
import json
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from crawler.scraper import TuoiTreScraper, get_category_post_urls

def test_find_comment_api():
    """Try to find the comment API endpoint"""
    scraper = TuoiTreScraper()

    try:
        # Get a sample post URL
        print("Getting sample post URL...")
        category_url = "https://tuoitre.vn/thoi-su.htm"
        post_urls = get_category_post_urls(scraper, category_url, max_posts=1)

        if not post_urls:
            print("No post URLs found!")
            return

        post_url = post_urls[0]
        print(f"Test post: {post_url}\n")

        # Extract post ID from URL
        # Format: https://tuoitre.vn/article-title-20251208123456789.htm
        match = re.search(r'-(\d+)\.htm', post_url)
        if match:
            post_id = match.group(1)
            print(f"Post ID: {post_id}\n")
        else:
            print("Could not extract post ID!")
            return

        # Get the HTML to look for comment-related code
        soup = scraper.get_html(post_url)

        # Look for comment-related scripts
        print("Looking for comment API endpoints in page source...\n")

        scripts = soup.find_all('script')
        comment_apis = []

        for script in scripts:
            if script.string:
                # Look for API URLs
                api_matches = re.findall(r'https?://[^\s"\'<>]+comment[^\s"\'<>]*', script.string)
                comment_apis.extend(api_matches)

                # Look for comment-related variables
                if 'comment' in script.string.lower():
                    lines = script.string.split('\n')
                    for line in lines[:5]:  # First few lines
                        if 'comment' in line.lower() or 'api' in line.lower():
                            print(f"Found: {line.strip()[:100]}")

        if comment_apis:
            print("\n" + "=" * 60)
            print("Found potential comment API endpoints:")
            print("=" * 60)
            for api in set(comment_apis):
                print(f"  - {api}")

        # Try common comment API patterns
        print("\n" + "=" * 60)
        print("Testing common API patterns...")
        print("=" * 60)

        api_patterns = [
            f"https://id.tuoitre.vn/api/getlist-comment.api?objId={post_id}&objType=1&pageindex=1&pagesize=20",
            f"https://comment.tuoitre.vn/api/comment/list?objectId={post_id}",
            f"https://api.tuoitre.vn/comment?post_id={post_id}",
            f"https://id.tuoitre.vn/api/comment/getlist?objectId={post_id}",
        ]

        for api_url in api_patterns:
            print(f"\nTrying: {api_url}")
            try:
                headers = {
                    'User-Agent': 'StudentCrawler/1.0 (Educational Project)',
                    'Accept': 'application/json',
                    'Referer': post_url
                }
                response = requests.get(api_url, headers=headers, timeout=10)
                print(f"  Status: {response.status_code}")

                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"  ✓ Got JSON response!")
                        print(f"  Keys: {list(data.keys())}")

                        # Pretty print first part of response
                        print(f"  Response preview:")
                        print(json.dumps(data, indent=2, ensure_ascii=False)[:500])

                    except:
                        print(f"  Response (text): {response.text[:200]}")

            except Exception as e:
                print(f"  ✗ Error: {e}")

    finally:
        scraper.close()

if __name__ == '__main__':
    test_find_comment_api()
