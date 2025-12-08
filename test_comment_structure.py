"""
Test to see the actual structure of comment API response
"""
import sys
from pathlib import Path
import requests
import json
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from crawler.scraper import TuoiTreScraper, get_category_post_urls

def test_comment_structure():
    """Check the actual fields in comment API response"""
    scraper = TuoiTreScraper()

    try:
        # Get a sample post URL
        category_url = "https://tuoitre.vn/thoi-su.htm"
        post_urls = get_category_post_urls(scraper, category_url, max_posts=5)

        if not post_urls:
            print("No post URLs found!")
            return

        # Try each post until we find one with comments
        for post_url in post_urls:
            print(f"\nChecking: {post_url}")

            # Extract post ID
            match = re.search(r'-(\d+)\.htm', post_url)
            if not match:
                continue

            post_id = match.group(1)

            # Get comments from API
            api_url = f"https://id.tuoitre.vn/api/getlist-comment.api?objId={post_id}&objType=1&pageindex=1&pagesize=10"

            headers = {
                'User-Agent': 'StudentCrawler/1.0 (Educational Project)',
                'Accept': 'application/json',
                'Referer': post_url
            }

            response = requests.get(api_url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get('Success') and data.get('Data'):
                    comments_json = data.get('Data', '[]')
                    if isinstance(comments_json, str):
                        comments = json.loads(comments_json)
                    else:
                        comments = comments_json

                    if comments:
                        print(f"\n✓ Found {len(comments)} comments!")
                        print("\n" + "=" * 60)
                        print("First comment structure:")
                        print("=" * 60)
                        print(json.dumps(comments[0], indent=2, ensure_ascii=False))

                        print("\n" + "=" * 60)
                        print("All field names in first comment:")
                        print("=" * 60)
                        for key in comments[0].keys():
                            value = comments[0][key]
                            value_preview = str(value)[:100] if value else "null"
                            print(f"  {key}: {value_preview}")

                        # Check if there are any with parent_id != "0"
                        print("\n" + "=" * 60)
                        print("Checking for nested replies...")
                        print("=" * 60)
                        for i, comment in enumerate(comments):
                            parent_id = comment.get('parent_id', '0')
                            if parent_id != '0' and parent_id is not None:
                                print(f"\nFound reply at index {i}:")
                                print(json.dumps(comment, indent=2, ensure_ascii=False))
                                break

                        return

        print("\n⚠ No posts with comments found in the sample!")

    finally:
        scraper.close()

if __name__ == '__main__':
    test_comment_structure()
